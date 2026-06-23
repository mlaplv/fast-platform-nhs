#!/usr/bin/env bash
# ==============================================================================
# SCRIPT: vps_health_check.sh (BẢN HOÀN CHỈNH - AUTO UPDATE SIGNATURE & VERSION)
# MỤC ĐÍCH: Kiểm tra tài nguyên VPS, Leak DB, Log rác & Tự động update DB virus và quét
# CHÚ Ý: Bắt buộc chạy bằng quyền sudo: sudo ./scripts/vps_health_check.sh
# ==============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' 
BOLD='\033[1m'

# 0. KIỂM TRA QUYỀN ROOT/SUDO NGAY TỪ ĐẦU
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}${BOLD}[❌ LỖI] Vui lòng chạy script bằng quyền sudo:${NC}"
    echo -e "${YELLOW}sudo ./scripts/vps_health_check.sh${NC}"
    exit 1
fi

clear
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${PURPLE}${BOLD}         BÁO CÁO TOÀN DIỆN: SỨC KHỎE HỆ THỐNG & BẢO MẬT VPS            ${NC}"
echo -e "${BLUE}${BOLD}======================================================================${NC}"
echo -e "${YELLOW}Thời gian kiểm tra:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "${YELLOW}Thời gian uptime  :${NC} $(uptime -p)"
echo -e "${BLUE}----------------------------------------------------------------------${NC}"

# 1. TÀI NGUYÊN CPU & RAM
echo -e "${BOLD}1. TÀI NGUYÊN CPU & RAM${NC}"
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | sed 's/ //g')
echo -e "  * Tải hệ thống (1m, 5m, 15m): ${YELLOW}${LOAD_AVG}${NC}"
free -m | awk -v r="$RED" -v g="$GREEN" -v y="$YELLOW" -v nc="$NC" '
    NR==2 {
        total=$2; used=$3; avail=$7;
        printf "  * RAM Khả dụng: %s%d MB%s / %d MB (Đã dùng: %.1f%%)\n", (avail<300?r:(avail<600?y:g)), avail, nc, total, (used*100/total);
    }
'
echo ""

# 2. KIỂM TRA TIẾN TRÌNH BỊ KẸT / TREO
echo -e "${BOLD}2. TIẾN TRÌNH BỊ KẸT (ZOMBIE / UNINTERRUPTIBLE SLEEP)${NC}"
ZOMBIES=$(ps aux | awk '{if ($8 ~ /^[ZD]/) print $0}')
if [ -z "$ZOMBIES" ]; then
    echo -e "  ${GREEN}[✓] Không phát hiện tiến trình độc lập nào bị kẹt.${NC}"
else
    echo -e "  ${RED}[⚠️ PHÁT HIỆN] Các tiến trình sau đang bị treo cứng (Trạng thái Z/D):${NC}"
    echo "$ZOMBIES" | sed 's/^/  /'
fi
echo ""

# 3. PHÁT HIỆN LEAK DB & CONNECTIONS
echo -e "${BOLD}3. ĐÁNH GIÁ RÒ RỈ DATABASE (LEAK DB POOL)${NC}"
PG_CONN=$(ss -tanp 2>/dev/null | grep -E ':5432 ' | wc -l)
MY_CONN=$(ss -tanp 2>/dev/null | grep -E ':3306|:33060 ' | wc -l)
echo -e "  * Session mạng đến PostgreSQL (5432) : ${YELLOW}${PG_CONN}${NC} connections"
echo -e "  * Session mạng đến MySQL/MariaDB (3306): ${YELLOW}${MY_CONN}${NC} connections"
if [ "$PG_CONN" -gt 60 ] || [ "$MY_CONN" -gt 60 ]; then
    echo -e "  ${RED}[⚠️ CẢNH BÁO LEAK] Số kết nối mạng tăng cao liên tục. Kiểm tra lại pool_size trong mã nguồn.${NC}"
else
    echo -e "  ${GREEN}[✓] Số lượng kết nối DB ổn định.${NC}"
fi
echo ""

# 4. QUÉT LOG RÁC & CÁC FILE LOG PHÌNH TO
echo -e "${BOLD}4. QUÉT LOG RÁC & CÁC FILE PHÌNH TO TRONG HỆ THỐNG${NC}"
LARGE_LOGS=$(find /var/log /home /root -type f -name "*.log" -size +50M 2>/dev/null)
if [ -z "$LARGE_LOGS" ]; then
    echo -e "  ${GREEN}[✓] Không có file log đơn lẻ nào vượt quá 50MB.${NC}"
else
    echo -e "  ${RED}[⚠️ PHÁT HIỆN] Các file log rác đang chiếm dụng nhiều bộ nhớ:${NC}"
    echo "$LARGE_LOGS" | while read -r file; do
        size=$(du -sh "$file" | awk '{print $1}')
        echo -e "    - ${YELLOW}[$size]${NC} $file"
    done
fi
echo ""

# 5. KIỂM TRA BẢO MẬT & TỰ ĐỘNG CẬP NHẬT (SECURITY AUTO-UPDATE & SCAN)
echo -e "${BOLD}5. KIỂM TRA AN NINH & QUÉT MÃ ĐỘC (LIVE UPDATE ACTIVE)${NC}"

# A. Kiểm tra Brute-Force SSH (Nhận biết cấu hình PasswordAuthentication)
if [ -f /var/log/auth.log ]; then
    FAILED_SSH=$(grep "Failed password" /var/log/auth.log 2>/dev/null | wc -l)
    SSH_PASS_AUTH=$(grep -E "^PasswordAuthentication" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null | grep -i "no" | wc -l)
    
    if [ "$SSH_PASS_AUTH" -gt 0 ]; then
        if [ "$FAILED_SSH" -gt 20 ]; then
            echo -e "  ${GREEN}[✓] Phát hiện ${FAILED_SSH} lượt dò mật khẩu rác, nhưng VPS AN TOÀN vì bạn đã khóa Login Password (Chỉ dùng SSH Key).${NC}"
        else
            echo -e "  ${GREEN}[✓] Không có dấu hiệu bất thường về đăng nhập.${NC}"
        fi
    else
        if [ "$FAILED_SSH" -gt 20 ]; then
            echo -e "  ${RED}[🚨 CẢNH BÁO BẢO MẬT] Phát hiện ${FAILED_SSH} lần đăng nhập SSH thất bại. Hệ thống chưa khóa Password, nguy cơ dính Brute-force cao!${NC}"
        else
            echo -e "  ${GREEN}[✓] Số lần đăng nhập lỗi an toàn ($FAILED_SSH lần).${NC}"
        fi
    fi
else
    echo -e "  * Kiểm tra Brute-force: ${BLUE}[BỎ QUA - KHÔNG TÌM THẤY AUTH LOG]${NC}"
fi

# B. Kiểm tra & Cập nhật & Quét Rkhunter
if ! command -v rkhunter &> /dev/null; then
    echo -e "  * ${YELLOW}[!] Chưa cài rkhunter. Đang tự động cài đặt ngầm...${NC}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq && apt-get install -y -qq rkhunter &>/dev/null
    rkhunter --propupd --quiet &>/dev/null
else
    echo -e "  * ${GREEN}[✓] Rkhunter đã cài đặt.${NC} Đang cập nhật dữ liệu và kiểm tra phiên bản mới..."
    # Cập nhật cơ sở dữ liệu lỗi/mã độc của rkhunter
    rkhunter --update --quiet &>/dev/null
    # Cập nhật snapshot thuộc tính file hệ thống hiện tại để tránh báo động giả
    rkhunter --propupd --quiet &>/dev/null
fi

echo -e "    -> Đang quét Rootkit & Backdoor bằng dữ liệu mới nhất..."
RKH_RESULT=$(rkhunter --check --sk --nocolor --quiet 2>&1 | grep -E "Warning|🔥")
if [ -z "$RKH_RESULT" ]; then
    echo -e "    ${GREEN}[✓] Hệ thống sạch, không phát hiện dấu vết Rootkit/Backdoor.${NC}"
else
    echo -e "    ${RED}[⚠️ CẢNH BÁO ROOTKIT] Phát hiện bất thường hệ thống:${NC}"
    echo "$RKH_RESULT" | sed 's/^/      /'
fi

# C. Kiểm tra & Cập nhật & Quét ClamAV
if ! command -v clamscan &> /dev/null; then
    echo -e "  * ${YELLOW}[!] Chưa cài ClamAV. Đang tự động cài đặt ngầm...${NC}"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq && apt-get install -y -qq clamav clamav-daemon &>/dev/null
    systemctl stop clamav-freshclam &>/dev/null
    freshclam --quiet &>/dev/null
    systemctl start clamav-freshclam &>/dev/null
else
    echo -e "  * ${GREEN}[✓] ClamAV đã cài đặt.${NC} Đang cập nhật Database mẫu virus mới nhất (Freshclam)..."
    # Dừng service tạm thời để chạy lệnh update thủ công không bị lock db
    systemctl stop clamav-freshclam &>/dev/null
    freshclam --quiet &>/dev/null
    systemctl start clamav-freshclam &>/dev/null
fi

echo -e "    -> Đang quét Trojan/Virus tại vùng rủi ro cao (/tmp, /dev/shm, /root)..."
VIRUS_SCAN=$(clamscan -r /tmp /dev/shm /root --infected --quiet 2>/dev/null)
if [ -z "$VIRUS_SCAN" ]; then
    echo -e "    ${GREEN}[✓] Không tìm thấy dấu hiệu Trojan hoặc Virus thực thi ngầm.${NC}"
else
    echo -e "    ${RED}[🚨 BÁO ĐỘNG ĐỎ] PHÁT HIỆN PHẦN MỀM ĐỘC HẠI TRÊN VPS:${NC}"
    echo "$VIRUS_SCAN" | sed 's/^/      /'
fi

echo -e "${BLUE}${BOLD}======================================================================${NC}"
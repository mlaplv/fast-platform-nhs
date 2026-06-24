#!/bin/bash
# ==============================================================================
# Script dọn dẹp log và các tệp tin lưu trữ cũ trên VPS (Tránh phình đĩa & giảm hiệu năng)
# ==============================================================================

# Thư mục chính
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "${SCRIPT_DIR}")"
BACKUPS_DIR="${BASE_DIR}/backups"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] BẮT ĐẦU DỌN DẸP HỆ THỐNG ==="

# 1. Truncate Docker logs qua helper container (không cần sudo)
# [FIX V2.3] Không dùng truncate trực tiếp lên log file của container đang chạy vì sẽ làm lệch file offset của Docker daemon,
# dẫn đến lệnh 'docker logs' / 'docker compose logs' bị treo cứng (hang) và sau đó bị kill.
# Hệ thống đã cấu hình max-size="10m" và max-file="3" trong docker-compose.yml nên Docker sẽ tự động xoay vòng log an toàn.
echo "-> [1/4] Đang làm sạch Docker Container logs..."
echo "   ✔ Bỏ qua (Docker đã tự động xoay vòng log qua cấu hình max-size trong docker-compose.yml)."

# 2. Xóa các file .log trên Host
echo "-> [2/4] Đang làm sạch các tệp tin .log trên Host..."
find "${BASE_DIR}" -type f -name "*.log" -delete 2>/dev/null
echo "   ✔ Đã dọn dẹp các tệp *.log trên thư mục dự án."

# 3. Giới hạn số lượng bản sao lưu (Backup) - Chỉ giữ lại 5 bản gần nhất
echo "-> [3/4] Đang kiểm tra và giới hạn số lượng bản sao lưu..."
if [ -d "${BACKUPS_DIR}" ]; then
    cd "${BACKUPS_DIR}" || exit
    # Liệt kê các tệp tin bắt đầu bằng XOHI_BKP_ và kết thúc bằng .tar.gz.enc, sắp xếp theo ngày sửa đổi từ mới đến cũ
    # Giữ lại 5 bản mới nhất, xóa các bản cũ hơn từ dòng thứ 6 trở đi
    ls -t XOHI_BKP_*.tar.gz.enc 2>/dev/null | tail -n +6 | while read -r old_backup; do
        echo "   - Xóa bản sao lưu cũ: ${old_backup}"
        rm -f "${old_backup}" "${old_backup}.sha256" 2>/dev/null
    done
    echo "   ✔ Hoàn thành kiểm tra và tối ưu thư mục backups."
fi

# 4. Prune các tài nguyên Docker không dùng đến (dangling)
echo "-> [4/4] Đang dọn dẹp các tài nguyên Docker không sử dụng (dangling)..."
docker system prune -f 2>/dev/null
docker volume prune -f 2>/dev/null
docker builder prune -a -f 2>/dev/null
echo "   ✔ Hoàn thành dọn dẹp Docker cache!"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] DỌN DẸP HOÀN TẤT ==="

#!/usr/bin/env bash

# SSL Setup Helper for Fast Platform
# This script extracts the Caddy Root CA and helps trust it on the local system.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT=$(pwd)
CONTAINER_NAME="fast_platform_caddy"
CERT_DIR="$PROJECT_ROOT/certs"
CERT_PATH="$CERT_DIR/caddy-root-ca.crt"

echo -e "${CYAN}[SSL] Đang kiểm tra container Caddy...${NC}"

if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}[ERROR] Container $CONTAINER_NAME không chạy. Hãy chạy './xohi.sh' rồi chọn Hot Restart trước.${NC}"
    exit 1
fi

echo -e "${CYAN}[SSL] Đang trích xuất Caddy Root CA...${NC}"
mkdir -p "$CERT_DIR"
docker exec "$CONTAINER_NAME" cat /data/caddy/pki/authorities/local/root.crt > "$CERT_PATH"
chmod 644 "$CERT_PATH"

if [ ! -s "$CERT_PATH" ]; then
    echo -e "${RED}[ERROR] Không thể trích xuất chứng chỉ hoặc chứng chỉ trống.${NC}"
    exit 1
fi

echo -e "${GREEN}[OK] Đã lưu chứng chỉ vào: $CERT_PATH${NC}"
echo -e ""

# Tự động hóa phần Linux System Trust
echo -e "${YELLOW}Bước 1: Đang tự động thiết lập tin cậy trên hệ thống Linux...${NC}"
sudo cp "$CERT_PATH" /usr/local/share/ca-certificates/caddy-root-ca.crt
sudo update-ca-certificates
echo -e "${GREEN}[OK] Hệ thống đã tin tưởng chứng chỉ.${NC}"
echo -e ""

echo -e "${YELLOW}Bước 2: THIẾT LẬP TRÌNH DUYỆT (BẮT BUỘC)${NC}"
echo -e "${CYAN}Tại sao?${NC} Trình duyệt có kho bảo mật riêng. Tại màn hình anh đang mở: Mở Chrome và truy cập: chrome://settings/security -> Chọn Manage certificates (Quản lý chứng chỉ)."
echo -e ""
echo -e "1. Nhấn nút ${CYAN}'Import'${NC} nằm bên phải dòng ${GREEN}'Trusted Certificates'${NC} (Chứng chỉ tin cậy)."
echo -e "2. Chọn file: ${YELLOW}$CERT_PATH${NC}"
echo -e "3. Sau khi Import xong, anh sẽ thấy 'Caddy Local Authority' xuất hiện trong danh sách."
echo -e ""
echo -e "${YELLOW}Bước 3: Khởi động lại trình duyệt hoàn toàn và tải lại trang.${NC}"
echo -e ""
echo -e "${GREEN}== THIẾT LẬP HOÀN TẤT ==${NC}"
echo -e ""
echo -e "${GREEN}== THIẾT LẬP HOÀN TẤT ==${NC}"

#!/bin/bash
# ==============================================================================
# Script dọn dẹp log và các tệp tin lưu trữ cũ trên VPS (Tránh phình đĩa & giảm hiệu năng)
# ==============================================================================

# Thư mục chính
BASE_DIR="/opt/fast-platform"
BACKUPS_DIR="${BASE_DIR}/backups"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] BẮT ĐẦU DỌN DẸP HỆ THỐNG ==="

# 1. Truncate Docker logs qua helper container (không cần sudo)
echo "-> [1/4] Đang làm sạch Docker Container logs..."
if docker run --rm -v /var/lib/docker/containers:/var/lib/docker/containers alpine sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log' 2>/dev/null; then
    echo "   ✔ Đã làm sạch toàn bộ tệp tin logs Docker thành công!"
else
    echo "   ✘ Lỗi hoặc không thể dọn dẹp logs Docker."
fi

# 2. Xóa các file .log trên Host
echo "-> [2/4] Đang làm sạch các tệp tin .log trên Host..."
find "${BASE_DIR}" -type f -name "*.log" -delete 2>/dev/null
echo "   ✔ Đã dọn dẹp các tệp *.log trên thư mục dự án."

# 3. Giới hạn số lượng bản sao lưu (Backup) - Chỉ giữ lại 5 bản gần nhất
echo "-> [3/4] Đang kiểm tra và giới hạn số lượng bản sao lưu..."
if [ -d "${BACKUPS_DIR}" ]; then
    cd "${BACKUPS_DIR}" || exit
    # Liệt kê các tệp tin/thư mục bắt đầu bằng XOHI_BKP_, sắp xếp theo ngày sửa đổi từ mới đến cũ
    # Giữ lại 5 bản mới nhất (5 dòng đầu), xóa các bản cũ hơn từ dòng thứ 6 trở đi
    ls -dt XOHI_BKP_* 2>/dev/null | tail -n +6 | while read -r old_backup; do
        echo "   - Xóa bản sao lưu cũ: ${old_backup}"
        rm -rf "${old_backup}" "${old_backup}.sha256" 2>/dev/null
    done
    echo "   ✔ Hoàn thành kiểm tra và tối ưu thư mục backups."
fi

# 4. Prune các tài nguyên Docker không dùng đến (dangling)
echo "-> [4/4] Đang dọn dẹp các tài nguyên Docker không sử dụng (dangling)..."
docker system prune -f 2>/dev/null
echo "   ✔ Hoàn thành dọn dẹp Docker cache!"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] DỌN DẸP HOÀN TẤT ==="

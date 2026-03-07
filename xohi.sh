#!/usr/bin/env bash

# XOHI OS - PROJECT MANAGEMENT COMMANDER v2.1
# Fixed: Aggressive cleanup with sudo & robust find

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 0: Xác định Docker Command
if command -v docker-compose &> /dev/null; then DOCKER_CMD="docker-compose"; else DOCKER_CMD="docker compose"; fi

# Helper: Deep Clean function
function deep_clean() {
    echo -e "${CYAN}[CLEAN] Đang dùng SUDO để quét sạch rác (bao gồm file do Docker tạo)...${NC}"
    
    # Sử dụng find + sudo để xóa triệt để node_modules và các thư mục rác
    # -prune giúp find không đi sâu vào các thư mục đã được liệt kê để xóa
    find . -type d \( -name "node_modules" -o -name "dist" -o -name "build" -o -name ".svelte-kit" -o -name ".next" -o -name ".vite" -o -name "__pycache__" -o -name ".pnpm-store" -o -name ".pytest_cache" \) -prune -exec sudo rm -rf {} + 2>/dev/null || true
    
    # Xóa các file lock, log và file rác hệ thống (macOS .DS_Store)
    find . -maxdepth 3 -type f \( -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "*.log" -o -name ".coverage" -o -name ".DS_Store" \) -delete 2>/dev/null || true
    
    echo -e "${GREEN}[OK] Đã dọn dẹp môi trường sạch bóng.${NC}"
}

function clean_docker_completely() {
    echo -e "${YELLOW}Bắt đầu làm sạch Docker HOÀN TOÀN...${NC}"
    echo "---------------------------"
    echo -e "${RED}CẢNH BÁO: Hành động này sẽ xóa SẠCH Docker như lúc mới cài đặt!${NC}"
    echo -e "${RED}Tất cả container, image, volume, network sẽ bị xóa vĩnh viễn!${NC}"
    echo "---------------------------"

    read -p "$(echo -e "${RED}Bạn có CHẮC CHẮN muốn xóa sạch Docker hoàn toàn không? (gõ 'yyes' để xác nhận): ${NC}")" confirm
    if [[ "$confirm" != "yyes" ]]; then
        echo -e "${YELLOW}Đã hủy thao tác. Docker không bị thay đổi.${NC}"
        return 1
    fi

    echo -e "${CYAN}Đang thực hiện dọn dẹp Docker hoàn toàn...${NC}"

    echo -e "${CYAN}1. Dừng tất cả container...${NC}"
    docker stop $(docker ps -aq) 2>/dev/null || true

    echo -e "${CYAN}2. Xóa tất cả container...${NC}"
    docker rm $(docker ps -aq) 2>/dev/null || true

    echo -e "${CYAN}3. Xóa tất cả image...${NC}"
    docker rmi -f $(docker images -aq) 2>/dev/null || true

    echo -e "${CYAN}4. Xóa tất cả volume...${NC}"
    docker volume rm $(docker volume ls -q) 2>/dev/null || true

    echo -e "${CYAN}5. Xóa tất cả network...${NC}"
    docker network rm $(docker network ls -q --filter "type=custom") 2>/dev/null || true

    echo -e "${CYAN}6. Xóa build cache...${NC}"
    docker builder prune -af 2>/dev/null || true

    echo -e "${CYAN}7. Dọn dẹp hệ thống hoàn toàn...${NC}"
    docker system prune -af --volumes 2>/dev/null || true

    echo -e "${CYAN}8. Xóa Docker Compose volumes và networks...${NC}"
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true

    echo "---------------------------"
    echo -e "${GREEN}✅ Docker đã được xóa sạch hoàn toàn!${NC}"
    echo -e "${GREEN}✅ Docker hiện tại như lúc mới cài đặt!${NC}"
    echo "---------------------------"
}

while true; do
    clear
    echo -e "${CYAN}"
    echo "------------------------------------------------"
    echo "   XOHI OS - PROJECT MANAGEMENT COMMANDER       "
    echo "   (New & Fixed Edition)                        "
    echo "------------------------------------------------"
    echo -e "${NC}"

    echo "Vui lòng chọn tính năng:"
    echo "1) Khởi tạo sâu (Hard Reset & Deep Clean & Seed)"
    echo "2) Làm sạch & Cập nhật gói (Clean Update)"
    echo "3) Khởi động lại (Hot Restart)"
    echo "4) SAO LƯU DỮ LIỆU & MEDIA (Backup Data)"
    echo "5) SIÊU DỌN DẸP ĐỂ SAO LƯU (Nuke & Backup - Cực nhẹ)"
    echo "6) CÀI ĐẶT & TRIỂN KHAI (Production Deploy)"
    echo "7) THIẾT LẬP SSL (Trust SSL Certificate)"
    echo "8) XÓA SẠCH DOCKER HOÀN TOÀN (Như lúc mới cài đặt)"
    echo "0) Thoát (Exit)"
    echo ""
    read -p "Lựa chọn của anh [0-8]: " choice

    case $choice in
        1)
            echo -e "${YELLOW}[INFO] Đang KHỞI TẠO TOÀN DIỆN...${NC}"
            $DOCKER_CMD down -v || true
            deep_clean
            $DOCKER_CMD build --no-cache
            # Start DB + Redis first, wait for healthcheck
            $DOCKER_CMD up -d db redis
            echo -e "${YELLOW}[WAIT] Đang chờ DB + Redis healthy...${NC}"
            until $DOCKER_CMD exec db pg_isready -U postgres >/dev/null 2>&1; do
              sleep 1
            done
            echo -e "${GREEN}[OK] DB đã sẵn sàng.${NC}"
            # Start API (depends_on: service_healthy ensures DB is ready)
            $DOCKER_CMD up -d api
            sleep 3
            # Run migrations and seed using exec (existing container)
            $DOCKER_CMD exec api sh -c "cd apps/api-gateway && alembic upgrade head && python src/scripts/seed.py"
            # Start remaining services
            $DOCKER_CMD up -d
            if command -v pnpm &> /dev/null; then pnpm install --no-frozen-lockfile &>/dev/null || true; fi
            echo -e "${GREEN}== KHỞI TẠO HOÀN TẤT ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        2)
            echo -e "${YELLOW}[INFO] Đang cập nhật...${NC}"
            deep_clean
            if command -v pnpm &> /dev/null; then pnpm install --no-frozen-lockfile; fi
            $DOCKER_CMD exec api sh -c "pip install --root-user-action=ignore --disable-pip-version-check --upgrade ./packages/shared ./packages/ai-engine ./apps/api-gateway && cd apps/api-gateway && alembic upgrade head" || true
            echo -e "${GREEN}== CẬP NHẬT HOÀN TẤT ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        3)
            $DOCKER_CMD restart
            echo -e "${GREEN}== RESTART HOÀN TẤT ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        4)
            echo -e "${YELLOW}[INFO] Đang sao lưu...${NC}"
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            BACKUP_DIR="backups/backup_$TIMESTAMP"
            mkdir -p "$BACKUP_DIR"
            if $DOCKER_CMD ps --status running | grep -q "db"; then
                $DOCKER_CMD exec -t db pg_dump -U postgres fast_platform > "$BACKUP_DIR/db_dump.sql"
            fi
            if [ -d "apps/api-gateway/uploads" ]; then cp -r "apps/api-gateway/uploads" "$BACKUP_DIR/uploads"; fi
             # 3. Bundling everything
            echo -e "${YELLOW}[INFO] Đang đóng gói bản sao lưu...${NC}"
            # COPYFILE_DISABLE=1 ngăn macOS tạo ra các file ._ rác trong archive
            COPYFILE_DISABLE=1 tar -czf "backups/backup_$TIMESTAMP.tar.gz" -C backups "backup_$TIMESTAMP"
            rm -rf "$BACKUP_DIR"
            echo -e "${GREEN}== SAO LƯU THÀNH CÔNG: backups/backup_$TIMESTAMP.tar.gz ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        5)
            echo -e "${RED}[WARNING] XÓA SẠCH DỮ LIỆU & THƯ VIỆN?${NC}"
            read -p "Xác nhận xóa sạch? (y/n): " confirm
            if [[ "$confirm" == "y" ]]; then
                $DOCKER_CMD down -v || true
                deep_clean
                echo -e "${GREEN}== ĐÃ DỌN DẸP SẠCH BÓNG ==${NC}"
            fi
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        6)
            echo -e "${GREEN}[DEPLOY] Đang khởi động tiến trình PRODUCTION...${NC}"
            ./deploy.sh
            echo -e "${GREEN}== TRIỂN KHAI HOÀN TẤT ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        7)
            echo -e "${YELLOW}[INFO] Đang khởi chạy thiết lập SSL...${NC}"
            bash scripts/setup-ssl.sh
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        8)
            clean_docker_completely
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        0)
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR] Sai lựa chọn.${NC}"
            sleep 1
            ;;
    esac
done

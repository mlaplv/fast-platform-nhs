#!/usr/bin/env bash

# XOHI OS - PROJECT MANAGEMENT COMMANDER v3.0 (Lean Monorepo)
# Optimized for UV (Backend) & Vite/NPM (Frontend)
# No PNPM, No Turbo.

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper: Deep Clean function
function deep_clean() {
    echo -e "${CYAN}[CLEAN] Đang dọn dẹp rác hệ thống...${NC}"
    
    echo -e "${YELLOW}-> Đang xóa Frontend rác (node_modules, build caches)...${NC}"
    rm -rf frontend/node_modules frontend/dist frontend/.svelte-kit frontend/.vite
    
    echo -e "${YELLOW}-> Đang xóa Backend rác (.venv, pytest caches)...${NC}"
    rm -rf .venv .pytest_cache backend/.pytest_cache
    
    echo -e "${YELLOW}-> Đang xóa Python caches (__pycache__)...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    echo -e "${YELLOW}-> Đang xóa Lock files & Logs (.DS_Store)...${NC}"
    find . -maxdepth 3 -type f \( -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "*.log" -o -name ".DS_Store" \) -delete 2>/dev/null || true
    
    echo -e "${GREEN}[OK] Đã dọn dẹp môi trường sạch bóng!${NC}"
}

# Helper: Dependency Check
function check_deps() {
    # Auto-fix PATH for UV on Mac
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}[ERROR] Không tìm thấy 'uv'. Đang tự động cài đặt...${NC}"
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source $HOME/.local/bin/env
    fi
}

function bootstrap_all() {
    check_deps
    echo -e "${YELLOW}=== [GOD MODE] KHỞI ĐỘNG TỔNG LỰC (DOCKER) ===${NC}"
    deep_clean
    echo -e "${CYAN}[1/2] Đang xây dựng và khởi động Containers...${NC}"
    docker compose up -d --build
    echo -e "${CYAN}[2/2] Đang thiết lập SSL Trust...${NC}"
    sleep 10
    chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    echo -e "${GREEN}== HỆ THỐNG DOCKER SẴN SÀNG! ==${NC}"
    read -p "Nhấn Enter để tiếp tục..."
}

function start_dev() {
    echo -e "${CYAN}[DEV] Đang khởi động chế độ phát triển DOCKER (V61.1)...${NC}"
    docker compose up -d
    echo -e "${YELLOW}[INFO] Đang đồng bộ SSL...${NC}"
    chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    echo -e "${GREEN}[LIVE] Toàn bộ hệ thống đang chạy trong Docker!${NC}"
    echo -e "${CYAN}API: https://api.smartshop.test${NC}"
    echo -e "${CYAN}UI:  https://smartshop.test${NC}"
    echo -e "${CYAN}ADMIN: https://admin.smartshop.test${NC}"
    echo ""
    echo "Dùng 'docker compose logs -f' để xem log."
    read -p "Nhấn Enter để quay lại menu..."
}

function init_deploy() {
    echo -e "${YELLOW}=== [INIT] KHỞI TẠO & TRIỂN KHAI DỰ ÁN CHO DEV ===${NC}"
    check_deps
    
    echo -e "${CYAN}[1/5] Kiểm tra file cấu hình môi trường (.env)...${NC}"
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}Đã tạo file .env từ .env.example. Vui lòng kiểm tra lại cấu hình nếu cần thiết.${NC}"
        else
            echo -e "${YELLOW}Cảnh báo: Không tìm thấy file .env hoặc .env.example.${NC}"
        fi
    else
        echo -e "${GREEN}File .env đã tồn tại.${NC}"
    fi

    echo -e "${CYAN}[2/5] Cài đặt dependencies Backend & Frontend...${NC}"
    uv sync
    cd frontend && npm install && cd ..
    
    echo -e "${CYAN}[3/5] Khởi động hạ tầng Docker (Database, Redis, API, UI, Caddy)...${NC}"
    docker compose up -d --build
    
    echo -e "${CYAN}[4/5] Chạy Migration Database...${NC}"
    echo -e "${YELLOW}Đang chờ database sẵn sàng (5s)...${NC}"
    sleep 5
    uv run alembic -c backend/alembic.ini upgrade head || echo -e "${YELLOW}Lưu ý: Migration có thể đã được cập nhật hoặc cần chỉnh sửa.${NC}"
    
    echo -e "${CYAN}[5/5] Cấp chứng chỉ SSL (Local CA Trust)...${NC}"
    chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    
    echo -e "${GREEN}=== HOÀN TẤT KHỞI TẠO Dự Án! ===${NC}"
    echo -e "${CYAN}Hệ thống đã sẵn sàng code. Truy cập: https://smartshop.test (UI) | https://admin.smartshop.test (Admin)${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function run_tests() {
    echo -e "${YELLOW}=== [TEST] KIỂM THỬ HỆ THỐNG ===${NC}"
    echo -e "${CYAN}[1/2] Đang chạy Unit Test Backend (Pytest)...${NC}"
    
    check_deps
    uv run pytest || echo -e "${RED}Kiểm thử Backend có lỗi hoặc chưa thiết lập tests.${NC}"
    
    echo -e "${CYAN}[2/2] Đang chạy Test Frontend...${NC}"
    cd frontend && npm run test || echo -e "${RED}Kiểm thử Frontend có lỗi hoặc chưa thiết lập tests.${NC}"
    cd ..
    
    read -p "Nhấn Enter để quay lại menu..."
}

while true; do
    clear
    echo -e "${CYAN}"
    echo "------------------------------------------------"
    echo "   XOHI OS - COMMANDER v3.2 (V61.1 Standard)    "
    echo "   One-Click Bootstrap & AI Agent Management    "
    echo "------------------------------------------------"
    echo -e "${NC}"

    echo -e "${YELLOW}>>> OPTION SIÊU CẤP:${NC}"
    echo "i) INIT & DEPLOY CAO CẤP (Set up Full A-Z cho Dev mới + cấp SSL)"
    echo "z) ALL-IN-ONE (Clean + Build + Run DEV Docker)"
    echo ""
    echo -e "${CYAN}>>> QUẢN TRỊ & PHÁT TRIỂN:${NC}"
    echo "1) CHẠY DEV (Backend & Frontend Docker)"
    echo "2) SYNC MÔI TRƯỜNG (uv sync & npm install)"
    echo "3) DỌN DẸP RÁC (Cache, Logs, NodeModules...)"
    echo "4) MIGRATION (Cập nhật Database)"
    echo "5) BUILD PRODUCTION"
    echo "t) CHẠY TEST (Kiểm thử hệ thống Backend & Frontend)"
    echo "a) AUDIT V61.1 (Kiểm tra kiến trúc)"
    echo "6) SELF-HEAL (Cứu hộ Orchestrator)"
    echo "0) Thoát (Exit)"
    echo ""
    read -p "Anh chọn cái nào: " choice

    case $choice in
        i)
            init_deploy
            ;;
        z)
            bootstrap_all
            ;;
        t)
            run_tests
            ;;
        a)
            echo -e "${YELLOW}[INFO] Đang quét chuẩn kiến trúc V61.1...${NC}"
            check_deps
            uv run python3 backend/scripts/audit_v61.py
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        1)
            start_dev
            ;;
        2)
            check_deps
            echo -e "${YELLOW}[INFO] Đang đồng bộ hóa thăng cấp môi trường...${NC}"
            uv sync
            cd frontend && npm install && cd ..
            echo -e "${GREEN}== CÀI ĐẶT HOÀN TẤT ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        3)
            deep_clean
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        4)
            echo -e "${YELLOW}[INFO] Đang chạy database migration...${NC}"
            check_deps
            uv run alembic -c backend/alembic.ini upgrade head
            echo -e "${GREEN}== MIGRATION XONG ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        5)
            echo -e "${YELLOW}[INFO] Đang build frontend tĩnh...${NC}"
            cd frontend && npm run build && cd ..
            echo -e "${GREEN}== BUILD XONG: frontend/dist đã sẵn sàng ==${NC}"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        6)
            check_deps
            echo -e "${CYAN}[SELF-HEAL] Đang kích hoạt cơ chế tự chữa lành...${NC}"
            uv run python3 -c "from backend.services.xohi.creative_studio.orchestrator import content_factory; import asyncio; asyncio.run(content_factory.resume_all())"
            echo -e "${GREEN}[OK] Đã quét và Resume các tác vụ đang treo.${NC}"
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

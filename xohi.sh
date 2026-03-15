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

# Helper: OS & Arch check
# [LONG-TERM NOTE: INTEL MAC WORKAROUND]
# Starting from 2024/2025, modern AI libraries (like onnxruntime) dropped support 
# for x86_64 macOS wheels. To keep these "legacy" Intel Macs alive for development,
# we detect them here and shift the heavy lifting into Docker.
IS_INTEL_MAC=false
if [[ "$OSTYPE" == "darwin"* ]] && [[ "$(uname -m)" == "x86_64" ]]; then
    IS_INTEL_MAC=true
    echo -e "${YELLOW}------------------------------------------------${NC}"
    echo -e "${YELLOW}[LONG-TERM NOTE] Hệ thống phát hiện đây là Intel Mac.${NC}"
    echo -e "${YELLOW}Kể từ 2024, onnxruntime đã ngừng hỗ trợ kiến trúc này.${NC}"
    echo -e "${YELLOW}XOHI OS sẽ tự động điều hướng mọi lệnh vào Docker.${NC}"
    echo -e "${YELLOW}------------------------------------------------${NC}"
fi

# Helper: Run Backend Command (Intelligence Routing)
# Why this exists: 
# 1. On Linux/Ubuntu: We run natively for maximum speed.
# 2. On Intel Mac: The local Python environment cannot install core AI deps (onnxruntime).
#    So we "teleport" the command to run inside the Docker container instead.
#    We also fix the path for .env because host absolute paths don't match container paths.
function run_backend() {
    # Chuẩn hóa tham số: Chuyển đường dẫn tuyệt đối của .env sang tương đối
    # Điều này cực kỳ quan trọng để lệnh chạy được cả local (Ubuntu) và trong Docker (Mac)
    local args=()
    for arg in "$@"; do
        if [[ "$arg" == "$PWD/.env" ]]; then
            args+=(".env")
        else
            args+=("$arg")
        fi
    done

    if [ "$IS_INTEL_MAC" = true ]; then
        # On Intel Mac, we MUST run inside the container.
        docker compose exec -T api uv run "${args[@]}"
    else
        # On Ubuntu/Linux, run local for speed
        uv run "${args[@]}"
    fi
}


# Helper: Deep Clean function
function deep_clean() {
    echo -e "${CYAN}[CLEAN] Đang dọn dẹp hệ thống (Code artifacts)...${NC}"
    echo -e "${GREEN}[SAFE] Giữ lại: .env, certs/, .git/${NC}"

    # === FRONTEND CLEANUP ===
    echo -e "${YELLOW}-> [1/5] Đang xóa Frontend rác (node_modules, .pnpm-store, build caches)...${NC}"
    sudo rm -rf frontend/node_modules frontend/dist frontend/.svelte-kit frontend/.vite frontend/.pnpm-store

    # === BACKEND CLEANUP ===
    echo -e "${YELLOW}-> [2/5] Đang xóa Backend rác (.venv, pytest caches)...${NC}"
    sudo rm -rf .venv .pytest_cache backend/.pytest_cache

    # === PYTHON CACHES ===
    echo -e "${YELLOW}-> [3/5] Đang xóa Python caches (__pycache__)...${NC}"
    sudo find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # === LOCK FILES, LOGS, OS JUNK ===
    echo -e "${YELLOW}-> [4/5] Đang xóa Lock files, Logs, .DS_Store...${NC}"
    sudo rm -f uv.lock vad.slice kehoach.txt
    sudo find . -maxdepth 3 -type f \( -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "*.log" -o -name ".DS_Store" \) -delete 2>/dev/null || true

    # === ORPHAN EMPTY DIRS ===
    echo -e "${YELLOW}-> [5/5] Đang xóa thư mục rỗng...${NC}"
    sudo rm -rf static
    sudo find . -maxdepth 3 -type d -empty -not -path './.git/*' -not -path './certs/*' -delete 2>/dev/null || true

    echo -e "${GREEN}[OK] Đã dọn dẹp Code artifacts sạch bóng!${NC}"
}

function hard_reset_docker() {
    echo -e "${CYAN}[CLEAN] Đang reset TOÀN BỘ Docker (như mới cài)...${NC}"
    docker compose down --remove-orphans 2>/dev/null || true
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm -f $(docker ps -aq) 2>/dev/null || true
    docker rmi -f $(docker images -aq) 2>/dev/null || true
    docker volume rm -f $(docker volume ls -q) 2>/dev/null || true
    docker network rm $(docker network ls -q --filter "type=custom") 2>/dev/null || true
    docker system prune -af --volumes 2>/dev/null || true
    docker builder prune -af 2>/dev/null || true
    echo -e "${GREEN}   ✔ Docker đã reset như mới cài!${NC}"
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

    if ! command -v pnpm &> /dev/null; then
        echo -e "${YELLOW}[INFO] Không tìm thấy 'pnpm'. Đang tự động cài đặt qua npm...${NC}"
        sudo npm install -g pnpm
    fi
}

function bootstrap_all() {
    check_deps
    echo -e "${YELLOW}=== [GOD MODE] KHỞI ĐỘNG TỔNG LỰC (DOCKER) ===${NC}"
    mkdir -p certs/caddy/pki
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
    check_deps
    
    echo -e "${YELLOW}-> Đồng bộ thư viện (UV & PNPM)...${NC}"
    if [ "$IS_INTEL_MAC" = true ]; then
        echo -e "${YELLOW}[INTEL MAC] Đang bỏ qua uv sync local để tránh lỗi onnxruntime. Docker sẽ lo việc này.${NC}"
        # Chạy uv sync nhưng không dừng nếu lỗi (nếu sếp muốn thử vận may)
        uv sync || echo -e "${YELLOW}[SKIP] Không thể sync local trên Intel Mac. Chuyển sang dùng Docker...${NC}"
    else
        uv sync
    fi
    (cd frontend && pnpm install)
    
    echo -e "${YELLOW}-> Khởi động Containers...${NC}"
    docker compose up -d
    
    echo -e "${YELLOW}-> Cập nhật Database (Migration)...${NC}"
    # Đợi DB sẵn sàng một chút
    sleep 2
    run_backend --env-file "${PWD}/.env" alembic -c backend/alembic.ini upgrade head || echo -e "${YELLOW}[SKIP] Không có migration mới.${NC}"
    
    echo -e "${GREEN}[READY] Hệ thống đã sẵn sàng cho dev!${NC}"
    echo -e "${CYAN}Admin: https://admin.smartshop.test${NC}"
    echo -e "${CYAN}UI:    https://smartshop.test${NC}"
    echo ""
    echo "Dùng 'docker compose logs -f' để xem log."
    read -p "Nhấn Enter để quay lại menu..."
}

function init_deploy() {
    echo -e "${YELLOW}=== [INIT] KHỞI TẠO TỔNG LỰC (DOCKER - V61.1) ===${NC}"
    check_deps
    
    echo -e "${CYAN}[1/6] Dọn dẹp môi trường (Deep Clean)...${NC}"
    deep_clean
    
    echo -e "${CYAN}[2/6] Kiểm tra file cấu hình môi trường (.env)...${NC}"
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${GREEN}Đã tạo file .env từ .env.example.${NC}"
        else
            echo -e "${YELLOW}Cảnh báo: Không tìm thấy file .env.${NC}"
        fi
    fi

    echo -e "${CYAN}[3/6] Cài đặt dependencies (UV & PNPM)...${NC}"
    mkdir -p certs/caddy/pki
    if [ "$IS_INTEL_MAC" = true ]; then
        echo -e "${YELLOW}[INTEL MAC] Skip uv sync local...${NC}"
        uv sync || true
    else
        uv sync
    fi
    (cd frontend && pnpm install)
    
    echo -e "${CYAN}[4/6] Xây dựng và khởi động Containers (Docker)...${NC}"
    docker compose up -d --build
    
    echo -e "${CYAN}[5/6] Database Migration & SSL Setup...${NC}"
    echo -e "${YELLOW}Đang chờ DB sẵn sàng...${NC}"
    sleep 5
    run_backend --env-file "${PWD}/.env" alembic -c backend/alembic.ini upgrade head
    chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    
    echo -e "${CYAN}[6/6] Gieo mầm dữ liệu (Seeding Database)...${NC}"
    run_backend --env-file "${PWD}/.env" python3 backend/scripts/seed.py
    
    echo -e "${YELLOW}Đang đồng bộ bộ nhớ (Restarting API)...${NC}"
    docker compose restart api
    
    echo -e "${GREEN}=== HỆ THỐNG ĐÃ SẴN SÀNG! ===${NC}"
    echo -e "${CYAN}Truy cập: https://admin.smartshop.test${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function seed_db() {
    echo -e "${YELLOW}=== [SEED] KHỞI TẠO DỮ LIỆU MẪU (R1.5) ===${NC}"
    check_deps
    run_backend --env-file "${PWD}/.env" python3 backend/scripts/seed.py
    echo -e "${GREEN}== SEEDING HOÀN TẤT! ==${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function run_tests() {
    echo -e "${YELLOW}=== [TEST] KIỂM THỬ HỆ THỐNG ===${NC}"
    echo -e "${CYAN}[1/2] Backend (Pytest)...${NC}"
    check_deps
    run_backend pytest || echo -e "${RED}Lỗi Test Backend.${NC}"
    echo -e "${CYAN}[2/2] Frontend (Vitest)...${NC}"
    (cd frontend && pnpm run test) || echo -e "${RED}Lỗi Test Frontend.${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function view_logs() {
    echo -e "${CYAN}[LOGS] Đang xem log LỖI Backend (api) trong 5 phút qua...${NC}"
    echo -e "${YELLOW}Nhấn Ctrl+C để quay lại menu.${NC}"
    docker compose logs -f api --tail 100 --since 5m --no-log-prefix | grep -Ei --line-buffered "ERROR|CRITICAL|EXCEPTION"
}

while true; do
    clear
    echo -e "${CYAN}"
    echo "------------------------------------------------"
    echo "   XOHI OS - COMMANDER v4.0 (LOCKDOWN)          "
    echo "------------------------------------------------"
    echo -e "${NC}"

    echo -e "${YELLOW}>>> LÊNH TỔNG LỰC:${NC}"
    echo "1) FULL INIT (Clean + Build + Migration + Seed + SSL)"
    echo ""
    echo -e "${CYAN}>>> CÔNG CỤ HỖ TRỢ:${NC}"
    echo "2) CHẠY DEV (Docker Up)"
    echo "3) DỌN DẸP RÁC (Deep Clean)"
    echo "4) BUILD PRODUCTION"
    echo "5) SELF-HEAL (Resume Orchestrator)"
    echo "6) CHẠY TEST (Backend/Frontend)"
    echo "7) AUDIT V61.1"
    echo "8) XEM LOG BACKEND"
    echo "0) Thoát (Exit)"
    echo ""
    read -p "Sếp chọn lệnh nào: " choice

    case $choice in
        1)
            init_deploy
            ;;
        2)
            start_dev
            ;;
        3)
            hard_reset_docker
            deep_clean
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        4)
            echo -e "${YELLOW}[INFO] Đang build frontend tĩnh...${NC}"
            (cd frontend && pnpm run build)
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        5)
            check_deps
            run_backend --env-file "${PWD}/.env" python3 -c "from backend.services.xohi.creative_studio.orchestrator import content_factory; import asyncio; asyncio.run(content_factory.resume_all())"
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        6)
            run_tests
            ;;
        7)
            run_backend --env-file "${PWD}/.env" python3 backend/scripts/audit_v61.py
            read -p "Nhấn Enter để tiếp tục..."
            ;;
        8)
            view_logs
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

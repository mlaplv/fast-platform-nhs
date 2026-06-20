#!/usr/bin/env bash
export PYTHONPATH="${PWD}"
export PATH="$HOME/.local/bin:$PATH"

# XOHI OS - PROJECT MANAGEMENT COMMANDER v3.2 (LOCKDOWN)
# Optimized for UV (Backend) & Vite/NPM (Frontend)
# No PNPM, No Turbo.

set -e
set -o pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
 
# [GHOST MODE] Adaptive Resource Management
TOTAL_RAM_GB=0
if [[ "$OSTYPE" == "darwin"* ]]; then
    TOTAL_RAM_GB=$(($(sysctl -n hw.memsize) / 1024 / 1024 / 1024))
elif [[ -f /proc/meminfo ]]; then
    TOTAL_RAM_GB=$(grep MemTotal /proc/meminfo | awk '{print int($2/1024/1024)}')
fi

# Default Performance Settings (High RAM > 12GB)
export UV_CONCURRENCY=8
export PNPM_CONCURRENCY=4
export DOCKER_BUILDKIT=1
export COMPOSE_PARALLEL_LIMIT=10
export API_MEM_LIMIT="4G"
export UI_MEM_LIMIT="2G"
export WORKER_MEM_LIMIT="2G"

if [ "$TOTAL_RAM_GB" -le 12 ]; then
    echo -e "${YELLOW}[GHOST MODE] Hệ thống phát hiện RAM thấp (${TOTAL_RAM_GB}GB). Đang tối ưu Pháo Đài...${NC}"
    export UV_CONCURRENCY=2
    export PNPM_CONCURRENCY=1
    export COMPOSE_PARALLEL_LIMIT=1
    # Elite V2.2: Hardened Limits for 4GB VPS (Strict Compliance)
    export API_MEM_LIMIT="1.2G"
    export UI_MEM_LIMIT="512M"
    export WORKER_MEM_LIMIT="768M"
    # Anti-Lag: Disable heavy source maps & Enable Glibc Fragment Protection
    export NODE_OPTIONS="--max-old-space-size=448"
    export MALLOC_ARENA_MAX=2
else
    echo -e "${GREEN}[ELITE MODE] Hệ thống phát hiện RAM dồi dào (${TOTAL_RAM_GB}GB). Chạy tối đa tốc độ!${NC}"
fi

# Extract REDIS_PASSWORD from .env
REDIS_PASS=""
if [ -f .env ]; then
    REDIS_PASS=$(grep -E "^REDIS_PASSWORD=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
fi

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


# Helper: Flush Caddy Cache (SEO/HTML stale content)
function flush_caddy_cache() {
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_caddy"; then
        echo -e "${CYAN}[CADDY] Đang xóa cache Caddy (Reverse Proxy)...${NC}"
        # Xóa cache nội bộ của Caddy container
        docker exec fast_platform_caddy sh -c 'rm -rf /data/caddy/cache/* /tmp/caddy_cache/* 2>/dev/null' || true
        # Restart Caddy để flush toàn bộ in-memory cache + stale SSR HTML
        docker compose restart caddy 2>/dev/null || true
        echo -e "${GREEN}   ✔ Đã xóa sạch Caddy Cache và restart gateway!${NC}"
    else
        echo -e "${YELLOW}[SKIP] Container Caddy không chạy. Bỏ qua.${NC}"
    fi
}

# Helper: Deep Clean function
function deep_clean() {
    echo -e "${CYAN}[CLEAN] Đang dọn dẹp hệ thống (Code artifacts & Caches)...${NC}"
    echo -e "${GREEN}[SAFE] Giữ lại: .env, certs/, .git/${NC}"

    # === FRONTEND CLEANUP ===
    echo -e "${YELLOW}-> [1/6] Đang xóa Frontend rác (node_modules, .pnpm-store, build caches)...${NC}"
    sudo rm -rf frontend/node_modules frontend/dist frontend/.svelte-kit frontend/.vite frontend/.pnpm-store

    # === BACKEND CLEANUP ===
    echo -e "${YELLOW}-> [2/6] Đang xóa Backend rác (.venv, pytest caches)...${NC}"
    sudo rm -rf .venv .pytest_cache backend/.pytest_cache

    # === PYTHON CACHES ===
    echo -e "${YELLOW}-> [3/6] Đang xóa Python caches (__pycache__)...${NC}"
    sudo find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

    # === DATA & APPLICATION CACHES ===
    echo -e "${YELLOW}-> [4/6] Đang xóa Application Caches (backend/cache - GIỮ LẠI fastembed)...${NC}"
    # [CTO ELITE] Giữ lại cache model AI để tránh tải lại 500MB mỗi lần dọn rác (R00: RAM/Latency)
    if [ -d "backend/cache" ]; then
        sudo find backend/cache -mindepth 1 -maxdepth 1 ! -name 'fastembed' -exec rm -rf {} + 2>/dev/null || true
    fi

    # === LOCK FILES, LOGS, OS JUNK ===
    echo -e "${YELLOW}-> [5/7] Đang xóa Logs, .DS_Store... (Giữ lại Lock files)${NC}"
    sudo rm -f vad.slice kehoach.txt
    sudo find . -maxdepth 3 -type f \( -name "*.log" -o -name ".DS_Store" \) -delete 2>/dev/null || true

    # === ORPHAN EMPTY DIRS ===
    echo -e "${YELLOW}-> [6/7] Đang xóa thư mục rỗng...${NC}"
    sudo rm -rf static
    sudo find . -maxdepth 3 -type d -empty -not -path './.git/*' -not -path './certs/*' -delete 2>/dev/null || true

    # === CADDY CACHE FLUSH ===
    echo -e "${YELLOW}-> [7/7] Đang xóa Caddy Cache (SEO/HTML cũ)...${NC}"
    flush_caddy_cache

    # === DOCKER CLEANUP ===
    echo -e "${YELLOW}-> [Docker] Đang dọn dẹp Build Cache & Dangling Images...${NC}"
    docker builder prune -a -f &>/dev/null || true
    docker image prune -f &>/dev/null || true

    echo -e "${GREEN}[OK] Đã dọn dẹp hệ thống sạch bóng!${NC}"
}

function hard_reset_docker() {
    echo -e "${CYAN}[CLEAN] Đang reset TOÀN BỘ Docker (như mới cài)...${NC}"
    docker compose down --remove-orphans 2>/dev/null || true
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm -f $(docker ps -aq) 2>/dev/null || true
    docker rmi -f $(docker images -aq) 2>/dev/null || true
    # [ELITE VPS PROTECT] Chỉ xóa các volumes của database/cache, giữ lại volume SSL của Caddy để tránh bị Let's Encrypt block rate limit
    docker volume ls -q | grep -vE "caddy_data|caddy_config" | xargs -r docker volume rm -f 2>/dev/null || true
    docker network rm $(docker network ls -q --filter "type=custom") 2>/dev/null || true
    # Bỏ cờ --volumes để bảo vệ an toàn cho volume caddy_data
    docker system prune -af 2>/dev/null || true
    docker builder prune -af 2>/dev/null || true
    echo -e "${GREEN}   ✔ Docker đã reset sạch bóng (Bảo lưu chứng chỉ SSL Caddy)!${NC}"
}

function prune_docker_garbage() {
    echo -e "${CYAN}[CLEAN] ĐANG DỌN DẸP DOCKER (CHỈ GIỮ CÁC MỤC ĐANG CHẠY)...${NC}"
    
    echo -e "${YELLOW}-> [1/4] Đang xóa các container đã dừng (Stopped Containers)...${NC}"
    docker container prune -f
    
    echo -e "${YELLOW}-> [2/4] Đang xóa các image không sử dụng (Unused Images)...${NC}"
    # Prunes all unused images (both dangling and unreferenced by any running container)
    docker image prune -a -f
    
    echo -e "${YELLOW}-> [3/4] Đang xóa các volume không sử dụng (Unused Volumes)...${NC}"
    docker volume prune -f
    
    echo -e "${YELLOW}-> [4/4] Đang giải phóng bộ nhớ đệm build (Build Cache)...${NC}"
    docker builder prune -a -f
    
    echo -e "${GREEN}[SUCCESS] Đã dọn dẹp Docker cực kỳ sạch sẽ! Chỉ giữ lại các container/image/volume đang hoạt động.${NC}"
}

function update_docker() {
    local NO_WAIT=false
    if [[ "$1" == "--no-wait" ]]; then
        NO_WAIT=true
    fi

    echo -e "${CYAN}[SYSTEM] ĐÀO THẢI & NÂNG CẤP DOCKER ENGINE (UBUNTU)${NC}"
    echo -e "${RED}[WARNING] Thao tác này sẽ xóa SẠCH toàn bộ Images (Bản Build), Containers, Volumes, Cache!${NC}"
    
    if [ "$NO_WAIT" = false ]; then
        read -p "Sếp chắc chắn muốn thực hiện? (y/n): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    # 1. Làm sạch triệt để (Deep Clean Docker)
    hard_reset_docker

    # 2. Cập nhật Docker Engine
    echo -e "${YELLOW}-> [1/2] Đang cập nhật danh sách gói (apt update)...${NC}"
    sudo apt-get update -y
    
    echo -e "${YELLOW}-> [2/2] Đang nâng cấp Docker Engine & Plugins...${NC}"
    # Đảm bảo cài đặt các thành phần cốt lõi của Docker hiện đại
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    if [ "$NO_WAIT" = false ]; then
        echo -e "${GREEN}[SUCCESS] Đã bảo trì hệ thống Docker Engine thành công!${NC}"
        echo -e "${CYAN}[TIP] Sếp có thể dùng Mục 2 (FULL INIT) sau đây để rebuild dự án sạch sẽ.${NC}"
        read -p "Nhấn Enter để quay lại menu..."
    fi
}

# Helper: Rotate Encryption Key (Identity Shield)
function rotate_encryption_key() {
    echo -e "${CYAN}[SECURITY] Đang tạo dấu niêm phong mới (Rotate Encryption Salt)...${NC}"
    if [ ! -f .env ]; then
        echo -e "${RED}[ERROR] Không tìm thấy file .env để rotate key.${NC}"
        return 1
    fi

    # Generate a 32-char random string (Military Grade)
    NEW_SALT=$(openssl rand -hex 16)
    
    # Check if ENCRYPTION_SALT exists
    if grep -q "ENCRYPTION_SALT=" .env; then
        # Update existing
        sed -i "s/^ENCRYPTION_SALT=.*/ENCRYPTION_SALT=$NEW_SALT/" .env
    else
        # Append new
        echo "ENCRYPTION_SALT=$NEW_SALT" >> .env
    fi
    echo -e "${GREEN}[OK] Đã Rotate Encryption Salt thành công. Toàn bộ session cũ đã bị vô hiệu hóa.${NC}"
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

# Helper: Ensure Lock files exist before build
function ensure_locks() {
    echo -e "${CYAN}[SAFEGUARD] Đang kiểm tra tính toàn vẹn của Pháo đài...${NC}"
    
    if [ ! -f "uv.lock" ]; then
        echo -e "${YELLOW}[WARNING] Thiếu uv.lock. Đang tự động gieo mầm (uv lock)...${NC}"
        uv lock
    fi

    if [ ! -f "frontend/pnpm-lock.yaml" ]; then
        echo -e "${YELLOW}[WARNING] Thiếu pnpm-lock.yaml. Đang tạo môi trường frontend...${NC}"
        (cd frontend && pnpm install --lockfile-only)
    fi
    
    echo -e "${GREEN}[OK] Đã xác nhận đầy đủ Lock files.${NC}"
}

function init_deploy() {
    local NO_SEED=false
    if [[ "$1" == "--no-seed" ]]; then
        NO_SEED=true
    fi

    # [ELITE V2.2] Bảo trì hệ thống trước khi khởi tạo dự án
    update_docker --no-wait || return 1
    
    echo -e "${YELLOW}=== [INIT] KHỞI TẠO TỔNG LỰC (DOCKER - V61.1) ===${NC}"
    check_deps
    
    echo -e "${CYAN}[1/6] Dọn dẹp môi trường (Deep Clean)...${NC}"
    deep_clean
    
    # Rotate keys during fresh deploy to prevent "Ghost Identity" issues
    rotate_encryption_key
    
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
        uv venv --python 3.14 && source .venv/bin/activate
        uv pip install -e . || true
    else
        echo -e "${CYAN}-> Đang tạo môi trường ảo (Python 3.14)...${NC}"
        uv venv --seed --python 3.14
        source .venv/bin/activate
        echo -e "${CYAN}-> Đang cài đặt Core Dependencies (Mirror Mode)...${NC}"
        ./.venv/bin/pip install --upgrade pip
        ./.venv/bin/pip install "litellm>=1.83.0"
        uv pip install litestar[standard] advanced-alchemy asyncpg pydantic-ai
        uv pip install -e .
    fi
    echo -e "${CYAN}-> [CTO ELITE] Đang tạo uv.lock cho Docker...${NC}"
    uv lock || true
    (cd frontend && pnpm install)
    
    echo -e "${CYAN}[4/6] Xây dựng và khởi động Cơ sở hạ tầng (Database & Cache)...${NC}"
    docker compose build db redis caddy
    docker compose up -d db redis caddy
    
    echo -e "${CYAN}[5/6] Database Migration & SSL Setup...${NC}"
    echo -e "${YELLOW}Đang chờ DB sẵn sàng...${NC}"
    sleep 5
    echo -e "${YELLOW}Đang chạy Migration (Một lần)...${NC}"
    docker compose run --rm api /opt/venv/bin/alembic -c backend/alembic.ini upgrade head
    
    echo -e "${CYAN}[6/6] Khởi tạo dữ liệu (Data Injection)...${NC}"
    
    if [ "$NO_SEED" = true ]; then
        db_choice=3
        echo -e "${YELLOW}-> [BLANK DB] Tự động bỏ qua Seeding theo yêu cầu.${NC}"
    else
        echo -e "Sếp muốn làm gì với Database?"
        echo "1) Cháy Seed DB Test (Dữ liệu mẫu)"
        echo "2) Khôi phục từ bản sao lưu (Restore Backup)"
        echo "3) Bỏ qua (Giữ DB trắng)"
        db_choice=""
        for i in {10..1}; do
            echo -ne "\rLựa chọn của Sếp (mặc định 1 sau ${i}s): "
            if read -t 1 input; then
                db_choice=$input
                break
            fi
        done

        if [[ -z "$db_choice" ]]; then
            db_choice=1
            echo -e "\n${YELLOW}-> Tự động chọn mục 1 (Seed DB)...${NC}"
        else
            echo -e "" 
        fi
    fi

    case $db_choice in
        1)
            echo -e "${YELLOW}-> Đang chạy Seeding (Dữ liệu mẫu Test)...${NC}"
            docker compose run --rm api /opt/venv/bin/python3 -m backend.scripts.seed
            ;;
        2)
            echo -e "${YELLOW}-> Đang chuyển sang quy trình Khôi phục (Restore)...${NC}"
            restore_data
            ;;
        *)
            echo -e "${YELLOW}[SKIP] Không gieo mầm dữ liệu.${NC}"
            if [ "$NO_SEED" = false ]; then
                echo -e "Sếp có muốn khởi tạo Super User (Admin) để đăng nhập không? (y/n)"
                read -p "Lựa chọn (mặc định y): " create_admin
                if [[ -z "$create_admin" || "$create_admin" =~ ^[Yy]$ ]]; then
                    create_superuser
                fi
            else
                echo -e "${YELLOW}[INFO] Bỏ qua bước xác nhận tạo Super User (Dành cho bản 3.1).${NC}"
            fi
            ;;
    esac
    
    echo -e "${YELLOW}Đang khởi động toàn bộ dịch vụ (API, Worker & UI)...${NC}"
    docker compose build api worker_high worker_default ui
    export SKIP_MIGRATE=true
    docker compose up -d --remove-orphans api worker_high worker_default ui
    if [ "$NO_SEED" = true ]; then
        echo -e "${GREEN}[SSL] Đã có cấu hình SSL thật trên VPS. Bỏ qua thiết lập SSL Local CA.${NC}"
    else
        chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    fi
    
    echo -e "${GREEN}=== HỆ THỐNG ĐÃ SẴN SÀNG! (Đã tối ưu RAM) ===${NC}"
    echo -e "${CYAN}Truy cập: https://admin.osmo.vn${NC}"
    view_logs
}

function update_ai_model() {
    echo -e "${YELLOW}=== [AI] CẬP NHẬT MODEL (FAST-PLATFORM ELITE) ===${NC}"
    echo -e "${RED}[WARNING] Thao tác này sẽ xóa cache và tải lại model ~250MB từ Internet.${NC}"
    read -p "Sếp muốn tiến hành cập nhật? (y/n): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}-> Đang dọn dẹp cache model cũ...${NC}"
        # Xóa cả cấu trúc cũ (models-qdrant) và cấu trúc mới (basename) để đảm bảo sạch sẽ
        sudo rm -rf backend/cache/fastembed/paraphrase-multilingual-MiniLM-L12-v2
        sudo rm -rf backend/cache/fastembed/models--qdrant--paraphrase-multilingual-MiniLM-L12-v2-onnx-Q
        
        echo -e "${CYAN}-> Đang khởi động lại Backend để kích hoạt tải model mới...${NC}"
        docker compose stop api && docker compose rm -f api && docker compose up -d api
        echo -e "${GREEN}[SUCCESS] Khởi động lại API thành công!${NC}"
        echo -e "${YELLOW}[TIP] Sếp hãy xem Log (Mục 3) để theo dõi tiến trình tải model mới.${NC}"
    else
        echo -e "${YELLOW}-> Đã hủy cập nhật.${NC}"
    fi
    read -p "Nhấn Enter để quay lại menu..."
}

function create_superuser() {
    ensure_locks
    echo -e "${CYAN}[AUTH] Đang khởi tạo Super User (Admin Elite 2026)...${NC}"
    # Đảm bảo dùng 'run --rm' để có môi trường cô lập và kết nối DB ổn định
    docker compose run --rm api /opt/venv/bin/python3 -m backend.scripts.init_superuser
    echo -e "${GREEN}[OK] Đã hoàn tất quy trình khởi tạo Admin.${NC}"
}





function view_logs() {
    echo -e "${CYAN}[LOGS] Đang kiểm tra tín hiệu Backend (api + workers)...${NC}"
    echo -e "${YELLOW}Nhấn Ctrl+C để quay lại menu.${NC}"
    # Hiện 10 dòng cuối bất kể loại log để Sếp biết hệ thống vẫn chạy
    docker compose logs --tail 10 api worker_high worker_default
    echo -e "${YELLOW}--- Đang theo dõi lỗi mới (ERROR/CRITICAL/WARNING) ---${NC}"
    docker compose logs -f api worker_high worker_default --tail 100 --since 5m --no-log-prefix | grep -Ei --line-buffered "ERROR|CRITICAL|EXCEPTION|WARNING"
}

function backup_data() {
    BACKUP_DIR="backups"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BKP_NAME="XOHI_BKP_$TIMESTAMP"
    
    echo -e "${CYAN}[BACKUP] Đang khởi tạo bản sao lưu Elite V2.2...${NC}"
    mkdir -p "$BACKUP_DIR/$BKP_NAME"
    
    # [1/4] Database Dump
    echo -e "${YELLOW}-> 1. Đang trích xuất Database (PostgreSQL)...${NC}"
    if ! docker exec fast_platform_db pg_dump -U postgres fast_platform > "$BACKUP_DIR/$BKP_NAME/db.sql" 2>/dev/null; then
        echo -e "${RED}[ERROR] Không thể kết nối DB. Sếp hãy chắc chắn Docker đang chạy!${NC}"
        rm -rf "$BACKUP_DIR/$BKP_NAME"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi
    
    # [2/4] Media Files
    echo -e "${YELLOW}-> 2. Đang đóng gói hình ảnh (uploads)...${NC}"
    if [ -d "frontend/static/uploads" ]; then
        sudo cp -r frontend/static/uploads "$BACKUP_DIR/$BKP_NAME/"
        sudo chown -R $USER:$USER "$BACKUP_DIR/$BKP_NAME/uploads"
    else
        mkdir -p "$BACKUP_DIR/$BKP_NAME/uploads"
    fi
    
    # [3/4] Metadata & Versioning
    echo -e "${YELLOW}-> 3. Tạo Manifest & Versioning...${NC}"
    echo "TIMESTAMP=$TIMESTAMP" > "$BACKUP_DIR/$BKP_NAME/manifest.txt"
    git rev-parse HEAD > "$BACKUP_DIR/$BKP_NAME/git_version.txt" 2>/dev/null || echo "not_a_git_repo" > "$BACKUP_DIR/$BKP_NAME/git_version.txt"
    
    # [4/4] Compression & Security (AES-256)
    echo -e "${YELLOW}-> 4. Đang mã hóa AES-256 & tạo mã bảo mật (SHA256)...${NC}"
    read -s -p "Nhập mật khẩu để bảo vệ bản sao lưu: " BKP_PASS
    echo ""
    
    tar -czf - -C "$BACKUP_DIR" "$BKP_NAME" | openssl enc -aes-256-cbc -salt -pbkdf2 -out "$BACKUP_DIR/$BKP_NAME.tar.gz.enc" -pass pass:"$BKP_PASS"
    sha256sum "$BACKUP_DIR/$BKP_NAME.tar.gz.enc" | awk '{print $1}' > "$BACKUP_DIR/$BKP_NAME.tar.gz.enc.sha256"
    
    rm -rf "$BACKUP_DIR/$BKP_NAME"
    
    # Pruning (Keep only last 5)
    ls -t "$BACKUP_DIR"/XOHI_BKP_*.tar.gz.enc 2>/dev/null | tail -n +6 | xargs -I {} rm -f {} 2>/dev/null || true
    ls -t "$BACKUP_DIR"/XOHI_BKP_*.tar.gz.enc.sha256 2>/dev/null | tail -n +6 | xargs -I {} rm -f {} 2>/dev/null || true
    
    echo -e "${GREEN}[SUCCESS] Đã sao lưu và mã hóa thành công: $BKP_NAME.tar.gz.enc${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function purge_helen_data() {
    echo -e "${RED}[PURGE] ĐANG LÀM SẠCH DỮ LIỆU HELEN (CHAT LOGS & AI MEMORY)...${NC}"
    echo -e "${YELLOW}[WARNING] Thao tác này sẽ xóa vĩnh viễn toàn bộ lịch sử tư vấn và bộ nhớ đệm AI.${NC}"
    read -p "Sếp chắc chắn muốn thực hiện? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then return 1; fi

    # 1. Database Purge (Chat History & Telemetry)
    echo -e "${CYAN}-> [1/2] Đang xóa dữ liệu trong Database (PostgreSQL)...${NC}"
    # Xử lý xóa đồng thời nhiều bảng để đảm bảo tính nhất quán (Elite V2.2)
    docker exec fast_platform_db psql -U postgres -d fast_platform -c "DELETE FROM support_chat_history; DELETE FROM unified_agent_tasks; DELETE FROM agent_telemetry_logs; DELETE FROM chat_messages;" || echo -e "${YELLOW}[SKIP] DB Purge failed, maybe containers are down?${NC}"

    # 2. Redis Purge (Memory Caches)
    echo -e "${CYAN}-> [2/2] Đang xóa bộ nhớ đệm AI (Redis)...${NC}"
    # Use scan + xargs to avoid blocking Redis if large keys exist (Elite V2.2 RAM Guard)
    if [ -n "$REDIS_PASS" ]; then
        docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "xohi:chat:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
        docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "xohi:ctx:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
        docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "support:kb:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
        docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "support:presence:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
        docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "support:takeover:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
    else
        docker exec fast_platform_redis redis-cli --scan --pattern "xohi:chat:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
        docker exec fast_platform_redis redis-cli --scan --pattern "xohi:ctx:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
        docker exec fast_platform_redis redis-cli --scan --pattern "support:kb:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
        docker exec fast_platform_redis redis-cli --scan --pattern "support:presence:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
        docker exec fast_platform_redis redis-cli --scan --pattern "support:takeover:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
    fi
    
    echo -e "${GREEN}[SUCCESS] Đã làm sạch toàn bộ dữ liệu Helen cực kỳ triệt để!${NC}"
    # Trigger inbox update across browsers (Global Admin Pulse)
    docker exec fast_platform_api /opt/venv/bin/python3 -c "import asyncio; from backend.services.event_bus import event_bus; asyncio.run(event_bus.emit('SUPPORT_INBOX_UPDATE', {'session_id': 'all', 'action': 'PURGE_ALL'}))" || true
}

function restore_data() {
    BACKUP_DIR="backups"
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/*.enc 2>/dev/null)" ]; then
        echo -e "${RED}[ERROR] Không tìm thấy bản sao lưu .enc nào trong thư mục 'backups/'.${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi
    
    echo -e "${CYAN}[RESTORE] Danh sách bản sao lưu mã hóa khả dụng:${NC}"
    select ARCHIVE in "$BACKUP_DIR"/*.enc; do
        if [ -n "$ARCHIVE" ]; then
            break
        fi
    done
    
    echo -e "${YELLOW}-> Đang kiểm tra tính toàn vẹn (Integrity Check)...${NC}"
    EXPECTED_SHA=$(cat "${ARCHIVE}.sha256" 2>/dev/null || echo "none")
    ACTUAL_SHA=$(sha256sum "$ARCHIVE" | awk '{print $1}')
    
    if [ "$EXPECTED_SHA" != "none" ] && [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
        echo -e "${RED}[CAUTION] Mã SHA256 không khớp! File backup có thể đã bị hỏng.${NC}"
        read -p "Sếp vẫn muốn tiếp tục? (y/n): " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then return 1; fi
    fi
    
    # [SAFETY] Backup current state before restore
    echo -e "${YELLOW}-> Đang tạo bản lưu an toàn (Pre-Restore Safety)...${NC}"
    mkdir -p "$BACKUP_DIR/safety_net"
    docker exec fast_platform_db pg_dump -U postgres fast_platform > "$BACKUP_DIR/safety_net/pre_restore_db.sql" 2>/dev/null || true
    
    echo -e "${CYAN}-> Đang giải mã và khôi phục...${NC}"
    read -s -p "Nhập mật khẩu để giải mã: " BKP_PASS
    echo ""
    
    TEMP_RESTORE="temp_restore"
    # [ELITE 2.2] Đảm bảo dọn sạch thư mục tạm trước khi giải mã để tránh 'lẫn folder' cũ
    rm -rf "$TEMP_RESTORE"
    mkdir -p "$TEMP_RESTORE"
    
    if ! openssl enc -aes-256-cbc -d -pbkdf2 -in "$ARCHIVE" -pass pass:"$BKP_PASS" | tar -xzf - -C "$TEMP_RESTORE" 2>/dev/null; then
        echo -e "${RED}[ERROR] Sai mật khẩu hoặc file bị hỏng!${NC}"
        rm -rf "$TEMP_RESTORE"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi
    
    # [ELITE 2.2] Chỉ lấy thư mục đầu tiên để tránh lỗi khi có nhiều folder rác trong temp_restore
    BKP_FOLDER=$(ls -1 "$TEMP_RESTORE" | head -n 1)

    if [ -z "$BKP_FOLDER" ]; then
        echo -e "${RED}[ERROR] Không tìm thấy dữ liệu sau khi giải mã!${NC}"
        rm -rf "$TEMP_RESTORE"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi
    
    # Restore DB
    echo -e "${YELLOW}-> 1. Đang khôi phục Database (Dọn sạch Schema cũ)...${NC}"
    if [ -f "$TEMP_RESTORE/$BKP_FOLDER/db.sql" ]; then
        docker exec -t fast_platform_db psql -U postgres -d fast_platform -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null
        cat "$TEMP_RESTORE/$BKP_FOLDER/db.sql" | docker exec -i fast_platform_db psql -U postgres fast_platform > /dev/null
    else
        echo -e "${YELLOW}[SKIP] Không tìm thấy file db.sql trong bản sao lưu.${NC}"
    fi
    
    # Restore Media
    echo -e "${YELLOW}-> 2. Đang khôi phục hình ảnh (Media/Uploads)...${NC}"
    if [ -d "$TEMP_RESTORE/$BKP_FOLDER/uploads" ]; then
        sudo mkdir -p frontend/static/uploads
        sudo cp -r "$TEMP_RESTORE/$BKP_FOLDER/uploads/"* frontend/static/uploads/
        sudo chown -R root:root frontend/static/uploads # Keeping it consistent with Docker expectations
    fi
    
    rm -rf "$TEMP_RESTORE"
    
    echo -e "${YELLOW}-> 3. Đang khởi động lại hệ thống để làm mới cache...${NC}"
    # [ELITE 2.2] Auto-Reindex AI Knowledge (RAG Memory Restoration)
    echo -e "${YELLOW}-> 4. Đang tái nạp tri thức Helen (AI Knowledge Re-indexing)...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        docker exec -t fast_platform_api /opt/venv/bin/python3 backend/services/commerce/reindex_knowledge.py || echo -e "${RED}[WARNING] Re-indexing failed via exec.${NC}"
    else
        echo -e "${CYAN}[INFO] Container API chưa chạy. Sử dụng 'run --rm' để thực thi chuyên biệt...${NC}"
        docker compose run --rm api /opt/venv/bin/python3 backend/services/commerce/reindex_knowledge.py || echo -e "${RED}[WARNING] Re-indexing failed via run.${NC}"
    fi

    echo -e "${GREEN}[SUCCESS] Đã khôi phục dữ liệu và tri thức AI hoàn tất!${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function clean_backups() {
    BACKUP_DIR="backups"
    echo -e "${RED}[WARNING] THAO TÁC NGUY HIỂM: Xóa vĩnh viễn toàn bộ bản sao lưu!${NC}"
    read -s -p "Sếp hãy nhập mật mã quản trị (Admin Password): " confirm_pass
    echo ""
    
    echo -e "${YELLOW}-> Đang xác thực quyền hạn...${NC}"
    # Xác thực mật khẩu admin thông qua container api
    if docker exec -i fast_platform_api /opt/venv/bin/python3 -m backend.scripts.verify_admin "$confirm_pass" | grep -q "MATCH"; then
        echo -e "${YELLOW}-> Xác thực thành công. Đang dọn dẹp thư mục backups/...${NC}"
        sudo rm -rf "${BACKUP_DIR:?}"/*
        echo -e "${GREEN}[OK] Đã dọn sạch toàn bộ bản sao lưu!${NC}"
    else
        echo -e "${RED}[ERROR] Sai mật mã quản trị! Thao tác bị từ chối.${NC}"
    fi
    read -p "Nhấn Enter để quay lại menu..."
}

function manage_security_users() {
    echo -e "${YELLOW}=== [SECURITY] QUẢN TRỊ USER & SSH LOCKDOWN (ELITE V2.2) ===${NC}"
    echo "1) Tạo User quản trị mới (Sudoer)"
    echo "2) Khóa đăng nhập ROOT (Lockdown SSH)"
    echo "3) Mở lại đăng nhập ROOT (Unlock SSH)"
    echo "0) Quay lại"
    read -p "Sếp chọn lệnh nào: " sec_choice

    case $sec_choice in
        1)
            read -p "Nhập tên User mới (ví dụ: troly_smartshop): " new_user
            if id "$new_user" &>/dev/null; then
                echo -e "${RED}[ERROR] User $new_user đã tồn tại!${NC}"
            else
                sudo adduser "$new_user"
                sudo usermod -aG sudo "$new_user"
                echo -e "${GREEN}[SUCCESS] Đã tạo User $new_user và cấp quyền Sudo.${NC}"
                echo -e "${YELLOW}[TIP] Sếp hãy thử SSH bằng user này trước khi khóa Root!${NC}"
            fi
            ;;
        2)
            echo -e "${RED}[WARNING] THAO TÁC NGUY HIỂM: Khóa đăng nhập Root sẽ khiến Sếp không thể login bằng 'root'.${NC}"
            read -p "Sếp chắc chắn đã có user sudo khác và muốn khóa Root? (y/n): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "${CYAN}-> Đang cấu hình SSH Lockdown...${NC}"
                # Update PermitRootLogin to no
                sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
                sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
                
                echo -e "${CYAN}-> Đang khởi động lại dịch vụ SSH...${NC}"
                sudo systemctl restart ssh || sudo systemctl restart sshd
                echo -e "${GREEN}[SUCCESS] Đã khóa đăng nhập Root! Kẻ xấu sẽ không thể 'dò' pass Root nữa.${NC}"
            fi
            ;;
        3)
            echo -e "${YELLOW}=== [REVERSAL] MỞ LẠI ĐĂNG NHẬP ROOT ===${NC}"
            read -p "Sếp xác nhận muốn mở lại quyền login Root? (y/n): " confirm
            if [[ "$confirm" =~ ^[Yy]$ ]]; then
                echo -e "${CYAN}-> Đang cấu hình SSH Unlock...${NC}"
                sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
                sudo systemctl restart ssh || sudo systemctl restart sshd
                echo -e "${GREEN}[SUCCESS] Đã mở lại đăng nhập Root! Sếp có thể dùng 'root' để login.${NC}"
            fi
            ;;
        0) return ;;
    esac
    read -p "Nhấn Enter để tiếp tục..."
}

function show_elite_guide() {
    clear
    echo -e "${CYAN}==================================================${NC}"
    echo -e "${CYAN}   HƯỚNG DẪN VẬN HÀNH PHÁO ĐÀI (ELITE V2.2)      ${NC}"
    echo -e "${CYAN}==================================================${NC}"
    echo ""
    echo -e "${YELLOW}1. BẢO MẬT & SSH (Mục 12):${NC}"
    echo -e "   - BƯỚC 1: Tạo User mới (Mục 12.1). Nhớ kỹ mật khẩu!"
    echo -e "   - BƯỚC 2: Thử SSH bằng User mới (Mở tab mới, gõ: ssh user@ip)."
    echo -e "   - BƯỚC 3: Nếu vào được, mới chọn Khóa Root (Mục 12.2)."
    echo -e "   - CẤP CỨU: Nếu quên pass hoặc muốn mở lại Root, dùng user mới gõ:"
    echo -e "     sudo sed -i 's/PermitRootLogin no/PermitRootLogin yes/g' /etc/ssh/sshd_config"
    echo -e "     sudo systemctl restart ssh"
    echo ""
    echo -e "${YELLOW}2. BẢO TRÌ TỰ ĐỘNG (Mục 11):${NC}"
    echo -e "   - Sau khi chạy Mục 11, VPS sẽ tự dọn rác lúc 04:00 sáng hàng ngày."
    echo -e "   - Sếp không cần lo đầy ổ 60GB SSD."
    echo ""
    echo -e "${YELLOW}3. KIỂM TRA SỨC KHỎE (Mục 4):${NC}"
    echo -e "   - Xem log để biết AI có đang 'overloaded' hay không."
    echo -e "   - Nếu thấy lag, hãy Restart API (Mục 8)."
    echo ""
    read -p "Nhấn Enter để quay lại menu..."
}

function setup_vps() {
    echo -e "${YELLOW}=== [LOCKDOWN] THIẾT LẬP VPS TRẮNG (PROVISIONING - ELITE V2.2) ===${NC}"
    echo -e "${RED}[WARNING] Thao tác này sẽ thiết lập Tường lửa, Fail2Ban và cài đặt Docker/UV/PNPM.${NC}"
    echo -e "${CYAN}Thông số phát hiện: CPU Xeon 4-Cores | RAM 4GB | SSD 60GB${NC}"
    read -p "Sếp muốn tiến hành thiết lập VPS? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then return 1; fi

    # Phase 1: OS Update & Security
    echo -e "${CYAN}-> [1/6] Cập nhật OS & Cài đặt Bảo mật (UFW + Fail2Ban)...${NC}"
    sudo apt-get update -y && sudo apt-get upgrade -y
    sudo apt-get install -y ufw fail2ban unattended-upgrades curl git htop
    
    echo -e "${CYAN}-> Thiết lập Tường lửa (Chỉ mở 22, 80, 443)...${NC}"
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    echo "y" | sudo ufw enable

    # Phase 2: Performance Tuning (Swap + Limits)
    echo -e "${CYAN}-> [2/6] Tối ưu hiệu năng cho Xeon/4GB RAM (Alpha Performance Suite)...${NC}"
    # 2.1: Network Concurrency (TCP BBR for smooth AI streaming)
    if ! grep -q "bbr" /etc/sysctl.conf; then
        echo -e "${YELLOW}   ↳ Kích hoạt Google TCP BBR (Smooth Reaction)...${NC}"
        echo "net.core.default_qdisc=fq" | sudo tee -a /etc/sysctl.conf
        echo "net.ipv4.tcp_congestion_control=bbr" | sudo tee -a /etc/sysctl.conf
    fi

    # 2.2: Memory & Swap (R4GB Standard)
    # Swappiness=10: Ưu tiên RAM vật lý, chỉ lách sang Swap khi thực sự cần.
    # overcommit_memory=1: Đảm bảo Redis không bị crash do thiếu RAM ảo.
    echo -e "${YELLOW}   ↳ Thiết lập RAM Priority (Swappiness=10)...${NC}"
    echo "vm.swappiness=10" | sudo tee -a /etc/sysctl.conf
    echo "vm.overcommit_memory=1" | sudo tee -a /etc/sysctl.conf
    
    sudo sysctl -p

    # 2.3: Adaptive Swap 4GB
    if [ ! -f /swapfile ] && [ "$(free -m | grep Swap | awk '{print $2}')" -lt 1000 ]; then
        echo -e "${YELLOW}   ↳ Khởi tạo 4GB RAM Ảo (Emergency Safety Net)...${NC}"
        sudo fallocate -l 4G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    # 2.4: SSD TRIM (Health Protection)
    echo -e "${YELLOW}   ↳ Kích hoạt SSD Maintenance (fstrim.timer)...${NC}"
    sudo systemctl enable fstrim.timer || true
    sudo systemctl start fstrim.timer || true

    # 2.5: Elite Maintenance Cron (Automated Cleaning)
    echo -e "${CYAN}-> [2.5] Thiết lập Cron tự động bảo trì (4:00 AM)...${NC}"
    (crontab -l 2>/dev/null | grep -v "docker system prune"; echo "0 4 * * * /usr/bin/docker system prune -af --volumes --filter 'until=24h' > /dev/null 2>&1") | crontab -
    (crontab -l 2>/dev/null | grep -v "fstrim"; echo "0 5 * * * /usr/bin/fstrim -v / > /dev/null 2>&1") | crontab -
    echo -e "${GREEN}   ✔ Đã cài đặt lịch dọn dẹp Docker & Trim SSD hàng ngày.${NC}"

    echo -e "${CYAN}-> Tăng giới hạn File Descriptors (uLimit 65535)...${NC}"
    if ! grep -q "65535" /etc/security/limits.conf; then
        echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
        echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf
    fi

    # Phase 3: Docker Elite (Latest Engine)
    echo -e "${CYAN}-> [3/6] Cài đặt Docker Elite (Engine + Compose Plugin)...${NC}"
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER || true
    fi
    sudo apt-get install -y docker-compose-plugin

    # Phase 4: Binary Injection (UV + PNPM)
    echo -e "${CYAN}-> [4/6] Cài đặt Đồ nghề Build (UV 3.14 + Node 22 PNPM)...${NC}"
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    if ! command -v pnpm &> /dev/null; then
        sudo apt-get install -y nodejs npm
        sudo npm install -g pnpm
    fi

    # Phase 5: Final Lockdown check
    echo -e "${CYAN}-> [5/6] Kích hoạt Pháo đài tuần tra...${NC}"
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    echo -e "${GREEN}[SUCCESS] VPS đã được khóa bảo vệ và sẵn sàng chạy Mục 3 (FULL INIT)!${NC}"
    echo -e "${YELLOW}[TIP] Sếp hãy Logout và Login lại để quyền truy cập Docker có hiệu lực.${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}





function migrate_tenant_id() {
    echo -e "${CYAN}[TENANT] Đang khởi động quy trình di cư dữ liệu (Domain Migration)...${NC}"
    echo -e "${YELLOW}-> Mục tiêu: Đồng bộ dữ liệu cũ sang domain hiện tại trong .env${NC}"
    
    # Kiểm tra Container API có đang chạy không
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        docker exec -t fast_platform_api /opt/venv/bin/python3 -m backend.scripts.tenant_migration
    else
        echo -e "${YELLOW}[INFO] Container API chưa chạy. Khởi động môi trường tạm thời...${NC}"
        docker compose run --rm api /opt/venv/bin/python3 -m backend.scripts.tenant_migration
    fi
    
    echo -e "${GREEN}[OK] Đã hoàn tất quy trình di cư dữ liệu Tenant.${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function purge_full_database() {
    echo -e "${RED}[PURGE] GIAO THỨC LÀM SẠCH DATABASE (ELITE V2.2) !!!${NC}"
    echo -e "${YELLOW}[INFO] Sếp có thể chọn làm sạch toàn bộ hoặc chỉ các bảng cụ thể.${NC}"
    echo -e "${YELLOW}Cấu trúc (Schema) sẽ được giữ lại, nhưng dữ liệu trong bảng được chọn sẽ mất sạch.${NC}"
    
    # [SAFETY] Yêu cầu mật khẩu admin để xác thực trước khi show danh sách bảng
    read -s -p "Nhập mã quản trị để xác nhận (Admin Password): " confirm_pass
    echo ""
    
    if docker exec -i fast_platform_api /opt/venv/bin/python3 -m backend.scripts.verify_admin "$confirm_pass" | grep -q "MATCH"; then
        echo -e "${CYAN}-> Xác thực thành công. Đang tải danh sách bảng...${NC}"
        # Chạy script làm sạch (Sử dụng -it để tương tác chọn bảng)
        if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
            docker exec -it fast_platform_api /opt/venv/bin/python3 -m backend.scripts.clean_database
        else
            echo -e "${YELLOW}[INFO] Container API chưa chạy. Khởi động môi trường tạm thời...${NC}"
            docker compose run --rm api /opt/venv/bin/python3 -m backend.scripts.clean_database
        fi
        
        # [ELITE V2.2] Chỉ dọn Redis nếu Sếp dọn triệt để (hoặc nhắc Sếp tự dọn)
        echo -e "${CYAN}-> Gợi ý: Sếp nên Restart API (Mục 8) sau khi làm sạch DB để làm mới cache.${NC}"
        
        echo -e "${GREEN}[OK] Đã hoàn tất quy trình xử lý Database.${NC}"
    else
        echo -e "${RED}[ERROR] Sai mật mã quản trị! Thao tác bị từ chối.${NC}"
    fi
    read -p "Nhấn Enter để quay lại menu..."
}

function reset_db_for_marketing() {
    echo -e "${RED}[RESET] GIAO THỨC RESET DATABASE TIẾP THỊ (MARKETING RESET) !!!${NC}"
    echo -e "${YELLOW}[WARNING] Thao tác này sẽ xóa sạch dữ liệu đơn hàng, điểm loyalty, logs CTV và các tài khoản khách hàng thử nghiệm.${NC}"
    echo -e "${YELLOW}Chỉ tài khoản admin duy nhất (mlap) và dữ liệu sản phẩm, phân loại, bài viết, cấu hình, vouchers,... được giữ lại.${NC}"
    
    read -s -p "Nhập mã quản trị để xác nhận (Admin Password): " confirm_pass
    echo ""
    
    if docker exec -i fast_platform_api /opt/venv/bin/python3 -m backend.scripts.verify_admin "$confirm_pass" | grep -q "MATCH"; then
        echo -e "${CYAN}-> Xác thực thành công. Bắt đầu thực thi script reset...${NC}"
        if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
            docker exec -it fast_platform_api /opt/venv/bin/python3 backend/scripts/reset_db_marketing.py
        else
            echo -e "${YELLOW}[INFO] Container API chưa chạy. Khởi động môi trường tạm thời...${NC}"
            docker compose run --rm api /opt/venv/bin/python3 backend/scripts/reset_db_marketing.py
        fi
        
        echo -e "${CYAN}-> Đồng bộ lại liên kết hình ảnh (Media Sync)...${NC}"
        if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
            docker exec -t fast_platform_api /opt/venv/bin/python3 backend/scripts/sync_all_media.py
        else
            docker compose run --rm api /opt/venv/bin/python3 backend/scripts/sync_all_media.py
        fi
        
        echo -e "${CYAN}-> Làm sạch bộ nhớ đệm (Redis)...${NC}"
        if docker ps --format '{{.Names}}' | grep -q "fast_platform_redis"; then
            if [ -n "$REDIS_PASS" ]; then
                docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "xohi:chat:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
                docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" --scan --pattern "xohi:ctx:*" | xargs -r docker exec fast_platform_redis redis-cli -a "$REDIS_PASS" del || true
            else
                docker exec fast_platform_redis redis-cli --scan --pattern "xohi:chat:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
                docker exec fast_platform_redis redis-cli --scan --pattern "xohi:ctx:*" | xargs -r docker exec fast_platform_redis redis-cli del || true
            fi
        fi
        
        echo -e "${GREEN}[OK] Đã hoàn tất quy trình reset database phục vụ Marketing.${NC}"
    else
        echo -e "${RED}[ERROR] Sai mật mã quản trị! Thao tác bị từ chối.${NC}"
    fi
    read -p "Nhấn Enter để quay lại menu..."
}

function optimize_database() {
    echo -e "${CYAN}=== [OPTIMIZE] TỐI ƯU & CHỐNG PHÂN MẢNH DATABASE ZERO-LOCKING (POSTGRESQL) ===${NC}"
    echo -e "${YELLOW}-> Khởi động quy trình tối ưu hóa không gây khóa (Zero-Locking)...${NC}"
    
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        docker exec -t fast_platform_api /opt/venv/bin/python3 backend/scripts/optimize_db_concurrently.py
    else
        echo -e "${YELLOW}[INFO] Container API chưa chạy. Khởi động môi trường tạm thời...${NC}"
        docker compose run --rm api /opt/venv/bin/python3 backend/scripts/optimize_db_concurrently.py
    fi
    
    read -p "Nhấn Enter để quay lại menu..."
}

function deploy_security_index() {
    echo -e "${YELLOW}=== [SECURITY] DEPLOY GIN INDEX (POSTGRESQL PRODUCTION) ===${NC}"
    echo -e "${RED}[IMPORTANT] Thao tác này nên chạy vào GIỜ THẤP TẢI để đảm bảo hiệu năng tốt nhất.${NC}"
    echo -e "${CYAN}Ghi chú: Script dùng 'CONCURRENTLY' nên sẽ không gây lock table orders.${NC}"
    
    local SQL_FILE="backend/database/migrations/security_gin_index.sql"
    
    if [ ! -f "$SQL_FILE" ]; then
        echo -e "${RED}[ERROR] Không tìm thấy file $SQL_FILE${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    # Kiểm tra Container DB có đang chạy không
    if ! docker ps --format '{{.Names}}' | grep -q "fast_platform_db"; then
        echo -e "${RED}[ERROR] Container fast_platform_db không chạy. Hãy khởi động hệ thống trước.${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    echo -e "${CYAN}-> Đang thực thi GIN Index Migration...${NC}"
    # Đọc file SQL và pipe vào psql trong container
    if cat "$SQL_FILE" | docker exec -i fast_platform_db psql -U postgres -d fast_platform; then
        echo -e "${GREEN}[SUCCESS] Đã khởi tạo GIN Index thành công!${NC}"
    else
        echo -e "${RED}[ERROR] Thực thi SQL thất bại. Kiểm tra log của Database.${NC}"
    fi
    
    read -p "Nhấn Enter để quay lại menu..."
}

function upgrade_python_packages() {
    local NO_WAIT=false
    if [[ "$1" == "--no-wait" ]]; then
        NO_WAIT=true
    fi

    echo -e "${CYAN}[UPGRADE] Đang khởi động quy trình nâng cấp gói thư viện Python (Elite V2.2)...${NC}"
    
    # 1. Update lockfile
    if [ ! -f /.dockerenv ]; then
        echo -e "${YELLOW}-> Đang chạy uv lock --upgrade...${NC}"
        uv lock --upgrade
    fi

    # 2. Check if container fast_platform_api is running
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        echo -e "${YELLOW}-> [1/3] Đang cập nhật gói bên trong container fast_platform_api...${NC}"
        if docker exec -i fast_platform_api uv sync --no-dev; then
            echo -e "${GREEN}   ✔ Đã cập nhật thành công các gói trong container!${NC}"
        else
            echo -e "${RED}[ERROR] Cập nhật gói trong container thất bại.${NC}"
            if [ "$NO_WAIT" = false ]; then
                read -p "Nhấn Enter để quay lại..."
            fi
            return 1
        fi
    fi

    # 3. Sync local environment lock if local venv exists
    if [ -d ".venv" ]; then
        echo -e "${YELLOW}-> [2/3] Đang đồng bộ hóa môi trường ảo cục bộ (.venv)...${NC}"
        uv sync
    fi

    # 4. Restart containers to apply
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        echo -e "${YELLOW}-> [3/3] Đang khởi động lại dịch vụ api + worker_high để áp dụng...${NC}"
        docker compose restart api worker_high
    fi

    echo -e "${GREEN}[SUCCESS] Đã nâng cấp và áp dụng toàn bộ các gói thư viện mới thành công!${NC}"
    if [ "$NO_WAIT" = false ]; then
        read -p "Nhấn Enter để quay lại menu..."
    fi
}

function update_storefront_ssr() {
    echo -e "${CYAN}[SYSTEM] ĐANG CẬP NHẬT STOREFRONT SVELTEKIT SSR (HOST BUILD & CONTAINER RESTART)...${NC}"
    
    if [ ! -d "frontend" ]; then
        echo -e "${RED}[ERROR] Thư mục frontend không tồn tại.${NC}"
        read -p "Nhấn Enter để quay lại menu..."
        return
    fi
    
    echo -e "${YELLOW}-> 1. Đang build SvelteKit trên Host...${NC}"
    cd frontend
    rm -rf .svelte-kit build
    if [ ! -d "node_modules/vite" ]; then
        echo -e "${YELLOW}-> Không tìm thấy thư viện Vite trên Host, đang tiến hành cài đặt (pnpm install)...${NC}"
        pnpm install
    fi
    if pnpm build; then
        echo -e "${GREEN}✔ Build SvelteKit thành công!${NC}"
    else
        echo -e "${RED}[ERROR] Build SvelteKit thất bại.${NC}"
        cd ..
        read -p "Nhấn Enter để quay lại menu..."
        return
    fi
    cd ..
    
    echo -e "${YELLOW}-> 2. Đang build lại Docker Image cho UI...${NC}"
    docker compose build ui
    
    # [CLEANUP] Giải phóng ngay Build Cache của Docker để không bị phình ổ đĩa sau khi build
    echo -e "${YELLOW}-> [Docker] Đang giải phóng bộ nhớ đệm Build Cache...${NC}"
    docker builder prune -a -f &>/dev/null || true
    docker image prune -f &>/dev/null || true
    
    echo -e "${YELLOW}-> 3. Đang khởi động lại UI Container...${NC}"
    docker compose stop ui
    docker compose rm -f ui
    docker compose up -d ui

    echo -e "${YELLOW}-> 4. Đang xóa Caddy Cache (SEO/HTML cũ)...${NC}"
    flush_caddy_cache
    
    echo -e "${GREEN}✔ Cập nhật Storefront SSR hoàn tất! UI Container đã chạy bản mới nhất.${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}


function total_garbage_clean() {
    local NO_WAIT=false
    if [[ "$1" == "--no-wait" ]]; then
        NO_WAIT=true
    fi

    echo -e "${CYAN}[CLEAN] Đang tiến hành dọn rác toàn diện (Cache, Logs & Old Packages)...${NC}"

    # 1. Truncate Docker logs
    echo -e "${YELLOW}-> [1/6] Đang giải phóng bộ nhớ logs Docker...${NC}"
    if docker run --rm -v /var/lib/docker/containers:/var/lib/docker/containers alpine sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log' 2>/dev/null; then
        echo -e "${GREEN}   ✔ Đã làm sạch toàn bộ tệp tin logs Docker (qua container helper)!${NC}"
    else
        if sudo sh -c 'truncate -s 0 /var/lib/docker/containers/*/*-json.log' 2>/dev/null; then
            echo -e "${GREEN}   ✔ Đã làm sạch toàn bộ tệp tin logs Docker!${NC}"
        else
            echo -e "${YELLOW}[INFO] Không tìm thấy tệp logs hoặc thiếu quyền thực thi.${NC}"
        fi
    fi

    # 2. Clean UV cache inside container
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        echo -e "${YELLOW}-> [2/6] Đang xóa bộ nhớ đệm UV Cache trong container...${NC}"
        docker exec -i fast_platform_api uv cache clean 2>/dev/null || true
        echo -e "${GREEN}   ✔ Đã xóa sạch UV Cache inside container!${NC}"
    fi

    # 3. Clean local host UV cache
    if command -v uv &> /dev/null; then
        echo -e "${YELLOW}-> [3/6] Đang xóa bộ nhớ đệm UV Cache cục bộ...${NC}"
        uv cache clean 2>/dev/null || true
    fi

    # 4. Prune unused Docker builds & caches
    echo -e "${YELLOW}-> [4/6] Đang dọn dẹp Docker rác (Dangling images, build caches, networks)...${NC}"
    docker system prune -af 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
    docker builder prune -a -f 2>/dev/null || true
    echo -e "${GREEN}   ✔ Đã giải phóng toàn bộ tài nguyên Docker dư thừa!${NC}"

    # 5. Clean local system temp logs, pycache & dev caches
    echo -e "${YELLOW}-> [5/7] Đang làm sạch logs, pycache & dev caches trên Host...${NC}"
    rm -f "$PROJECT_DIR"/backend/cache/*.log 2>/dev/null || true
    find "$PROJECT_DIR" -type f -name "*.log" -delete 2>/dev/null || true
    find backend -type f -name "*.pyc" -delete 2>/dev/null || true
    find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    rm -rf frontend/node_modules frontend/build frontend/.svelte-kit frontend/.vite frontend/dist 2>/dev/null || true
    echo -e "${GREEN}   ✔ Đã làm sạch logs, pycache, node_modules và build folders trên Host!${NC}"

    # 6. Clean npm & pnpm global caches on Host
    echo -e "${YELLOW}-> [6/7] Đang làm sạch npm cache, pnpm store & hệ thống (apt, journal)...${NC}"
    if command -v npm &> /dev/null; then
        npm cache clean --force &>/dev/null || true
    fi
    if command -v pnpm &> /dev/null; then
        pnpm store prune &>/dev/null || true
        rm -rf ~/.cache/pnpm 2>/dev/null || true
        rm -rf ~/.local/share/pnpm 2>/dev/null || true
    fi
    sudo apt-get clean &>/dev/null || true
    sudo journalctl --vacuum-time=3d &>/dev/null || true
    echo -e "${GREEN}   ✔ Đã dọn dẹp sạch sẽ npm, pnpm, apt cache và system journals!${NC}"

    # 7. Flush Caddy Cache (SEO/HTML stale content)
    echo -e "${YELLOW}-> [7/8] Đang xóa Caddy Cache (SEO/HTML cũ)...${NC}"
    flush_caddy_cache

    # 8. Flush Redis & Force Client Reset Cache
    echo -e "${YELLOW}-> [8/8] Đang xóa toàn bộ Redis Cache & Ép client reset cache...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_redis"; then
        local redis_pass=""
        if [ -f .env ]; then
            redis_pass=$(grep -E "^REDIS_PASSWORD=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'" | tr -d '\r')
        fi
        if [ -n "$redis_pass" ]; then
            docker exec fast_platform_redis redis-cli -a "$redis_pass" FLUSHALL_SECURE_2026 2>/dev/null || \
            docker exec fast_platform_redis redis-cli -a "$redis_pass" flushall 2>/dev/null || \
            docker exec fast_platform_redis redis-cli flushall || true
        else
            docker exec fast_platform_redis redis-cli FLUSHALL_SECURE_2026 2>/dev/null || \
            docker exec fast_platform_redis redis-cli flushall || true
        fi
    fi
    if docker ps --format '{{.Names}}' | grep -q "fast_platform_api"; then
        docker exec fast_platform_api /opt/venv/bin/python3 -c "import asyncio; from backend.services.event_bus import event_bus; asyncio.run(event_bus.emit('SYSTEM_SIGNAL', {'action': 'FORCE_RELOAD'}))" 2>/dev/null || true
    fi

    echo -e "${GREEN}[SUCCESS] Đã hoàn tất dọn dẹp hệ thống siêu sạch và ép reset client!${NC}"
    df -h /

    # Check for bloated Docker images (greater than 4GB)
    echo -e "${CYAN}-> Đang kiểm tra Docker Images phình to...${NC}"
    local bloated_images=$(docker images --format "{{.Repository}}:{{.Tag}} ({{.Size}})" | grep -E "\((([4-9]|[1-9][0-9])(\.[0-9]+)?GB)\)" || true)
    if [ -n "$bloated_images" ]; then
        echo -e "\n${RED}[WARNING] Phát hiện các Docker Image sau đang chiếm dung lượng rất lớn (>4GB):${NC}"
        echo -e "${RED}$bloated_images${NC}"
        echo -e "${YELLOW}[GỢI Ý] Nguyên nhân thường do bản build cũ copy nhầm thư mục rác (node_modules, .venv) trên Host.${NC}"
        echo -e "${YELLOW}Để giải phóng 4GB - 5GB dung lượng này mà không ảnh hưởng tới Database, Sếp hãy chạy lệnh:${NC}"
        echo -e "${GREEN}       docker compose build api worker_high && docker image prune -f${NC}\n"
    fi
    
    view_logs
    
    if [ "$NO_WAIT" = false ]; then
        read -p "Nhấn Enter để quay lại menu..."
    fi
}

function restart_backend_services() {
    local NO_WAIT=false
    if [[ "$1" == "--no-wait" ]]; then
        NO_WAIT=true
    fi

    echo -e "${CYAN}[RESTART] Đang làm sạch Log và khởi động lại Backend, UI & Gateway (api + worker_high + ui + caddy)...${NC}"
    docker compose stop api worker_high ui caddy
    docker compose rm -f api worker_high ui caddy
    
    # [Elite V2.2] Purge pycache cũ trực tiếp trên host trước khi up (tránh Double Restart làm treo lock DB)
    echo -e "${YELLOW}[PYCACHE] Đang xóa sạch pycache cũ trên Host...${NC}"
    find backend -name "*.pyc" -delete 2>/dev/null || true
    find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    docker compose up -d api worker_high ui caddy
    echo -e "${GREEN}[OK] Đã khởi động lại Hệ thống (API, Worker High, UI, Caddy) sạch sẽ!${NC}"
    echo -e "${CYAN}--- Trạng thái hoạt động mới nhất ---${NC}"
    docker compose logs --tail 15 api worker_high ui
    echo -e "${GREEN}✔ Khởi chạy hoàn tất! Hệ thống đã trực tuyến ổn định.${NC}"
    
    if [ "$NO_WAIT" = false ]; then
        read -p "Nhấn Enter để quay lại menu..."
    fi
}

# Handle direct command-line arguments (e.g. ./xohi.sh clean)
if [[ -n "$1" ]]; then
    case "$1" in
        clean|dondep|dọn_dẹp|dondep_docker|dondep-docker)
            total_garbage_clean --no-wait
            exit 0
            ;;
        reset|restart|8)
            restart_backend_services --no-wait
            exit 0
            ;;
        ui-ssr|ssr-update|update-ui|ui|dist-ro|caddy-ro|update-ro|ro)
            update_storefront_ssr
            exit 0
            ;;
        caddy-cache|flush-cache|clear-cache)
            flush_caddy_cache
            exit 0
            ;;
        reset-marketing|marketing-reset|23)
            reset_db_for_marketing
            exit 0
            ;;
        optimize-db|db-optimize|24)
            optimize_database
            exit 0
            ;;
        upgrade|upgrade-python|20)
            upgrade_python_packages --no-wait
            exit 0
            ;;
    esac
fi

while true; do
    clear
    echo -e "${CYAN}"
    echo "------------------------------------------------"
    echo "   XOHI OS - COMMANDER v3.2 (TENANT SYNC)       "
    echo "------------------------------------------------"
    echo -e "${NC}"

    echo -e "${YELLOW}>>> LÊNH TỔNG LỰC:${NC}"
    echo "1) LÀM SẠCH CODE (Xóa Cache, Node_modules, Python Venv)"
    echo "2) BẢO TRÌ DOCKER (Làm sạch 100% + Cập nhật Engine)"
    echo "2a) DỌN DẸP DOCKER RÁC (Chỉ giữ container & image đang chạy)"
    echo "3) FULL INIT (Dọn + Build + Migration + Seed + SSL)"
    echo "3.1) INITIALIZE (Bản 3.1: Dọn + Build + Migration + SSL - Trống DB)"
    echo ""
    echo -e "${CYAN}>>> CÔNG CỤ HỖ TRỢ:${NC}"
    echo "4) XEM LOG BACKEND"
    echo "5) SAO LƯU DỮ LIỆU (DB + Images)"
    echo "6) KHÔI PHỤC DỮ LIỆU"
    echo "7) DỌN DẸP BẢN SAO LƯU (Xóa sạch)"
    echo "8) RESTART API (Kèm theo dõi Log lỗi)"
    echo "9) CẬP NHẬT MODEL AI (~250MB)"
    echo "10) CẤP SSL (HTTPS) - FULL 3 DOMAINS"
    echo "11) CÀI ĐẶT VPS (LOCKDOWN - Dành cho máy mới)"
    echo "12) QUẢN TRỊ USER & SSH (Lockdown Root)"
    echo "13) HƯỚNG DẪN CHI TIẾT (Tránh Quên)"
    echo "14) KHỞI TẠO SIÊU ADMIN (Login cho DB Trắng)"
    echo "15) LÀM SẠCH DỮ LIỆU HELEN (Purge Logs & Memory)"
    echo "16) ROTATE ENCRYPTION SALT (Vô hiệu hóa toàn bộ session)"
    echo "17) DI CƯ TENANT (Đổi Domain -> Update DB)"
    echo "18) LÀM SẠCH DATABASE (Dọn sạch toàn bộ Table)"
    echo "19) DEPLOY GIN INDEX (PostgreSQL Security Index)"
    echo "20) NÂNG CẤP GÓI THƯ VIỆN PYTHON (Upgrade Dependencies)"
    echo "21) DỌN RÁC TOÀN DIỆN (Clean Cache, Logs & Old Packages)"
    echo "22) CẬP NHẬT STOREFRONT SSR (Build SvelteKit & Restart UI)"
    echo "23) RESET DATABASE MARKETING (Khởi tạo lại dữ liệu khách hàng/CTV)"
    echo "24) TỐI ƯU & CHỐNG PHÂN MẢNH DB (Tăng tốc truy vấn)"
    echo "0) Thoát (Exit)"
    echo ""
    read -p "Sếp chọn lệnh nào: " choice

    case $choice in
        1)
            deep_clean
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        2)
            update_docker
            ;;
        2a|2A)
            prune_docker_garbage
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        3)
            init_deploy
            ;;
        3.1)
            init_deploy --no-seed
            ;;
        4)
            view_logs
            ;;
        5)
            backup_data
            ;;
        6)
            restore_data
            ;;
        7)
            clean_backups
            ;;
        8)
            restart_backend_services
            ;;
        9)
            update_ai_model
            ;;
        10)
            echo -e "${CYAN}[SSL] Đang khởi động quy trình cấp và tin cậy SSL (HTTPS)...${NC}"
            chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
            echo -e "${YELLOW}[INFO] Đang rebuild Caddy để áp dụng chứng chỉ mới...${NC}"
            docker compose up -d --build caddy
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        11)
            setup_vps
            ;;
        12)
            manage_security_users
            ;;
        13)
            show_elite_guide
            ;;
        14)
            create_superuser
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        15)
            purge_helen_data
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        16)
            rotate_encryption_key
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        17)
            migrate_tenant_id
            ;;
        18)
            purge_full_database
            ;;
        19)
            deploy_security_index
            ;;
        20)
            upgrade_python_packages
            ;;
        21)
            total_garbage_clean
            ;;
        22)
            update_storefront_ssr
            ;;
        23)
            reset_db_for_marketing
            ;;
        24)
            optimize_database
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
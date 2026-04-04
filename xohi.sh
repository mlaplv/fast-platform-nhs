#!/usr/bin/env bash
export PYTHONPATH="${PWD}"

# XOHI OS - PROJECT MANAGEMENT COMMANDER v3.0 (Lean Monorepo)
# Optimized for UV (Backend) & Vite/NPM (Frontend)
# No PNPM, No Turbo.

set -e
set -o pipefail


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
    echo -e "${YELLOW}-> [5/6] Đang xóa Lock files, Logs, .DS_Store...${NC}"
    sudo rm -f uv.lock vad.slice kehoach.txt
    sudo find . -maxdepth 3 -type f \( -name "pnpm-lock.yaml" -o -name "package-lock.json" -o -name "yarn.lock" -o -name "*.log" -o -name ".DS_Store" \) -delete 2>/dev/null || true

    # === ORPHAN EMPTY DIRS ===
    echo -e "${YELLOW}-> [6/6] Đang xóa thư mục rỗng...${NC}"
    sudo rm -rf static
    sudo find . -maxdepth 3 -type d -empty -not -path './.git/*' -not -path './certs/*' -delete 2>/dev/null || true

    echo -e "${GREEN}[OK] Đã dọn dẹp hệ thống sạch bóng!${NC}"
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





function init_deploy() {
    # [ELITE V2.2] Bảo trì hệ thống trước khi khởi tạo dự án
    update_docker --no-wait || return 1
    
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
        uv venv --python 3.13 && source .venv/bin/activate
        uv pip install -e . || true
    else
        echo -e "${CYAN}-> Đang tạo môi trường ảo (Python 3.13)...${NC}"
        # [CTO ELITE] Vượt rào mạng tuyệt đối bằng Mirror Aliyun
        export UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
        export PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple/"
        
        uv venv --seed --python 3.13
        source .venv/bin/activate
        echo -e "${CYAN}-> Đang cài đặt Core Dependencies (Mirror Mode)...${NC}"
        ./.venv/bin/pip install --upgrade pip
        ./.venv/bin/pip install litellm==1.40.0 --index-url "$PIP_INDEX_URL"
        uv pip install litestar[standard] advanced-alchemy asyncpg pydantic-ai
        # Sau đó cài nốt các thằng còn lại
        uv pip install -e .
    fi
    echo -e "${CYAN}-> [CTO ELITE] Đang tạo uv.lock cho Docker...${NC}"
    uv lock || true
    (cd frontend && pnpm install)
    
    echo -e "${CYAN}[4/6] Xây dựng và khởi động Cơ sở hạ tầng (Database & Cache)...${NC}"
    # [CTO ELITE] Build tuần tự để bảo vệ RAM tuyệt đối
    docker compose build db
    docker compose build redis
    docker compose build caddy
    docker compose up -d db redis caddy
    
    echo -e "${CYAN}[5/6] Database Migration & SSL Setup...${NC}"
    echo -e "${YELLOW}Đang chờ DB sẵn sàng...${NC}"
    # Đợi DB khởi khởi động hoàn toàn
    sleep 5
    echo -e "${YELLOW}Đang chạy Migration (Một lần)...${NC}"
    # [CTO ELITE] Chạy migration như một container tạm, tránh chiếm RAM lâu dài
    docker compose run --rm api /opt/venv/bin/alembic -c backend/alembic.ini upgrade head
    
    echo -e "${CYAN}[6/6] Khởi tạo dữ liệu (Data Injection)...${NC}"
    echo -e "Sếp muốn làm gì với Database?"
    echo "1) Cháy Seed DB Test (Dữ liệu mẫu)"
    echo "2) Khôi phục từ bản sao lưu (Restore Backup)"
    echo "3) Bỏ qua (Giữ DB trắng)"
    read -p "Lựa chọn của Sếp: " db_choice
    
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
            ;;
    esac
    
    echo -e "${YELLOW}Đang khởi động toàn bộ dịch vụ (API, Worker & UI)...${NC}"
    docker compose build api
    docker compose build worker
    docker compose build ui
    # [CTO ELITE] SKIP_MIGRATE=true vì đã chạy migrate tuần tự ở bước [5/6] rồi
    SKIP_MIGRATE=true docker compose up -d api worker ui
    chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
    
    echo -e "${GREEN}=== HỆ THỐNG ĐÃ SẴN SÀNG! (Đã tối ưu RAM) ===${NC}"
    echo -e "${CYAN}Truy cập: https://admin.smartshop.test${NC}"
    
    # [CTO ELITE] Tự động chuyển sang xem log để Sếp theo dõi WARNING/ERROR
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





function view_logs() {
    echo -e "${CYAN}[LOGS] Đang kiểm tra tín hiệu Backend (api + worker)...${NC}"
    echo -e "${YELLOW}Nhấn Ctrl+C để quay lại menu.${NC}"
    # Hiện 10 dòng cuối bất kể loại log để Sếp biết hệ thống vẫn chạy
    docker compose logs --tail 10 api worker
    echo -e "${YELLOW}--- Đang theo dõi lỗi mới (ERROR/CRITICAL/WARNING) ---${NC}"
    docker compose logs -f api worker --tail 100 --since 5m --no-log-prefix | grep -Ei --line-buffered "ERROR|CRITICAL|EXCEPTION|WARNING"
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
    docker compose restart api ui redis
    
    echo -e "${GREEN}[SUCCESS] Đã khôi phục dữ liệu hoàn tất!${NC}"
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

function setup_vps() {
    echo -e "${YELLOW}=== [LOCKDOWN] THIẾT LẬP VPS TRẮNG (PROVISIONING - ELITE V2.2) ===${NC}"
    echo -e "${RED}[WARNING] Thao tác này sẽ thiết lập Tường lửa, Fail2Ban và cài đặt Docker/UV/PNPM.${NC}"
    echo -e "${CYAN}Thông số phát hiện: CPU Xeon 4-Cores | RAM 4GB | SSD 60GB + SAS 120GB${NC}"
    read -p "Sếp muốn tiến hành thiết lập VPS? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then return 1; fi

    # Phase 1: OS Update & Security
    echo -e "${CYAN}-> [1/5] Cập nhật OS & Cài đặt Bảo mật (UFW + Fail2Ban)...${NC}"
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
    echo -e "${CYAN}-> [2/5] Tối ưu hiệu năng cho Xeon/4GB RAM (Alpha Performance Suite)...${NC}"
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

    echo -e "${CYAN}-> Tăng giới hạn File Descriptors (uLimit 65535)...${NC}"
    if ! grep -q "65535" /etc/security/limits.conf; then
        echo "* soft nofile 65535" | sudo tee -a /etc/security/limits.conf
        echo "* hard nofile 65535" | sudo tee -a /etc/security/limits.conf
    fi

    # Phase 3: Docker Elite (Latest Engine)
    echo -e "${CYAN}-> [3/5] Cài đặt Docker Elite (Engine + Compose Plugin)...${NC}"
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER || true
    fi
    sudo apt-get install -y docker-compose-plugin

    # Phase 4: Binary Injection (UV + PNPM)
    echo -e "${CYAN}-> [4/5] Cài đặt Đồ nghề Build (UV 3.13 + Node 22 PNPM)...${NC}"
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
    
    if ! command -v pnpm &> /dev/null; then
        sudo apt-get install -y nodejs npm
        sudo npm install -g pnpm
    fi

    # Phase 5: Final Lockdown check
    echo -e "${CYAN}-> [5/5] Kích hoạt Pháo đài tuần tra...${NC}"
    sudo systemctl enable fail2ban
    sudo systemctl restart fail2ban
    
    echo -e "${GREEN}[SUCCESS] VPS đã được khóa bảo vệ và sẵn sàng chạy Mục 3 (FULL INIT)!${NC}"
    echo -e "${YELLOW}[TIP] Sếp nên mount ổ SAS 120GB vào thư mục 'backups/' để lưu trữ lâu dài.${NC}"
    echo -e "${YELLOW}[TIP] Sếp hãy Logout và Login lại để quyền truy cập Docker có hiệu lực.${NC}"
    read -p "Nhấn Enter để quay lại menu..."
}

function mount_sas() {
    echo -e "${YELLOW}=== [STORAGE] MOUNT Ổ CỨNG SAS (120GB - ELITE V2.2) ===${NC}"
    echo -e "${RED}[SECURITY] Yêu cầu mã xác thực để tiếp tục...${NC}"
    read -s -p "Nhập mã khóa (Lockdown Key): " lockdown_key
    echo ""
    
    if [[ "$lockdown_key" != "ELITE_V22" ]]; then
        echo -e "${RED}[ERROR] Sai mã khóa! Thao tác bị từ chối để bảo vệ dữ liệu.${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    echo -e "${CYAN}Đang quét danh sách phân vùng khả dụng...${NC}"
    echo ""
    
    # Hiển thị danh sách ổ đĩa để sếp nhận diện
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE | grep -E "disk|part" | grep -v "loop"
    echo ""
    
    echo -e "${YELLOW}[TIP] Sếp tìm phân vùng khoảng 110G-120G (ví dụ: sda1).${NC}"
    echo -e "${RED}[WARNING] CẨN THẬN: Nhập sai có thể làm mất dữ liệu OS!${NC}"
    read -p "Nhập TÊN phân vùng Sếp chọn (ví dụ: sda1): " disk_name
    
    if [ -z "$disk_name" ]; then
        echo -e "${RED}[ERROR] Không có phân vùng nào được chọn.${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    DEVICE="/dev/$disk_name"
    if [ ! -b "$DEVICE" ]; then
        echo -e "${RED}[ERROR] Phân vùng $DEVICE không tồn tại.${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    # Kiểm tra xem phân vùng đã được mount chưa
    if grep -q "$DEVICE" /proc/mounts; then
        echo -e "${RED}[ERROR] Phân vùng $DEVICE đang được sử dụng ở nơi khác!${NC}"
        read -p "Nhấn Enter để quay lại..."
        return 1
    fi

    # Kiểm tra định dạng (FSTYPE)
    FSTYPE=$(lsblk -no FSTYPE "$DEVICE")
    if [ -z "$FSTYPE" ]; then
        echo -e "${RED}[WARNING] Phân vùng $DEVICE chưa có định dạng (Trắng).${NC}"
        read -p "Sếp muốn Format sang EXT4 (Xóa sạch dữ liệu)? (y/n): " confirm_format
        if [[ "$confirm_format" =~ ^[Yy]$ ]]; then
            echo -e "${CYAN}-> Đang định dạng $DEVICE sang EXT4...${NC}"
            sudo mkfs.ext4 "$DEVICE"
        else
            echo -e "${YELLOW}-> Đã hủy thao tác.${NC}"
            return 1
        fi
    fi

    # Tiến hành Mount vào thư mục backups/ của dự án
    BACKUP_PATH="$(pwd)/backups"
    echo -e "${CYAN}-> Đang tiến hành Mount $DEVICE vào $BACKUP_PATH...${NC}"
    mkdir -p "$BACKUP_PATH"
    sudo mount "$DEVICE" "$BACKUP_PATH"
    sudo chown -R $USER:$USER "$BACKUP_PATH"

    # Thiết lập Persistence (fstab) bằng UUID để tránh lỗi khi đổi tên thiết bị
    UUID=$(lsblk -no UUID "$DEVICE")
    if [ -n "$UUID" ]; then
        echo -e "${CYAN}-> Ghi danh vào hệ thống (fstab) bằng UUID: $UUID...${NC}"
        if ! grep -q "$UUID" /etc/fstab; then
            # Sử dụng nofail để VPS vẫn khởi động được nếu ổ cứng có vấn đề
            echo "UUID=$UUID  $BACKUP_PATH  ext4  defaults,nofail,user  0  2" | sudo tee -a /etc/fstab
        fi
    fi

    echo -e "${GREEN}[SUCCESS] Đã liên kết ổ SAS 120GB thành công vào: $BACKUP_PATH${NC}"
    df -h | grep backups
    read -p "Nhấn Enter để quay lại menu..."
}



while true; do
    clear
    echo -e "${CYAN}"
    echo "------------------------------------------------"
    echo "   XOHI OS - COMMANDER v4.0 (LOCKDOWN)          "
    echo "------------------------------------------------"
    echo -e "${NC}"

    echo -e "${YELLOW}>>> LÊNH TỔNG LỰC:${NC}"
    echo "1) LÀM SẠCH CODE (Xóa Cache, Node_modules, Python Venv)"
    echo "2) BẢO TRÌ DOCKER (Làm sạch 100% + Cập nhật Engine)"
    echo "3) FULL INIT (Dọn + Build + Migration + Seed + SSL)"
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
    echo "12) MOUNT Ổ SAS 120GB (Vào backups/)"
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
        3)
            init_deploy
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
            echo -e "${CYAN}[RESTART] Đang làm sạch Log và khởi động lại Backend (api + worker)...${NC}"
            docker compose stop api worker
            docker compose rm -f api worker
            docker compose up -d api worker
            echo -e "${GREEN}[OK] Đã khởi động lại API và Worker với Log sạch sẽ!${NC}"
            echo -e "${YELLOW}--- Đang theo dõi LỖI MỚI (ERROR/CRITICAL/WARNING) ---${NC}"
            echo -e "${YELLOW}Nhấn Ctrl+C để quay lại menu.${NC}"
            # Lọc log lỗi cho Sếp thấy thực trạng hệ thống
            docker compose logs -f api worker --tail 50 --no-log-prefix | grep -Ei --line-buffered "ERROR|CRITICAL|EXCEPTION|WARNING"
            ;;
        9)
            update_ai_model
            ;;
        10)
            echo -e "${CYAN}[SSL] Đang khởi động quy trình cấp and tin cậy SSL (HTTPS)...${NC}"
            chmod +x scripts/setup-ssl.sh && ./scripts/setup-ssl.sh
            read -p "Nhấn Enter để quay lại menu..."
            ;;
        11)
            setup_vps
            ;;
        12)
            mount_sas
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

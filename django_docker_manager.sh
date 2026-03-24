#!/bin/bash

# --- Cấu hình màu sắc cho terminal ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m' # Màu cho menu chính
CYAN='\033[0;36m'  # Màu cho menu phụ (Docker Compose)
MAGENTA='\033[0;35m' # Màu cho menu phụ (Django Project)
NC='\033[0m'      # Không màu

# --- Hàm kiểm tra Docker có hoạt động không ---
check_docker_status() {
    echo -e "${BLUE}Đang kiểm tra trạng thái Docker...${NC}"
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Lỗi: Docker không được cài đặt. Vui lòng cài đặt Docker trước khi chạy script này.${NC}"
        exit 1
    fi

    # Kiểm tra trạng thái của Docker daemon
    if ! sudo systemctl is-active --quiet docker 2>/dev/null; then
        echo -e "${YELLOW}Cảnh báo: Dịch vụ Docker không chạy. Đang cố gắng khởi động...${NC}"
        
        # Kiểm tra xem có thể sử dụng sudo không
        if ! sudo -n true 2>/dev/null; then
            echo -e "${RED}Lỗi: Không thể sử dụng sudo không cần password.${NC}"
            echo -e "${YELLOW}Vui lòng chạy thủ công: sudo systemctl start docker${NC}"
            echo -e "${YELLOW}Hoặc cấu hình sudo không cần password cho user hiện tại.${NC}"
            exit 1
        fi
        
        sudo systemctl start docker 2>/dev/null
        if ! sudo systemctl is-active --quiet docker 2>/dev/null; then
            echo -e "${RED}Lỗi: Không thể khởi động dịch vụ Docker. Vui lòng kiểm tra cài đặt Docker.${NC}"
            echo -e "${YELLOW}Thử chạy thủ công: sudo systemctl start docker${NC}"
            exit 1
        fi
        echo -e "${GREEN}Dịch vụ Docker đã được khởi động.${NC}"
    else
        echo -e "${GREEN}Docker daemon đang chạy.${NC}"
    fi
    echo "---"
}

# --- Hàm thực hiện lệnh Docker và kiểm tra lỗi ---
execute_docker_command() {
    local cmd="$1"
    local message="$2"
    local force_flag="$3" # Tùy chọn: -f cho xóa bắt buộc không hỏi

    echo -e "${BLUE}${message}...${NC}"

    if [[ "$cmd" == "docker system prune" ]]; then
        echo -e "${BLUE}Đang kiểm tra không gian sẽ được giải phóng...${NC}"
        local dry_run_output=$(docker system prune -a --volumes --dry-run 2>&1)
        echo "$dry_run_output"
        local reclaimed_space=$(echo "$dry_run_output" | grep "Total reclaimed space:" | awk '{print $NF}')
        if [[ -z "$reclaimed_space" ]]; then
             reclaimed_space="0B"
        fi
        echo -e "${YELLOW}Ước tính sẽ giải phóng: ${reclaimed_space}${NC}"
        read -p "$(echo -e "${YELLOW}Bạn có chắc chắn muốn tiếp tục? (y/n): ${NC}")" -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Đã hủy lệnh.${NC}"
            echo "---"
            return 1 # Báo hiệu hủy bỏ
        fi
    fi

    # Thực hiện lệnh. Sử dụng eval để hỗ trợ các lệnh có pipe hoặc chuỗi phức tạp.
    # 2>&1 chuyển stderr sang stdout, || true để không dừng script nếu lệnh thất bại
    local output=$(eval "$cmd $force_flag 2>&1")
    local status=$?

    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}Hoàn thành.${NC}"
    else
        echo -e "${RED}Có lỗi xảy ra trong quá trình thực hiện lệnh:${NC}"
        echo -e "${RED}$output${NC}" # Hiển thị lỗi từ lệnh Docker
    fi
    echo "---"
    return "$status" # Trả về trạng thái thực của lệnh
}

# --- Hàm dọn dẹp Docker ---
clean_docker_components() {
    echo -e "${YELLOW}Bắt đầu làm sạch Docker HOÀN TOÀN...${NC}"
    echo "---------------------------"
    echo -e "${RED}CẢNH BÁO: Hành động này sẽ xóa SẠCH Docker như lúc mới cài đặt!${NC}"
    echo -e "${RED}Tất cả container, image, volume, network sẽ bị xóa vĩnh viễn!${NC}"
    echo "---------------------------"

    # Xác nhận từ người dùng
    read -p "$(echo -e "${RED}Bạn có CHẮC CHẮN muốn xóa sạch Docker hoàn toàn không? (gõ 'yyes' để xác nhận): ${NC}")" confirm
    if [[ "$confirm" != "yyes" ]]; then
        echo -e "${YELLOW}Đã hủy thao tác. Docker không bị thay đổi.${NC}"
        return 1
    fi

    echo -e "${BLUE}Đang thực hiện dọn dẹp Docker hoàn toàn...${NC}"

    # 1. Dừng tất cả container đang chạy
    echo -e "${BLUE}1. Dừng tất cả container...${NC}"
    docker stop $(docker ps -aq) 2>/dev/null || true

    # 2. Xóa tất cả container
    echo -e "${BLUE}2. Xóa tất cả container...${NC}"
    docker rm $(docker ps -aq) 2>/dev/null || true

    # 3. Xóa tất cả image
    echo -e "${BLUE}3. Xóa tất cả image...${NC}"
    docker rmi -f $(docker images -aq) 2>/dev/null || true

    # 4. Xóa tất cả volume
    echo -e "${BLUE}4. Xóa tất cả volume...${NC}"
    docker volume rm $(docker volume ls -q) 2>/dev/null || true

    # 5. Xóa tất cả network (trừ default)
    echo -e "${BLUE}5. Xóa tất cả network...${NC}"
    docker network rm $(docker network ls -q --filter "type=custom") 2>/dev/null || true

    # 6. Xóa tất cả build cache
    echo -e "${BLUE}6. Xóa build cache...${NC}"
    docker builder prune -af 2>/dev/null || true

    # 7. Dọn dẹp hệ thống hoàn toàn
    echo -e "${BLUE}7. Dọn dẹp hệ thống hoàn toàn...${NC}"
    docker system prune -af --volumes 2>/dev/null || true

    # 8. Xóa tất cả Docker Compose volumes và networks
    echo -e "${BLUE}8. Xóa Docker Compose volumes và networks...${NC}"
    docker volume prune -f 2>/dev/null || true
    docker network prune -f 2>/dev/null || true

    echo "---------------------------"
    echo -e "${GREEN}✅ Docker đã được xóa sạch hoàn toàn!${NC}"
    echo -e "${GREEN}✅ Docker hiện tại như lúc mới cài đặt!${NC}"
    echo -e "${BLUE}Để kiểm tra, chạy: docker ps -a, docker images, docker volume ls${NC}"
    echo "---------------------------"
    
    # Tự động cập nhật Docker sau khi dọn dẹp
    echo -e "${BLUE}Đang cập nhật Docker lên phiên bản mới nhất...${NC}"
    update_docker
}

# --- Hàm hiển thị trạng thái Docker ---
show_docker_info() {
    echo -e "${BLUE}--- Thông tin Docker ---${NC}"
    if docker info >/dev/null 2>&1; then
        docker info
        echo ""
        echo -e "${GREEN}✅ Docker daemon đang hoạt động bình thường${NC}"
    else
        echo -e "${RED}❌ Docker daemon không hoạt động hoặc có lỗi${NC}"
        echo -e "${YELLOW}Thử kiểm tra logs: sudo journalctl -u docker --no-pager -l${NC}"
    fi
    echo "---"
}

# --- Hàm liệt kê các container ---
list_containers() {
    echo -e "${BLUE}--- Danh sách Docker Containers (tất cả) ---${NC}"
    docker ps -a || echo -e "${RED}Không thể liệt kê container.${NC}"
    echo "---"
}

# --- Hàm liệt kê các image ---
list_images() {
    echo -e "${BLUE}--- Danh sách Docker Images ---${NC}"
    docker images || echo -e "${RED}Không thể liệt kê image.${NC}"
    echo "---"
}

# --- Hàm liệt kê các volume ---
list_volumes() {
    echo -e "${BLUE}--- Danh sách Docker Volumes ---${NC}"
    docker volume ls || echo -e "${RED}Không thể liệt kê volume.${NC}"
    echo "---"
}

# --- Hàm liệt kê các network ---
list_networks() {
    echo -e "${BLUE}--- Danh sách Docker Networks ---${NC}"
    docker network ls || echo -e "${RED}Không thể liệt kê network.${NC}"
    echo "---"
}

# --- Hàm khởi động lại Docker daemon ---
restart_docker_daemon() {
    echo -e "${BLUE}Đang khởi động lại Docker daemon...${NC}"
    
    # Kiểm tra xem có thể sử dụng sudo không
    if ! sudo -n true 2>/dev/null; then
        echo -e "${YELLOW}Cảnh báo: Không thể sử dụng sudo không cần password.${NC}"
        echo -e "${YELLOW}Docker daemon có thể cần được khởi động lại thủ công.${NC}"
        echo -e "${YELLOW}Chạy: sudo systemctl restart docker${NC}"
        echo "---"
        return 1
    fi
    
    # Reload systemd daemon trước khi restart Docker
    echo -e "${BLUE}Reloading systemd daemon...${NC}"
    sudo systemctl daemon-reload 2>/dev/null || {
        echo -e "${YELLOW}Cảnh báo: Không thể reload systemd daemon.${NC}"
    }
    
    # Restart Docker service
    sudo systemctl restart docker 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Đã khởi động lại Docker daemon thành công.${NC}"
        
        # Kiểm tra trạng thái Docker
        echo -e "${BLUE}Kiểm tra trạng thái Docker...${NC}"
        sleep 3
        if sudo systemctl is-active --quiet docker 2>/dev/null; then
            echo -e "${GREEN}Docker daemon đang chạy bình thường.${NC}"
        else
            echo -e "${RED}Cảnh báo: Docker daemon có thể chưa ổn định.${NC}"
        fi
    else
        echo -e "${RED}Lỗi: Không thể khởi động lại Docker daemon.${NC}"
        echo -e "${YELLOW}Vui lòng chạy thủ công: sudo systemctl restart docker${NC}"
    fi
    echo "---"
}

# --- Hàm kiểm tra và sửa lỗi Docker daemon ---
fix_docker_daemon() {
    echo -e "${YELLOW}Bắt đầu kiểm tra và sửa lỗi Docker daemon...${NC}"
    echo "---------------------------"
    
    # Kiểm tra trạng thái Docker daemon
    if ! sudo systemctl is-active --quiet docker; then
        echo -e "${RED}Docker daemon không chạy. Đang khởi động...${NC}"
        sudo systemctl start docker
        sleep 3
    fi
    
    # Kiểm tra Docker daemon configuration
    echo -e "${BLUE}Kiểm tra Docker daemon configuration...${NC}"
    if [ -f /etc/docker/daemon.json ]; then
        echo -e "${GREEN}✅ Docker daemon.json tồn tại${NC}"
        echo -e "${BLUE}Nội dung daemon.json:${NC}"
        cat /etc/docker/daemon.json
    else
        echo -e "${YELLOW}⚠️  Docker daemon.json không tồn tại, tạo cấu hình mặc định...${NC}"
        sudo mkdir -p /etc/docker
        sudo tee /etc/docker/daemon.json > /dev/null <<'EOF'
{
  "exec-opts": ["native.cgroupdriver=systemd"],
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" },
  "storage-driver": "overlay2",
  "live-restore": true
}
EOF
        echo -e "${GREEN}✅ Đã tạo daemon.json mặc định${NC}"
    fi
    
    # Reload systemd và restart Docker
    echo -e "${BLUE}Reloading systemd daemon...${NC}"
    sudo systemctl daemon-reload
    
    echo -e "${BLUE}Restarting Docker service...${NC}"
    sudo systemctl restart docker
    
    # Kiểm tra kết quả
    sleep 3
    if sudo systemctl is-active --quiet docker; then
        echo -e "${GREEN}✅ Docker daemon đã được sửa và đang chạy${NC}"
        
        # Kiểm tra Docker info
        if docker info >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker daemon hoạt động bình thường${NC}"
        else
            echo -e "${RED}❌ Docker daemon vẫn có vấn đề${NC}"
        fi
    else
        echo -e "${RED}❌ Không thể sửa Docker daemon${NC}"
        echo -e "${YELLOW}Kiểm tra logs: sudo journalctl -u docker --no-pager -l${NC}"
    fi
    
    echo "---------------------------"
}

# --- Hàm cập nhật Docker ---
update_docker() {
    echo -e "${YELLOW}Bắt đầu quá trình cập nhật Docker...${NC}"
    echo -e "${BLUE}Lưu ý: Bạn cần có kết nối internet để cập nhật.${NC}"
    echo "---------------------------"

    # Cập nhật danh sách gói
    echo -e "${BLUE}1. Cập nhật danh sách gói APT...${NC}"
    sudo apt update
    if [ $? -ne 0 ]; then
        echo -e "${RED}Lỗi: Không thể cập nhật danh sách gói. Vui lòng kiểm tra kết nối internet hoặc kho APT.${NC}"
        echo "---"
        return 1
    fi
    echo -e "${GREEN}Danh sách gói đã được cập nhật.${NC}"
    echo "---"

    # Nâng cấp các gói Docker
    echo -e "${BLUE}2. Nâng cấp các gói Docker (docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin)...${NC}"
    sudo apt upgrade -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Docker đã được cập nhật thành công!${NC}"
    else
        echo -e "${RED}Lỗi: Không thể nâng cấp Docker. Vui lòng kiểm tra lại hoặc thử cài đặt thủ công.${NC}"
        echo "---"
        return 1
    fi
    echo "---"

    echo -e "${BLUE}Phiên bản Docker hiện tại: $(docker version --format '{{.Server.Version}}')${NC}"
    
    # Tự động khởi động lại Docker daemon sau khi cập nhật
    echo -e "${BLUE}Đang khởi động lại Docker daemon để áp dụng các thay đổi...${NC}"
    restart_docker_daemon
    
    # Xử lý systemd warnings nếu có
    echo -e "${BLUE}Kiểm tra systemd warnings...${NC}"
    if sudo systemctl daemon-reload 2>&1 | grep -q "Warning"; then
        echo -e "${YELLOW}⚠️  Systemd warning detected, applying fix...${NC}"
        sudo systemctl daemon-reload
        sudo systemctl reset-failed
        echo -e "${GREEN}✅ Systemd warnings resolved${NC}"
    else
        echo -e "${GREEN}✅ No systemd warnings found${NC}"
    fi

    echo -e "${GREEN}Quá trình cập nhật Docker đã hoàn tất.${NC}"
    echo "---"
}

# --- Hàm tìm và chọn dự án Docker Compose ---
select_docker_compose_project() {
    local -n _selected_path=$1 # Tham chiếu đến biến sẽ lưu đường dẫn đã chọn
    _selected_path="" # Khởi tạo rỗng

    echo -e "${BLUE}Đang tìm kiếm các dự án Docker Compose trong thư mục hiện tại và các thư mục con...${NC}"
    
    IFS=$'\n' # Đặt Internal Field Separator thành ký tự xuống dòng cho đầu ra của 'find'
    # Tìm các thư mục chứa docker-compose.yml hoặc compose.yaml trong thư mục hiện tại và một cấp độ sâu
    local projects=($(find . -maxdepth 2 -type f \( -name "docker-compose.yml" -o -name "compose.yaml" \) -exec dirname {} \; | sort -u))
    unset IFS

    if [ ${#projects[@]} -eq 0 ]; then
        echo -e "${RED}Không tìm thấy dự án Docker Compose nào trong thư mục hiện tại và các thư mục con cấp một. Vui lòng đảm bảo bạn đang ở đúng vị trí hoặc tạo tệp docker-compose.yml.${NC}"
        echo "---"
        return 1 # Báo hiệu thất bại
    elif [ ${#projects[@]} -eq 1 ]; then
        # Nếu chỉ tìm thấy 1 dự án (dù là . hay thư mục con), tự động chọn nó
        _selected_path="${projects[0]}"
        echo -e "${GREEN}Đã tự động chọn dự án duy nhất tìm thấy: ${BLUE}${_selected_path}${NC}"
    else
        # Có nhiều dự án hoặc cần nhập thủ công, hiển thị danh sách
        echo -e "${YELLOW}Các dự án Docker Compose đã tìm thấy:${NC}"
        for i in "${!projects[@]}"; do
            echo -e "${GREEN}$((i+1)). ${projects[$i]}${NC}"
        done
        echo -e "${RED}0. Nhập đường dẫn thủ công (nếu dự án của bạn không có trong danh sách)${NC}"
        
        local project_choice
        while true; do
            read -p "$(echo -e "${YELLOW}Chọn số của dự án (hoặc 0 để nhập thủ công): ${NC}")" project_choice
            if [[ "$project_choice" =~ ^[0-9]+$ ]] && (( project_choice >= 0 && project_choice <= ${#projects[@]} )); then
                if [ "$project_choice" -eq 0 ]; then
                    read -p "$(echo -e "${YELLOW}Nhập đường dẫn thư mục dự án Docker Compose: ${NC}")" manual_path
                    # Đảm bảo đường dẫn tồn tại và chứa file compose
                    if [ -d "$manual_path" ] && ( [ -f "$manual_path/docker-compose.yml" ] || [ -f "$manual_path/compose.yaml" ] ); then
                        _selected_path="$manual_path"
                        break
                    else
                        echo -e "${RED}Lỗi: Đường dẫn hoặc tệp docker-compose.yml/compose.yaml không hợp lệ. Vui lòng thử lại.${NC}"
                    fi
                else
                    _selected_path="${projects[$((project_choice-1))]}"
                    break
                fi
            else
                echo -e "${RED}Lựa chọn không hợp lệ. Vui lòng nhập số hợp lệ.${NC}"
            fi
        done
        echo -e "${GREEN}Đã chọn dự án: ${BLUE}${_selected_path}${NC}"
    fi
    echo "---"
    return 0 # Báo hiệu thành công
}

# --- Hàm quản lý Docker Compose ---
manage_docker_compose() {
    echo -e "${YELLOW}Bạn đang vào menu quản lý Docker Compose.${NC}"
    local project_path=""
    if ! select_docker_compose_project project_path; then
        return 1 # Thoát nếu chọn dự án thất bại
    fi

    while true; do
        echo -e "${CYAN}========== Menu Docker Compose ==========${NC}"
        echo -e "${GREEN}  Dự án hiện tại: ${project_path}${NC}"
        echo -e "${GREEN}1. Khởi động dự án (docker compose up -d)${NC}"
        echo -e "${GREEN}2. Dừng dự án (docker compose down)${NC}"
        echo -e "${GREEN}3. Xây dựng lại dự án (docker compose build)${NC}"
        echo -e "${GREEN}4. Xem Logs dự án (docker compose logs -f)${NC}"
        echo -e "${GREEN}5. Chạy lệnh trong service (e.g., migrate)${NC}"
        echo -e "${RED}0. Quay lại Menu Chính${NC}"
        echo -e "${CYAN}=========================================${NC}"
        read -p "Chọn một tùy chọn: " dc_choice

        case $dc_choice in
            1)
                (cd "$project_path" && docker compose up -d) || echo -e "${RED}Lỗi: Không thể khởi động Docker Compose. Vui lòng kiểm tra cấu hình.${NC}"
                ;;
            2)
                (cd "$project_path" && docker compose down) || echo -e "${RED}Lỗi: Không thể dừng Docker Compose.${NC}"
                ;;
            3)
                (cd "$project_path" && docker compose build) || echo -e "${RED}Lỗi: Không thể build lại Docker Compose.${NC}"
                ;;
            4)
                (cd "$project_path" && docker compose logs -f) || echo -e "${RED}Lỗi: Không thể xem logs.${NC}"
                ;;
            5)
                read -p "$(echo -e "${YELLOW}Nhập tên service (ví dụ: web, app, django, postgres): ${NC}")" service_name
                read -p "$(echo -e "${YELLOW}Nhập lệnh cần chạy (ví dụ: python manage.py migrate, psql -U user -d db): ${NC}")" cmd_to_run
                (cd "$project_path" && docker compose exec -it "$service_name" bash -c "$cmd_to_run") || echo -e "${RED}Lỗi: Không thể chạy lệnh.${NC}"
                ;;
            0)
                echo -e "${YELLOW}Quay lại Menu Chính.${NC}"
                break
                ;;
            *)
                echo -e "${RED}Lựa chọn không hợp lệ. Vui lòng chọn lại.${NC}"
                ;;
        esac
        echo # Dòng trống để dễ đọc
        read -p "Nhấn Enter để tiếp tục..."
    done
}

# --- Hàm đoán tên service Django (Phiên bản cuối cùng, tối ưu) ---
guess_django_service_name() {
    local project_path="$1"
    local config_file="${project_path}/docker-compose.yml"
    if [ ! -f "$config_file" ]; then
        config_file="${project_path}/compose.yaml"
    fi

    local guessed_name=""

    if [ -f "$config_file" ]; then
        local potential_django_services=()
        IFS=$'\n' # Đặt Internal Field Separator thành ký tự xuống dòng
        
        # Cải tiến logic để lấy chính xác các tên service dưới block 'services:'
        # Tên service phải được thụt vào (ít nhất 2 khoảng trắng) so với 'services:'
        # và kết thúc bằng ':' và không phải là dòng comment
        local all_services=($(awk '
            /^[[:space:]]*services:/ { in_services_block=1; next }
            in_services_block && /^[[:space:]]{2,}[^[:space:]#].*:/ {
                # Loại bỏ khoảng trắng đầu và dấu ':' để lấy tên service
                print substr($0, match($0, /^ +/) + 1, index($0, ":") - match($0, /^ +/) - 1)
            }
            /^[[:graph:]]/ { # Nếu là một block cấp cao mới (không bắt đầu bằng khoảng trắng), thoát khỏi block services
                in_services_block=0
            }
        ' "$config_file"))
        unset IFS

        for service_name in "${all_services[@]}"; do
            # Lấy block cấu hình của service đó
            local service_block=$(awk "/^\\s*${service_name}:/{flag=1;print;next}/^\\S/ && flag{flag=0}flag" "$config_file")
            
            # Tiêu chí 1: Build context trỏ đến thư mục 'backend' (hoặc 'app', 'src', 'server')
            if echo "$service_block" | grep -E -q "build:[[:space:]]*\n[[:space:]]+context:[[:space:]]*(./backend|./app|./src|./server)"; then
                potential_django_services+=("$service_name")
                continue
            fi

            # Tiêu chí 2: Lệnh khởi động chứa 'gunicorn', 'python manage.py', hoặc 'celery'
            # Cải thiện regex để bắt các định dạng command khác nhau (string, list) và dấu ngoặc kép
            if echo "$service_block" | grep -E -q "command:[[:space:]]*(\[|\")?.*\b(gunicorn|python manage.py|celery)\b.*(\]|\")?"; then
                potential_django_services+=("$service_name")
                continue
            fi
            
            # Tiêu chí 3: Volumes có chứa đường dẫn liên quan đến Django project (e.g., ./backend:/app)
            if echo "$service_block" | grep -E -q "volumes:[[:space:]]*\n[[:space:]]+- (./backend|./app|./src|./server):/app(:consistent)?"; then
                potential_django_services+=("$service_name")
                continue
            fi

            # Tiêu chí 4: Image có liên quan đến Python/Django
            if echo "$service_block" | grep -E -q "image:[[:space:]]*(python:|django:|gunicorn:|ghcr.io/python/)"; then
                potential_django_services+=("$service_name")
                continue
            fi
            
            # Tiêu chí 5: Có biến môi trường DJANGO_SETTINGS_MODULE
            if echo "$service_block" | grep -E -q "DJANGO_SETTINGS_MODULE="; then
                potential_django_services+=("$service_name")
                continue
            fi

            # Tiêu chí 6: Có biến môi trường Python (PYTHONUNBUFFERED, PYTHONDONTWRITEBYTECODE)
            if echo "$service_block" | grep -E -q "(PYTHONUNBUFFERED|PYTHONDONTWRITEBYTECODE)="; then
                potential_django_services+=("$service_name")
                continue
            fi
        done

        # Ưu tiên các tên service phổ biến cho Django, đặc biệt là 'backend'
        local preferred_names=("backend" "web" "app" "django" "api" "server") # Thêm "api" và "server"
        for pref_name in "${preferred_names[@]}"; do
            for found_name in "${potential_django_services[@]}"; do
                if [[ "$found_name" == "$pref_name" ]]; then
                    guessed_name="$found_name"
                    break 2 # Thoát cả hai vòng lặp nếu tìm thấy
                fi
            done
        done
        
        # Nếu không tìm thấy tên ưu tiên nhưng vẫn có service tiềm năng, chọn service đầu tiên
        if [ -z "$guessed_name" ] && [ ${#potential_django_services[@]} -gt 0 ]; then
            guessed_name="${potential_django_services[0]}"
        fi
    fi
    echo "$guessed_name"
}


# --- Hàm quản lý dự án Django ---
manage_django_project() {
    echo -e "${YELLOW}Bạn đang vào menu quản lý dự án Django.${NC}"
    local project_path=""
    if ! select_docker_compose_project project_path; then
        return 1 # Thoát nếu chọn dự án thất bại
    fi

    local django_service_name=""
    local guessed_name=$(guess_django_service_name "$project_path")

    if [ -n "$guessed_name" ]; then
        read -p "$(echo -e "${YELLOW}Nhập tên service Django của bạn (mặc định: ${guessed_name}, nhấn Enter để xác nhận): ${NC}")" input_service_name
        django_service_name="${input_service_name:-$guessed_name}"
    else
        read -p "$(echo -e "${YELLOW}Nhập tên service Django của bạn trong docker-compose.yml (thường là 'web', 'app', 'django', 'backend'): ${NC}")" django_service_name
    fi

    # Kiểm tra xem tên service có hợp lệ không
    if [ -z "$django_service_name" ]; then
        echo -e "${RED}Lỗi: Tên service Django không được để trống.${NC}"
        echo "---"
        return 1
    fi

    # Đảm bảo Docker Compose đang chạy để có thể exec vào container
    if ! (cd "$project_path" && docker compose ps -q "$django_service_name" &> /dev/null); then
        echo -e "${RED}Lỗi: Service Django '${django_service_name}' không chạy hoặc không tồn tại trong dự án này.${NC}"
        read -p "$(echo -e "${YELLOW}Bạn có muốn khởi động dự án Docker Compose này không? (y/n): ${NC}")" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Đang khởi động Docker Compose...${NC}"
            (cd "$project_path" && docker compose up -d)
            if [ $? -ne 0 ]; then
                echo -e "${RED}Lỗi: Không thể khởi động Docker Compose. Vui lòng kiểm tra lại cấu hình.${NC}"
                echo "---"
                return 1
            fi
            # Cho một chút thời gian để service khởi động
            echo -e "${GREEN}Docker Compose đã được khởi động. Đang đợi service '${django_service_name}' ổn định...${NC}"
            sleep 5 # Đợi 5 giây
            if ! (cd "$project_path" && docker compose ps -q "$django_service_name" &> /dev/null); then
                 echo -e "${RED}Cảnh báo: Service '${django_service_name}' vẫn chưa hoạt động sau khi khởi động.${NC}"
                 echo -e "${RED}Vui lòng kiểm tra logs thủ công nếu gặp vấn đề.${NC}"
                 echo "---"
                 return 1 # Quay lại menu chính nếu service không ổn định
            fi
            echo -e "${GREEN}Service '${django_service_name}' đã hoạt động.${NC}"
        else
            echo -e "${YELLOW}Đã hủy thao tác. Vui lòng khởi động Docker Compose thủ công nếu muốn tiếp tục.${NC}"
            echo "---"
            return 1
        fi
    fi


    while true; do
        echo -e "${MAGENTA}========== Menu Quản lý Dự án Django ==========${NC}"
        echo -e "${GREEN}  Dự án: ${project_path}, Service Django: ${django_service_name}${NC}"
        echo -e "${GREEN}1. Chạy Migrations (python manage.py migrate)${NC}"
        echo -e "${GREEN}2. Tạo Superuser (python manage.py createsuperuser)${NC}"
        echo -e "${GREEN}3. Chạy Server phát triển (python manage.py runserver 0.0.0.0:8000)${NC}"
        echo -e "${GREEN}4. Thu thập các tệp tĩnh (python manage.py collectstatic)${NC}"
        echo -e "${GREEN}5. Chạy Shell Django (python manage.py shell)${NC}"
        echo -e "${GREEN}6. Chạy lệnh tùy chỉnh (python manage.py ...)${NC}"
        echo -e "${RED}0. Quay lại Menu Chính${NC}"
        echo -e "${MAGENTA}=========================================${NC}"
        read -p "Chọn một tùy chọn: " django_choice

        case $django_choice in
            1)
                (cd "$project_path" && docker compose exec -it "$django_service_name" python manage.py migrate) || echo -e "${RED}Lỗi khi chạy migrations.${NC}"
                ;;
            2)
                (cd "$project_path" && docker compose exec -it "$django_service_name" python manage.py createsuperuser) || echo -e "${RED}Lỗi khi tạo superuser.${NC}"
                ;;
            3)
                echo -e "${YELLOW}Chạy server phát triển. Bạn có thể cần mở một terminal khác để tiếp tục tương tác với script này.${NC}"
                echo -e "${YELLOW}Để dừng server, nhấn Ctrl+C trong terminal mà nó đang chạy.${NC}"
                # Sử dụng -T để không phân bổ TTY, thích hợp cho các lệnh chạy background hoặc không cần tương tác
                (cd "$project_path" && docker compose exec -T "$django_service_name" python manage.py runserver 0.0.0.0:8000) || echo -e "${RED}Lỗi khi chạy server phát triển.${NC}"
                ;;
            4)
                (cd "$project_path" && docker compose exec -it "$django_service_name" python manage.py collectstatic --noinput) || echo -e "${RED}Lỗi khi thu thập tệp tĩnh.${NC}"
                ;;
            5)
                echo -e "${YELLOW}Đang mở Django shell. Nhấn Ctrl+D hoặc gõ 'exit()' để thoát.${NC}"
                # Sử dụng -it để phân bổ TTY và tương tác
                (cd "$project_path" && docker compose exec -it "$django_service_name" python manage.py shell) || echo -e "${RED}Lỗi khi mở Django shell.${NC}"
                ;;
            6)
                read -p "$(echo -e "${YELLOW}Nhập lệnh 'manage.py' tùy chỉnh (ví dụ: changepassword <username>): ${NC}")" custom_django_cmd
                # Sử dụng bash -c để đảm bảo lệnh được phân tích cú pháp đúng
                (cd "$project_path" && docker compose exec -it "$django_service_name" bash -c "python manage.py $custom_django_cmd") || echo -e "${RED}Lỗi khi chạy lệnh tùy chỉnh.${NC}"
                ;;
            0)
                echo -e "${YELLOW}Quay lại Menu Chính.${NC}"
                break
                ;;
            *)
                echo -e "${RED}Lựa chọn không hợp lệ. Vui lòng chọn lại.${NC}"
                ;;
        esac
        echo # Dòng trống để dễ đọc
        read -p "Nhấn Enter để tiếp tục..."
    done
}


# --- Hàm hiển thị menu chính ---
display_menu() {
    echo -e "${PURPLE}========== Menu Quản lý Docker & Dự án Django ==========${NC}"
    echo -e "${GREEN}1. Xóa sạch Docker HOÀN TOÀN (như lúc mới cài đặt)${NC}"
    echo -e "${GREEN}2. Xem thông tin Docker tổng quan (docker info)${NC}"
    echo -e "${GREEN}3. Liệt kê Containers${NC}"
    echo -e "${GREEN}4. Liệt kê Images${NC}"
    echo -e "${GREEN}5. Liệt kê Volumes${NC}"
    echo -e "${GREEN}6. Liệt kê Networks${NC}"
    echo -e "${GREEN}7. Khởi động lại Docker Daemon${NC}"
    echo -e "${YELLOW}8. Cập nhật Docker (docker-ce và các thành phần liên quan)${NC}"
    echo -e "${RED}9. Sửa lỗi Docker Daemon (kiểm tra và sửa cấu hình)${NC}"
    echo -e "${CYAN}10. Quản lý Docker Compose (Menu phụ)${NC}"
    echo -e "${MAGENTA}11. Quản lý Dự án Django (Menu phụ)${NC}"
    echo -e "${RED}0. Thoát${NC}"
    echo -e "${PURPLE}=========================================${NC}"
    read -p "Chọn một tùy chọn: " choice
}

# --- Logic chính của script ---
main() {
    check_docker_status

    while true; do
        display_menu
        case $choice in
            1)
                clean_docker_components
                ;;
            2)
                show_docker_info
                ;;
            3)
                list_containers
                ;;
            4)
                list_images
                ;;
            5)
                list_volumes
                ;;
            6)
                list_networks
                ;;
            7)
                restart_docker_daemon
                ;;
            8)
                update_docker
                ;;
            9)
                fix_docker_daemon
                ;;
            10)
                manage_docker_compose
                ;;
            11)
                manage_django_project
                ;;
            0)
                echo -e "${YELLOW}Đang thoát khỏi script. Tạm biệt!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Lựa chọn không hợp lệ. Vui lòng chọn lại.${NC}"
                ;;
        esac
        echo # Dòng trống để dễ đọc
        read -p "Nhấn Enter để tiếp tục..."
    done
}

# Chạy hàm main
main

#!/bin/bash

# NHẬP DÃY KEY CỦA BẠN VÀO ĐÂY (Cách nhau bằng dấu phẩy, không khoảng trắng)
INPUT_KEYS="AIzaSyDGf4FYnAP7Tp463xm6XocO9SnHxGFikSs,AIzaSyBUDTtODvWg1vUL2gjsHM8UDBU9228r8ew,AIzaSyAsl3t1zInuOo8tskrz1_FzO9o8GOPrk4A,AIzaSyAdWxvdliDJCdRTRc3wDjPqMbBuQWTpRmI,AIzaSyBUwokbBFhIcaZR9PQ0mlb7W9awGN0odsk,AIzaSyAMEVZrNziQi1zPINg09iURV5LEtqcI7bo,AIzaSyBYYrrjd61yL98W61owDVbkH6MCchXLHj8"

IFS=',' read -ra ADDR <<< "$INPUT_KEYS"

echo "============================================================"
echo "         GEMINI MULTI-MODEL SCANNER"
echo "============================================================"

for KEY in "${ADDR[@]}"; do
    KEY=$(echo $KEY | xargs)
    [ -z "$KEY" ] && continue

    echo "🔑 Đang check: ${KEY:0:8}...${KEY: -4}"
    
    # 1. Lấy Header và Body riêng biệt
    RESPONSE=$(curl -s -i "https://generativelanguage.googleapis.com/v1beta/models?key=${KEY}")
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP/" | awk '{print $2}' | tail -n 1)
    BODY=$(echo "$RESPONSE" | awk '/^\r$/ {p=1; next} p')

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "  ✅ Trạng thái: KEY SỐNG (ACTIVE)"
        
        # 2. Tự động tìm model tốt nhất hiện có để test Quota
        # Ưu tiên theo thứ tự: gemini-1.5-flash -> gemini-pro -> model đầu tiên tìm thấy
        BEST_MODEL=$(echo "$BODY" | grep -o '"name": "models/[^"]*"' | cut -d'/' -f2 | tr -d '"' | grep -E "flash|pro" | head -n 1)
        
        if [ -z "$BEST_MODEL" ]; then
             BEST_MODEL=$(echo "$BODY" | grep -o '"name": "models/[^"]*"' | cut -d'/' -f2 | tr -d '"' | head -n 1)
        fi

        echo "  🎯 Thử nghiệm Quota với: $BEST_MODEL"

        # 3. Gửi request thực tế để check Quota
        QUOTA_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
            -H 'Content-Type: application/json' \
            -d '{"contents": [{"parts":[{"text": "ping"}]}]}' \
            -X POST "https://generativelanguage.googleapis.com/v1beta/models/${BEST_MODEL}:generateContent?key=${KEY}")
        
        if [ "$QUOTA_CHECK" -eq 200 ]; then
            echo "  💰 Hạn mức: CÒN LƯỢT (Ready)"
        elif [ "$QUOTA_CHECK" -eq 429 ]; then
            echo "  ⚠️ Hạn mức: HẾT QUOTA (Rate Limit)"
        else
            echo "  ❓ Hạn mức: Lỗi $QUOTA_CHECK (Endpoint có thể yêu cầu cấu hình khác)"
        fi
        
        # 4. Liệt kê toàn bộ Model khả dụng (để bạn theo dõi)
        ALL_MODELS=$(echo "$BODY" | grep -o '"name": "models/[^"]*"' | cut -d'/' -f2 | tr -d '"' | xargs)
        echo "  📦 Danh sách Model: $ALL_MODELS"

    else
        echo "  ❌ Trạng thái: KEY CHẾT/LỖI ($HTTP_STATUS)"
        MSG=$(echo "$BODY" | grep -o '"message": "[^"]*"' | head -n 1 | cut -d'"' -f4)
        echo "  💬 Chi tiết: ${MSG:-"Key không hợp lệ hoặc đã bị vô hiệu hóa"}"
    fi
    echo "------------------------------------------------------------"
done
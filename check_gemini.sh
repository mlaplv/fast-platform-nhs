#!/bin/bash

# ĐỌC DÃY KEY TỪ FILE text.key
if [ ! -f "text.key" ]; then
    echo "❌ Lỗi: Không tìm thấy file text.key. Vui lòng tạo file text.key và dán danh sách key vào đó."
    exit 1
fi

INPUT_KEYS=$(tr '\n' ',' < text.key | tr -d ' \r\t' | sed 's/,$//')

IFS=',' read -ra ADDR <<< "$INPUT_KEYS"

echo "========================================================================================================================"
printf "%-18s | %-37s | %-s\n" "KEY (SHORT)" "TRẠNG THÁI QUOTA (BEST ALIVE)" "TOP 3 MODELS"
echo "------------------------------------------------------------------------------------------------------------------------"

for KEY in "${ADDR[@]}"; do
    KEY=$(echo $KEY | xargs)
    [ -z "$KEY" ] && continue

    # 1. Lấy Header và Body riêng biệt
    RESPONSE=$(curl -s -i "https://generativelanguage.googleapis.com/v1beta/models?key=${KEY}")
    HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP/" | awk '{print $2}' | tail -n 1)
    BODY=$(echo "$RESPONSE" | awk '/^\r$/ {p=1; next} p')

    if [ "$HTTP_STATUS" -eq 200 ]; then
        # 2. Lấy danh sách các dòng Gemini có đánh số (đã sắp xếp 3.1 > 2.5...)
        GEMINI_LIST=$(echo "$BODY" | grep -o '"name": "models/gemini-[0-9][^"]*"' | cut -d'/' -f2 | tr -d '"' | sort -rV)
        
        STATUS="⚠️ HẾT QUOTA (Limit)"
        MOD_ALIVE="None"
        
        # 3. Vòng lặp tìm model CÒN QUOTA (Skill lùi bước để tiến tới)
        for M in $GEMINI_LIST; do
            QUOTA_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
                -H 'Content-Type: application/json' \
                -d '{"contents": [{"parts":[{"text": "ping"}]}]}' \
                -X POST "https://generativelanguage.googleapis.com/v1beta/models/${M}:generateContent?key=${KEY}")
            
            if [ "$QUOTA_CHECK" -eq 200 ]; then
                STATUS="✅ CÒN QUOTA ($M)"
                MOD_ALIVE=$M
                break
            fi
        done
        
        # 4. Lấy 3 model mới nhất để Sếp theo dõi danh sách
        TOP_3=$(echo "$GEMINI_LIST" | head -n 3 | xargs | tr ' ' ',')

        printf "%-18s | %-37s | %-s\n" "${KEY:0:12}...${KEY: -4}" "$STATUS" "$TOP_3"

    else
        MSG=$(echo "$BODY" | grep -o '"message": "[^"]*"' | head -n 1 | cut -d'"' -f4)
        printf "%-18s | %-25s | %-s\n" "${KEY:0:12}...${KEY: -4}" "❌ CHẾT ($HTTP_STATUS)" "${MSG:-"Khống hợp lệ"}"
    fi
done
echo "===================================================================================================="
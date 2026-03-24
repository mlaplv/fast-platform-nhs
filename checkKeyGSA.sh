#!/bin/bash

# checkKeyGSA.sh - Google Search API Key Diagnostic Tool
# Usage: ./checkKeyGSA.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== NEURAL XOHI: Google Search Key Diagnostic ===${NC}"

if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    exit 1
fi

# Load .env variables (ignoring comments)
export $(grep -v '^#' .env | xargs)

check_key() {
    local key=$1
    local cx=$2
    local label=$3
    
    if [ -z "$key" ] || [ -z "$cx" ]; then
        return
    fi

    echo -ne "Checking ${YELLOW}[$label]${NC} Key: ${key:0:8}...${key: -4} | CX: ${cx:0:8}... "
    
    # Perform a minimal test search (q=test)
    response=$(curl -s -w "\n%{http_code}" "https://www.googleapis.com/customsearch/v1?key=${key}&cx=${cx}&q=test&num=1&searchType=image")
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" == "200" ]; then
        echo -e "${GREEN}[OK]${NC}"
    elif [ "$http_code" == "429" ]; then
        echo -e "${YELLOW}[RATE LIMITED (429)]${NC}"
    elif [ "$http_code" == "403" ]; then
        reason=$(echo "$body" | grep -o '"reason": "[^"]*"' | head -n 1 | cut -d'"' -f4)
        if [ "$reason" == "dailyLimitExceeded" ]; then
            echo -e "${YELLOW}[QUOTA EXCEEDED (403: $reason)]${NC}"
        else
            echo -e "${RED}[FORBIDDEN (403: $reason)]${NC}"
        fi
    else
        echo -e "${RED}[FAILED (Status: $http_code)]${NC}"
    fi
}

echo -e "Scanning .env for keys..."

# 1. Check comma-separated keys
if [ -n "$GOOGLE_SEARCH_KEYS" ]; then
    IFS=',' read -ra KEYS <<< "$GOOGLE_SEARCH_KEYS"
    IFS=',' read -ra CXS <<< "$GOOGLE_SEARCH_ENGINE_IDS"
    default_cx=${CXS[0]}
    [ -z "$default_cx" ] && default_cx=$GOOGLE_SEARCH_ENGINE_ID
    
    for i in "${!KEYS[@]}"; do
        key=$(echo "${KEYS[$i]}" | xargs)
        cx=$(echo "${CXS[$i]}" | xargs)
        [ -z "$cx" ] && cx=$default_cx
        check_key "$key" "$cx" "Bulk_$i"
    done
fi

# 2. Check suffixed keys
check_key "$GOOGLE_SEARCH_API_KEY" "$GOOGLE_SEARCH_ENGINE_ID" "Primary"
for i in {1..10}; do
    key_var="GOOGLE_SEARCH_API_KEY_$i"
    cx_var="GOOGLE_SEARCH_ENGINE_ID_$i"
    key_val="${!key_var}"
    cx_val="${!cx_var}"
    if [ -n "$key_val" ]; then
        check_key "$key_val" "$cx_val" "Index_$i"
    fi
done

echo -e "${BLUE}===============================================${NC}"

#!/bin/bash
# XOHI ELITE V2.2 - NEURAL TEST SUITE (CLI CMD MODE)
echo "----------------------------------------------------------------"
echo "🚀 [XOHI ELITE V2.2] ĐANG KHỞI ĐỘNG HỆ THỐNG KIỂM THỬ CLI..."
echo "----------------------------------------------------------------"

# Chạy trực tiếp trên container API đang hoạt động
docker compose exec fast_platform_api python backend/scripts/verify_operatives.py

echo "----------------------------------------------------------------"
echo "✅ KIỂM THỬ HOÀN TẤT!"

#!/bin/bash
echo "--- Dang bat dau qua trinh cai dat TablePlus cho Ubuntu 24.04 ---"

echo "[1/3] Dang them GPG key..."
wget -qO - https://deb.tableplus.com/apt.tableplus.com.gpg.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/tableplus-archive.gpg > /dev/null

echo "[2/3] Dang cau hinh Repository..."
echo "deb [arch=amd64] https://deb.tableplus.com/debian/24 tableplus main" | sudo tee /etc/apt/sources.list.d/tableplus.list

echo "[3/3] Dang cap nhat he thong va cai dat TablePlus..."
sudo apt update
sudo apt install tableplus -y

echo "--- CAI DAT HOAN TAT! Ban co the mo TablePlus tu Menu ung dung ---"

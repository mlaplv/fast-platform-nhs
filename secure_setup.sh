#!/bin/bash

# 1. Cấu hình SSH để tắt mật khẩu (Đảm bảo bạn đã add SSH Key vào authorized_keys trước khi chạy!)
echo "Configuring SSH..."
sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#ChallengeResponseAuthentication yes/ChallengeResponseAuthentication no/' /etc/ssh/sshd_config
systemctl restart ssh

# 2. Cấu hình tường lửa UFW
echo "Configuring UFW..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "Security setup completed!"
echo "LƯU Ý: Hãy chắc chắn bạn đã test SSH bằng Key thành công trước khi đóng terminal này!"
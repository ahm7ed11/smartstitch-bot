#!/bin/bash
# سكريبت تركيب smartstitch-bot على Oracle Cloud (Ubuntu)
set -e

echo "==> تحديث النظام..."
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git

echo "==> استنساخ المشروع..."
cd ~
if [ ! -d "smartstitch-bot" ]; then
  git clone https://github.com/ahm7ed11/smartstitch-bot.git
fi
cd smartstitch-bot

echo "==> إنشاء بيئة بايثون..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> جاهز! دلوقتي:"
echo "1. حط ملف .env (شوف .env.example)"
echo "2. حط service_account.json و oauth_client.json"
echo "3. شغل: sudo cp smartstitch-bot.service /etc/systemd/system/"
echo "4. sudo systemctl daemon-reload && sudo systemctl enable --now smartstitch-bot"

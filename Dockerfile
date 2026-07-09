FROM python:3.11-slim

WORKDIR /app

# مكتبات النظام المطلوبة لـ Pillow / psd-tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# البوت مش بيسمع على أي بورت (مش ويب سيرفر)، بس Fly.io محتاج نص إعدادات فقط
CMD ["python", "bot.py"]

FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libffi-dev \
    libsodium-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ép PyNaCl sử dụng libsodium của hệ thống Linux để chạy voice mượt mà
ENV SODIUM_INSTALL=system

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]

FROM python:3.10-slim

# Cài đặt các công cụ biên dịch hệ thống và ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    libffi-dev \
    libnacl-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]

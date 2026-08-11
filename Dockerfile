FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết cho voice
RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
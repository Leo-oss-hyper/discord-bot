FROM python:3.10-slim

# Cài đặt ffmpeg phục vụ cho việc phát âm thanh trong voice channel
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]

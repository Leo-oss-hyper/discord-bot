FROM python:3.10-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy toàn bộ file trong máy vào thư mục app trên mây
COPY . /app

# Cài đặt thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Lệnh chạy bot
CMD ["python", "bot.py"]
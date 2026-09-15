import base64
import os
import subprocess
import tempfile
import discord
from discord.ext import commands
from flask import Flask
from google import genai
import httpx

# ==================== CẤU HÌNH KHỞI TẠO ====================
app = Flask(__name__)


@app.route("/")
def home():
  return "Bot is running 24/7!"


# Khởi tạo Gemini Client (Dùng key từ biến môi trường)
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Cấu hình Discord Bot Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ID kênh được phép dùng AI (Cố định dạng chuỗi để so sánh chính xác tuyệt đối)
ALLOWED_CHANNEL_ID = "1549094816678420580"


# ==================== SỰ KIỆN KHI BOT SẴN SÀNG ====================
@bot.event
async def on_ready():
  print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
  print("Bot is ready and connected to Discord!")


# ==================== LỆNH KẾT NỐI VOICE (!afk voice) ====================
@bot.command(name="afk")
async def afk_voice(ctx, mode: str = None):
  if mode == "voice":
    if ctx.author.voice:
      channel = ctx.author.voice.channel
      if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
      else:
        try:
          await channel.connect()
        except Exception as e:
          await ctx.send(f"❌ Có lỗi khi kết nối voice: {e}")
          return
      await ctx.send(
          f"🎙️ Đã vào phòng voice **{channel.name}** và sẵn sàng hỗ trợ anh!"
      )
    else:
      await ctx.send("⚠️ Anh phải vào một phòng Voice trước đã nhé!")
  else:
    await ctx.send("💡 Cú pháp đúng: `!afk voice`")


# ==================== LỆNH LÀM SẠCH KÊNH (!clean) ====================
@bot.command(name="clean")
async def clean_chat(ctx, limit: int = 5):
  await ctx.message.delete()
  deleted = await ctx.channel.purge(limit=limit)
  await ctx.send(
      f"🧹 Đã dọn dẹp {len(deleted)} tin nhắn gần nhất!", delete_after=3
  )


# ==================== LỆNH AI CHÍNH (!ai) ====================
@bot.command(name="ai")
async def ai_chat(ctx, *, prompt: str = None):
  # KIỂM TRA KÊNH: Nếu gõ ngoài kênh được chỉ định thì chặn ngay lập tức
  if str(ctx.channel.id) != ALLOWED_CHANNEL_ID:
    await ctx.send(
        f"⚠️ Bot chỉ trả lời lệnh `!ai` trong kênh <#{ALLOWED_CHANNEL_ID}> thôi"
        " anh nhé!",
        delete_after=5,
    )
    return

  if not prompt and not ctx.message.attachments:
    await ctx.send("💡 Vui lòng nhập nội dung hoặc gửi kèm hình ảnh cần hỏi!")
    return

  async with ctx.typing():
    try:
      contents = []
      image_temp_path = None

      # Xử lý hình ảnh nếu có gửi kèm
      if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        if attachment.content_type and attachment.content_type.startswith(
            "image"
        ):
          image_temp_path = tempfile.NamedTemporaryFile(
              delete=False, suffix=".png"
          ).name
          await attachment.save(image_temp_path)

          with open(image_temp_path, "rb") as f:
            image_bytes = f.read()

          contents.append(
              genai.types.Part.from_bytes(
                  data=image_bytes, mime_type=attachment.content_type
              )
          )

      if prompt:
        contents.append(prompt)
      else:
        contents.append(
            "Hãy phân tích hình ảnh này và đưa ra câu trả lời chi tiết bằng"
            " tiếng Việt."
        )

      # Gọi Gemini API với model chuẩn mới nhất
      response = gemini_client.models.generate_content(
          model="gemini-3.6-flash", contents=contents
      )

      ai_reply = response.text

      # Xóa file ảnh tạm nếu có
      if image_temp_path and os.path.exists(image_temp_path):
        os.remove(image_temp_path)

      # Gửi câu trả lời lên chat
      if len(ai_reply) > 2000:
        chunks = [ai_reply[i : i + 1900] for i in range(0, len(ai_reply), 1900)]
        for chunk in chunks:
          await ctx.send(chunk)
      else:
        await ctx.send(ai_reply)

      # Đọc voice nếu bot đang ở trong phòng voice
      if ctx.voice_client and ctx.voice_client.is_connected():
        speech_text = (
            ai_reply[:300] + "..." if len(ai_reply) > 300 else ai_reply
        )
        speech_text = (
            speech_text.replace("*", "")
            .replace("#", "")
            .replace("`", "")
            .replace("-", "")
        )

        audio_path = tempfile.NamedTemporaryFile(
            delete=False, suffix=".mp3"
        ).name

        tts_cmd = f'edge-tts --voice vi-VN-HoaiMyNeural --text="{speech_text}" --write-media "{audio_path}"'
        subprocess.run(tts_cmd, shell=True, check=True)

        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
          if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

          ctx.voice_client.play(
              discord.FFmpegPCMAudio(audio_path),
              after=lambda e: os.remove(audio_path)
              if os.path.exists(audio_path)
              else None,
          )

    except Exception as e:
      await ctx.send(f"❌ Đã xảy ra lỗi khi xử lý yêu cầu: `{e}`")


# ==================== CHẠY ỨNG DỤNG ====================
if __name__ == "__main__":
  import threading


  def run_flask():
    app.run(host="0.0.0.0", port=10000)


  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  TOKEN = os.environ.get("DISCORD_TOKEN")
  if TOKEN:
    bot.run(TOKEN)
  else:
    print("ERROR: DISCORD_TOKEN not found in environment variables!")

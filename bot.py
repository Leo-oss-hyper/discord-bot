import asyncio
import base64
import os
import tempfile
import threading
import discord
from flask import Flask
import httpx
from openai import OpenAI
import edge_tts

app = Flask(__name__)


@app.route("/")
def home():
  return "Discord AI Voice Chat Bot đang hoạt động!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)

# Khởi tạo client kết nối tới Gemini qua chuẩn OpenAI-compatible
ai_client = OpenAI(
    api_key=os.environ.get("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

current_voice_client = None
inactivity_task = None


async def disconnect_after_24h(voice_client):
  global inactivity_task, current_voice_client
  try:
    await asyncio.sleep(86400)
    if voice_client and voice_client.is_connected():
      members = [m for m in voice_client.channel.members if not m.bot]
      if len(members) == 0:
        await voice_client.disconnect()
        current_voice_client = None
        inactivity_task = None
        print("Đã tự động rời voice do trống vắng suốt 24 giờ liên tục.")
  except asyncio.CancelledError:
    pass


@client.event
async def on_ready():
  print(f"Đã đăng nhập thành công với tên: {client.user}")


@client.event
async def on_voice_state_update(member, before, after):
  global current_voice_client, inactivity_task
  if member.bot:
    return

  if current_voice_client and current_voice_client.is_connected():
    channel = current_voice_client.channel
    real_members = [m for m in channel.members if not m.bot]

    if len(real_members) == 0:
      if inactivity_task is None or inactivity_task.done():
        inactivity_task = asyncio.create_task(
            disconnect_after_24h(current_voice_client)
        )
    else:
      if inactivity_task and not inactivity_task.done():
        inactivity_task.cancel()
        inactivity_task = None


@client.event
async def on_message(message):
  global current_voice_client, inactivity_task
  if message.author == client.user:
    return

  content = message.content.strip()

  # 1. Lệnh xóa tin nhắn (!clean <số lượng>)
  if content.startswith("!clean"):
    parts = content.split()
    if len(parts) < 2 or not parts[1].isdigit():
      await message.channel.send(
          "❌ Vui lòng nhập đúng cú pháp, ví dụ: `!clean 5` (xóa 5 tin nhắn gần"
          " nhất)."
      )
      return

    limit_num = int(parts[1])
    if limit_num <= 0:
      await message.channel.send("❌ Số lượng tin nhắn cần xóa phải lớn hơn 0!")
      return

    try:
      deleted = await message.channel.purge(limit=limit_num + 1)
      temp_msg = await message.channel.send(
          f"🗑️ Đã dọn dẹp thành công {len(deleted) - 1} tin nhắn!"
      )
      await asyncio.sleep(3)
      await temp_msg.delete()
    except discord.Forbidden:
      await message.channel.send(
          "❌ Bot không có quyền `Manage Messages` để xóa tin nhắn!"
      )
    except discord.HTTPException as e:
      await message.channel.send(f"❌ Có lỗi xảy ra khi xóa tin nhắn: {e}")
    return

  # 2. Lệnh treo voice (!afk voice)
  if content == "!afk voice":
    if not message.author.voice or not message.author.voice.channel:
      await message.channel.send(
          "❌ Bạn phải vào một phòng Voice trước thì bot mới biết đường vào"
          " theo chứ!"
      )
      return

    target_channel = message.author.voice.channel

    try:
      if current_voice_client and current_voice_client.is_connected():
        await current_voice_client.disconnect()

      current_voice_client = await target_channel.connect()
      await message.channel.send(
          f"🎧 Đã vào phòng **{target_channel.name}** để treo voice và sẵn sàng"
          " đọc thoại cùng bạn!"
      )

      if inactivity_task and not inactivity_task.done():
        inactivity_task.cancel()
        inactivity_task = None

      real_members = [m for m in target_channel.members if not m.bot]
      if len(real_members) == 0:
        inactivity_task = asyncio.create_task(
            disconnect_after_24h(current_voice_client)
        )

    except Exception as e:
      await message.channel.send(f"❌ Có lỗi khi kết nối voice: {e}")
    return

  # 3. Lệnh !ai (Hỗ trợ text, hình ảnh và tự động đọc giọng nói vào Voice)
  if content.startswith("!ai") or message.attachments:
    user_prompt = ""
    if content.startswith("!ai "):
      user_prompt = content[4:].strip()
    elif content == "!ai":
      user_prompt = ""

    image_bytes = None
    image_url = None
    if message.attachments:
      for attachment in message.attachments:
        if any(
            attachment.filename.lower().endswith(ext)
            for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]
        ):
          image_url = attachment.url
          break

    if not user_prompt and not image_url:
      await message.channel.send(
          "Anh nhớ nhập nội dung hoặc gửi kèm ảnh cùng lệnh `!ai` nhé!"
      )
      return

    async with message.channel.typing():
      try:
        messages_payload = []
        if image_url:
          async with httpx.AsyncClient() as httpx_client:
            img_response = await httpx_client.get(image_url)
            if img_response.status_code == 200:
              image_bytes = img_response.content

          if image_bytes:
            encoded_image = base64.b64encode(image_bytes).decode("utf-8")
            if not user_prompt:
              user_prompt = (
                  "Hãy đọc toàn bộ văn bản trong ảnh này và dịch sang tiếng Việt"
                  " một cách tự nhiên, chính xác nhất."
              )

            messages_payload = [{
                "role": "system",
                "content": (
                    "Bạn là một trợ lý AI thông minh, ngắn gọn, súc tích để tiện"
                    " đọc giọng nói."
                ),
            }, {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        },
                    },
                ],
            }]
          else:
            await message.channel.send("❌ Không thể tải được ảnh từ Discord về!")
            return
        else:
          messages_payload = [{
              "role": "system",
              "content": (
                  "Bạn là một trợ lý AI thân thiện trên Discord. Hãy trả lời"
                  " ngắn gọn, rõ ràng."
              ),
          }, {"role": "user", "content": user_prompt}]

        response = ai_client.chat.completions.create(
            model="gemini-3.6-flash",
            messages=messages_payload,
            stream=False,
        )
        reply_content = response.choices[0].message.content

        # Gửi phản hồi dạng chữ lên kênh chat (cắt ngắn nếu quá 2000 ký tự)
        text_to_send = reply_content
        if len(text_to_send) > 2000:
          text_to_send = text_to_send[:1997] + "..."
        await message.channel.send(text_to_send)

        # Nếu bot đang ở trong phòng voice, tự động chuyển nội dung câu trả lời thành giọng nói phát vào voice
        if current_voice_client and current_voice_client.is_connected():
          try:
            # Tạo file âm thanh tạm thời từ edge-tts (giọng đọc Nam Minh tự nhiên)
            voice_name = "vi-VN-NamMinhNeural"
            communicate = edge_tts.Communicate(reply_content, voice_name)

            with tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3"
            ) as tf:
              temp_filename = tf.name

            await communicate.save(temp_filename)

            # Phát âm thanh vào phòng voice nếu bot chưa phát audio khác
            if not current_voice_client.is_playing():
              audio_source = discord.FFmpegPCMAudio(temp_filename)
              current_voice_client.play(audio_source)
          except Exception as voice_err:
            print(f"Lỗi khi phát giọng nói trong voice: {voice_err}")

      except Exception as e:
        await message.channel.send(f"Đã xảy ra lỗi khi xử lý: {e}")
    return


TOKEN = os.environ.get("DISCORD_TOKEN")

if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  if TOKEN:
    client.run(TOKEN)
  else:
    print(
        "Lỗi: Chưa thiết lập DISCORD_TOKEN trong Environment Variables của"
        " Render!"
    )

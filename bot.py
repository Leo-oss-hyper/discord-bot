import os
import threading
import asyncio
import discord
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord AFK Voice Bot đang hoạt động!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

client = discord.Client(intents=intents)

current_voice_client = None
inactivity_task = None

async def disconnect_after_24h(voice_client):
    global inactivity_task, current_voice_client
    try:
        # 24 giờ = 86400 giây
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
    print(f'Đã đăng nhập thành công với tên: {client.user}')

@client.event
async def on_voice_state_update(member, before, after):
    global current_voice_client, inactivity_task
    if member.bot:
        return

    if current_voice_client and current_voice_client.is_connected():
        channel = current_voice_client.channel
        real_members = [m for m in channel.members if not m.bot]
        
        if len(real_members) == 0:
            # Phòng trống: Nếu chưa có bộ đếm nào chạy thì bắt đầu đếm mới 24h
            if inactivity_task is None or inactivity_task.done():
                inactivity_task = asyncio.create_task(disconnect_after_24h(current_voice_client))
        else:
            # Có người vào phòng: Hủy bộ đếm hiện tại (reset thời gian chờ)
            if inactivity_task and not inactivity_task.done():
                inactivity_task.cancel()
                inactivity_task = None

@client.event
async def on_message(message):
    global current_voice_client, inactivity_task
    if message.author == client.user:
        return
    
    if message.content.strip() == '!afk voice':
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send("❌ Bạn phải vào một phòng Voice trước thì bot mới biết đường vào theo chứ!")
            return
        
        target_channel = message.author.voice.channel

        try:
            if current_voice_client and current_voice_client.is_connected():
                await current_voice_client.disconnect()

            current_voice_client = await target_channel.connect()
            await message.channel.send(f"🎧 Đã vào phòng **{target_channel.name}** để treo voice cùng bạn!")

            if inactivity_task and not inactivity_task.done():
                inactivity_task.cancel()
                inactivity_task = None

            real_members = [m for m in target_channel.members if not m.bot]
            if len(real_members) == 0:
                inactivity_task = asyncio.create_task(disconnect_after_24h(current_voice_client))

        except Exception as e:
            await message.channel.send(f"❌ Có lỗi khi kết nối voice: {e}")

TOKEN = os.environ.get("DISCORD_TOKEN")

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    if TOKEN:
        client.run(TOKEN)
    else:
        print("Lỗi: Chưa thiết lập DISCORD_TOKEN trong Environment Variables của Render!")

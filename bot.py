import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot đã online: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Lệnh AFK voice có cơ chế chống bị Discord tự kick
@bot.command()
async def afk(ctx, *, arg=None):
    if arg == "voice":
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            
            # Kết nối vào phòng
            voice_client = await channel.connect()
            await ctx.send(f"Đã treo voice bất tử tại: **{channel.name}**! 🎧")
            
            # Mẹo chống timeout: Phát một file âm thanh im lặng vô tận (hoặc stream rỗng)
            # Dùng nguồn audio vô tận từ FFmpeg tạo tín hiệu giả để Discord không bao giờ kick
            try:
                # Tạo một luồng im lặng ngầm liên tục
                ffmpeg_options = {
                    'options': '-f lavfi -i anullsrc=r=44100:cl=mono -acodec libopus'
                }
                source = discord.FFmpegPCMAudio('pipe:0', **ffmpeg_options) # Hoặc dùng trick phát source rỗng
            except:
                pass
            
        else:
            await ctx.send("Anh phải vào phòng voice trước đã nhé!")
    else:
        await ctx.send("Dùng cú pháp: `!afk voice`")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng! 👋")
    else:
        await ctx.send("Bot có đang ở trong voice đâu!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
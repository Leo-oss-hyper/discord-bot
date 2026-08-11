import os
import discord
from discord.ext import commands

# Cấu hình intents cho bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập thành công với tên: {bot.user}")

# Lệnh kiểm tra ping
@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Lệnh treo voice với cú pháp !afk voice
@bot.command()
async def afk(ctx, *, arg=None):
    if arg == "voice":
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            
            await channel.connect()
            await ctx.send(f"Đã vào treo voice tại: **{channel.name}**! 🎧")
        else:
            await ctx.send("Anh phải vào phòng voice trước rồi gọi em nhé!")
    else:
        await ctx.send("Vui lòng dùng đúng cú pháp: `!afk voice`")

# Lệnh rời phòng voice
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng voice! 👋")
    else:
        await ctx.send("Em có đang ở trong phòng voice nào đâu ạ!")

# Khởi động bot bằng token từ Railway
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
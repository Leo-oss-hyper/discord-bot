import os
import discord
from discord.ext import commands

# Cấu hình intents để bot đọc được tin nhắn
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Bot da dang nhap voi ten: {bot.user.name}')

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# Lấy token từ biến môi trường (sau này mình cài trên Railway)
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
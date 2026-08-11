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

# Lệnh AFK voice chính
@bot.command()
async def afk(ctx, *, arg=None):
    if arg == "voice":
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.disconnect()
            await channel.connect()
            await ctx.send(f"Đã treo voice tại: **{channel.name}**! 🎧")
        else:
            await ctx.send("Anh phải vào phòng voice trước đã nhé!")
    else:
        await ctx.send("Dùng cú pháp: `!afk voice`")

# Lệnh rời voice (khi nào chán mới gọi)
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng! 👋")
    else:
        await ctx.send("Bot có đang ở trong voice đâu!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
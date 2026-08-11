import os
import discord
from discord.ext import commands
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot đã đăng nhập thành công với tên: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# 1. Lệnh treo voice giữ chỗ
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

# 2. Lệnh phát nhạc hoặc kể chuyện từ YouTube (Đã fix lỗi chặn 403 bằng cơ chế giả lập)
@bot.command()
async def play(ctx, url: str):
    if not ctx.author.voice:
        return await ctx.send("Anh phải vào phòng voice trước đã nhé!")
    
    channel = ctx.author.voice.channel
    
    if not ctx.voice_client:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    # Cấu hình yt-dlp vượt tường lửa YouTube
    ytdl_options = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'impersonate': 'chrome',
        'cachedir': False
    }

    try:
        with yt_dlp.YoutubeDL(ytdl_options) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            title = info.get('title', 'Âm thanh')
    except Exception as e:
        return await ctx.send(f"YouTube đang chặn server, không lấy được link: `{e}`")

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -b:a 192k'
    }
    
    try:
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: print(f'Lỗi: {e}'))
        await ctx.send(f"Đang phát: **{title}** 🎶🎧")
    except Exception as e:
        await ctx.send(f"Lỗi phát âm thanh: `{e}`")

# 3. Lệnh dừng phát nhạc/truyện
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Đã dừng phát! ⏹️")
    else:
        await ctx.send("Em có đang phát gì đâu!")

# 4. Lệnh rời phòng voice (chỉ khi nào gọi lệnh này bot mới out)
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng voice! 👋")
    else:
        await ctx.send("Em có đang ở trong phòng voice nào đâu ạ!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
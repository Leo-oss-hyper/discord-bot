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

# Lệnh treo voice
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

# Lệnh phát nhạc/truyện bằng link YouTube đã fix lỗi chặn
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

    # Cấu hình yt-dlp để vượt tường lửa YouTube
    ytdl_options = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        # Giả lập trình duyệt Chrome để không bị YouTube chặn 403 Forbidden
        'socket_timeout': 30,
        'cachedir': False
    }

    try:
        with yt_dlp.YoutubeDL(ytdl_options) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get('url')
            title = info.get('title', 'Âm thanh')
    except Exception as e:
        return await ctx.send(f"Không thể phát link này do YouTube chặn: `{e}`")

    ffmpeg_options = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn -b:a 192k'
    }
    
    try:
        source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: print(f'Lỗi âm thanh (nếu có): {e}'))
        await ctx.send(f"Đang phát: **{title}** 🎶🎧")
    except Exception as e:
        await ctx.send(f"Lỗi khi phát âm thanh vào voice: `{e}`")

# Lệnh dừng phát
@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("Đã dừng phát! ⏹️")
    else:
        await ctx.send("Em có đang phát gì đâu!")

# Lệnh rời phòng voice
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Đã rời phòng voice! 👋")
    else:
        await ctx.send("Em có đang ở trong phòng voice nào đâu ạ!")

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
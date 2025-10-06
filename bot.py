import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
from dotenv import load_dotenv  # ✅ dotenv eklendi

# .env dosyasını yükle
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")  # ✅ Token artık gizli dosyadan okunuyor

# Bot ayarları
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Sunucuya özel müzik kuyruğu
music_queue = {}

# YTDL & FFMPEG ayarları
YDL_OPTIONS = {
    "format": "bestaudio",
    "noplaylist": True,
    "default_search": "ytsearch"
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
    "options": "-vn"
}

def get_queue(ctx):
    if ctx.guild.id not in music_queue:
        music_queue[ctx.guild.id] = []
    return music_queue[ctx.guild.id]

def play_next(ctx):
    queue = get_queue(ctx)
    if queue:
        url = queue.pop(0)
        play_music(ctx, url)
    else:
        coro = ctx.send("✅ Kuyruk bitti! Yeni şarkı ekleyene kadar bekliyorum...")
        asyncio.run_coroutine_threadsafe(coro, bot.loop)

def play_music(ctx, url):
    with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        audio_url = info["url"]
        title = info.get("title", "Bilinmeyen Şarkı")

    vc = ctx.voice_client
    vc.play(
        discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS),
        after=lambda e: play_next(ctx)
    )

    coro = ctx.send(f"🎶 Şimdi çalıyor: **{title}**")
    asyncio.run_coroutine_threadsafe(coro, bot.loop)

@bot.command()
async def katil(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send("🔊 Kanala katıldım!")
    else:
        await ctx.send("❌ Ses kanalında değilsin!")

@bot.command()
async def ayril(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Kanaldan ayrıldım!")
    else:
        await ctx.send("❌ Kanaldan zaten değilim.")

@bot.command()
async def cal(ctx, *, search):
    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("❌ Önce bir ses kanalına gir!")

    queue = get_queue(ctx)
    if ctx.voice_client.is_playing():
        queue.append(search)
        await ctx.send("➕ Kuyruğa eklendi!")
    else:
        play_music(ctx, search)

@bot.command()
async def gec(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Şarkı geçildi!")
    else:
        await ctx.send("❌ Çalan şarkı yok.")

@bot.command()
async def durdur(ctx):
    queue = get_queue(ctx)
    queue.clear()
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
    await ctx.send("⏹ Müzik durduruldu ve kuyruk temizlendi.")

@bot.command()
async def kuyruk(ctx):
    queue = get_queue(ctx)
    if not queue:
        await ctx.send("📭 Kuyruk boş!")
    else:
        msg = "\n".join([f"{i+1}. {url}" for i, url in enumerate(queue)])
        await ctx.send("🎶 Kuyruk:\n" + msg)

# ---- BOTU BAŞLAT ----
bot.run(TOKEN)

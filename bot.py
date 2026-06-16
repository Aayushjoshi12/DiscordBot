import discord
from discord.ext import commands
import random
import yt_dlp
import asyncio
from discord import PCMVolumeTransformer, FFmpegPCMAudio

TOKEN = "Your_token"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# -------------------------
# READY EVENT
# -------------------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# -------------------------
# BASIC COMMANDS
# -------------------------
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")


@bot.command()
async def move(ctx):
    if not ctx.author.voice:
        await ctx.send("Join a voice channel first!")
        return

    if not ctx.voice_client:
        await ctx.send("Bot is not connected to a voice channel.")
        return

    await ctx.voice_client.move_to(ctx.author.voice.channel)
    await ctx.send(f"Moved to {ctx.author.voice.channel.name}")

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="🎧 Music + Fun + AI Bot Help",
        description="All available commands in this bot:",
        color=discord.Color.green()
    )

    # BASIC
    embed.add_field(
        name="🟢 Basic Commands",
        value="""
`!hello` → Say hello  
`!ping` → Check bot latency  
`!roll` → Roll a dice
""",
        inline=False
    )

    # VOICE
    embed.add_field(
        name="🔊 Voice Commands",
        value="""
`!join` → Join your voice channel  
`!leave` → Leave voice channel
""",
        inline=False
    )

    # MUSIC
    embed.add_field(
        name="🎵 Music Commands",
        value="""
`!play <song name/url>` → Play music from YouTube  
`!pause` → Pause music  
`!resume` → Resume music  
`!skip` → Skip current song  
`!stop` → Stop music  
`!volume <0-200>` → Set volume  
`!queue_list` → Show queue
""",
        inline=False
    )

    # MODERATION
    embed.add_field(
        name="🛡️ Moderation",
        value="""
`!mute @user` → Timeout user  
`!unmute @user` → Remove timeout
""",
        inline=False
    )

    # FUN COMMANDS
    embed.add_field(
        name="😂 Fun Commands",
        value="""
`!joke @user` → Random online joke  
`!roast @user` → Roast a user  
`!nepaliroast @user` → Nepali style roast  
`!joke` → Joke about yourself
""",
        inline=False
    )

    # 🤖 AI COMMANDS
    embed.add_field(
        name="🤖 AI Commands",
        value="""
`!ai <message>` → Chat with AI (owner only)
""",
        inline=False
    )

    # ⚙️ SYSTEM COMMANDS
    embed.add_field(
        name="⚙️ System Commands",
        value="""
`!shutdown` → Turn bot offline (owner only)
`!offline` → Enable offline mode (if added)
`!online` → Disable offline mode (if added)
""",
        inline=False
    )

    # FOOTER
    embed.set_footer(text="Made by Aayush 🚀")

    await ctx.send(embed=embed)

@bot.command()
async def roll(ctx):
    await ctx.send(f"🎲 {random.randint(1,6)}")


@bot.command()
async def chatmute(ctx, member: discord.Member):

    if ctx.author.id != 966729792382701628:
        await ctx.send("❌ You cannot use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, name="Muted Chat")

    if role is None:
        await ctx.send("❌ 'Muted Chat' role not found.")
        return

    await member.add_roles(role)
    await ctx.send(f"💬🔇 {member.mention} has been chat muted.")

@bot.command()
    
async def chatunmute(ctx, member: discord.Member):

    if ctx.author.id != 966729792382701628:
        await ctx.send("❌ You cannot use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, name="Muted Chat")

    if role is None:
        await ctx.send("❌ 'Muted Chat' role not found.")
        return

    await member.remove_roles(role)
    await ctx.send(f"💬🔊 {member.mention} has been chat unmuted.")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong! 🏓")

# -------------------------
# VOICE CONNECT
# -------------------------
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel

        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()

        await ctx.send("🎧 Joined voice channel")
    else:
        await ctx.send("Join a voice channel first!")


import requests

OPENROUTER_API_KEY = "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"

@bot.command()
async def ai(ctx, *, message):

    # ONLY YOU CAN USE IT
    if ctx.author.id != 966729792382701628:
        await ctx.send("❌ You are not allowed to use AI command.")
        return

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a helpful Discord AI assistant."},
                    {"role": "user", "content": message}
                ]
            }
        )

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        await ctx.send(reply)

    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Left voice channel")

# -------------------------
# MUSIC SYSTEM (PRO FIXED)
# -------------------------
queue = []
volume_level = 0.5

def get_audio(url):
    ydl_opts = {
        'format': 'bestaudio',
        'noplaylist': True,
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url'], info.get('title', 'Unknown')

async def play_next(ctx):
    if len(queue) == 0:
        return

    url = queue.pop(0)
    voice = ctx.voice_client

    stream_url, title = await asyncio.to_thread(get_audio, url)

    source = discord.FFmpegPCMAudio(stream_url)

    def after_playing(error):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except:
            pass

    voice.play(source, after=after_playing)
    await ctx.send(f"🎵 Now playing: **{title}**")

@bot.command()
async def play(ctx, *, query):
    voice = ctx.voice_client

    if not voice:
        await ctx.send("I'm not in a voice channel!")
        return

    if voice.is_playing():
        await ctx.send("❌ Music is already playing. Use !stop or !skip first.")
        return

    ydl_opts = {
        'format': 'bestaudio',
        'default_search': 'ytsearch',
        'quiet': True
    }

    def get_audio():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)

            if 'entries' in info:
                info = info['entries'][0]

            return info['url'], info.get('title', 'Unknown Title')

    try:
        stream_url, title = await asyncio.to_thread(get_audio)
    except Exception as e:
        print(e)
        await ctx.send(f"Error: {e}")
        return

    source = PCMVolumeTransformer(
        FFmpegPCMAudio(
    stream_url,
    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
),
        volume=volume_level
    )

    voice.play(source)

    await ctx.send(f"🎵 Now playing: {title}")

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ Skipped")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        queue.clear()
        ctx.voice_client.stop()
        await ctx.send("⏹ Stopped music + cleared queue")

@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶ Resumed music")
    else:
        await ctx.send("Nothing is paused")

@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸ Paused music")
    else:
        await ctx.send("Nothing is playing")

@bot.command()
async def volume(ctx, value: int):
    global volume_level

    if value < 0 or value > 200:
        await ctx.send("Volume must be between 0 and 200")
        return

    volume_level = value / 100

    # If something is currently playing, update it live
    if ctx.voice_client and ctx.voice_client.source:
        ctx.voice_client.source.volume = volume_level

    await ctx.send(f"🔊 Volume set to {value}%")

@bot.command()
async def queue_list(ctx):
    if len(queue) == 0:
        await ctx.send("Queue is empty")
    else:
        msg = "\n".join([f"{i+1}. {u}" for i, u in enumerate(queue)])
        await ctx.send(f"📜 Queue:\n{msg}")

import aiohttp

import aiohttp
import random

import aiohttp
import random

@bot.command()
async def nepaliroast(ctx, member: discord.Member = None):

    if ctx.author.id != 966729792382701628:
        await ctx.send("❌ You are not allowed to use this command.")
        return

    if member is None:
        member = ctx.author

    url = "https://www.reddit.com/r/cleanjokes/top.json?limit=30&t=day"
    headers = {"User-agent": "Mozilla/5.0"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as r:
                data = await r.json()

        posts = data["data"]["children"]

        jokes = [
            post["data"]["title"]
            for post in posts
            if "data" in post and post["data"].get("title")
        ]

        if not jokes:
            raise Exception("No jokes found")

        joke = random.choice(jokes)

    except Exception as e:
        joke = "Nepali internet slow bhayo 😂 (fallback roast)"

    roasts = [
        "💀 system lag detected in brain",
        "😂 certified Nepali debugging failure",
        "🔥 talent loading… still at 1%",
        "🧠 brain.exe stopped working"
    ]

    await ctx.send(
        f"🔥 NEPALI INTERNET ROAST 🔥\n\n"
        f"{member.mention}\n\n"
        f"{joke}\n\n"
        f"{random.choice(roasts)}"
    )

import aiohttp
import random

import aiohttp
import random

@bot.command()
async def joke(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    async with aiohttp.ClientSession() as session:
        async with session.get("https://official-joke-api.appspot.com/random_joke") as r:
            data = await r.json()

    setup = data["setup"]
    punchline = data["punchline"]

    personalized_roasts = [
        f"{member.display_name} ले यो joke सुनेपछि confuse हुन्छ 😂",
        f"{member.display_name} को reaction: 'wait… what?' 🤔",
        f"{member.display_name} को brain: buffering... 99% 🧠",
        f"{member.display_name} लाई यो बुझ्न time लाग्छ 📦",
    ]

    await ctx.send(
        f"😂 {member.mention}\n\n"
        f"{setup}\n"
        f"||{punchline}||\n\n"
        f"{random.choice(personalized_roasts)}"
    )

import aiohttp
import random

@bot.command()
async def roast(ctx, member: discord.Member = None):

    # ONLY YOU CAN USE IT
    if ctx.author.id != 966729792382701628:
        await ctx.send("❌ You are not allowed to use this command.")
        return

    if member is None:
        member = ctx.author

    async with aiohttp.ClientSession() as session:
        async with session.get("https://official-joke-api.appspot.com/random_joke") as r:
            data = await r.json()

    setup = data["setup"]
    punchline = data["punchline"]

    roasts = [
        "skill issue detected 😭",
        "even Google can't find talent here 😂",
        "bro is on airplane mode in real life ✈️",
        "loading personality... still at 1% 🧠",
        "error 404: brain not found 💀"
    ]

    roast_line = random.choice(roasts)

    await ctx.send(
        f"🔥 ROAST ON {member.mention}\n\n"
        f"{setup}\n||{punchline}||\n\n"
        f"💀 {roast_line}"
    )


import datetime

import datetime

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    try:
        await member.timeout(None)  # removes timeout
        await ctx.send(f"🔊 Removed timeout for {member.mention}")
    except Exception as e:
        await ctx.send(f"❌ Failed to unmute: {e}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, time: int = 10):
    try:
        duration = datetime.timedelta(minutes=time)
        await member.timeout(duration)
        await ctx.send(f"🔇 Timed out {member.mention} for {time} minutes")
    except Exception as e:
        await ctx.send(f"❌ Failed to mute: {e}")

# -------------------------
# RUN BOT
# -------------------------
bot.run(TOKEN)

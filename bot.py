import discord
import os
from groq import Groq

# =========================
# EINSTELLUNGEN
# =========================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

ALLOWED_CHANNEL_ID = 1507649049602424976

# =========================
# DISCORD
# =========================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# GROQ
# =========================

groq = Groq(api_key=GROQ_KEY)

MODEL = "llama-3.3-70b-versatile"

# =========================
# CHAT MEMORY
# =========================

memory = []

# =========================
# KI
# =========================

def ask_ai(user_name, message):

    global memory

    messages = [
        {
            "role": "system",
            "content": """
Du bist Abu Olaf.

Du bist ein lockerer, freundlicher Discord-Bot.

Regeln:
- antworte auf deutsch
- schreibe klein
- antworte natürlich wie ein Mensch
- antworte meistens kurz
- nutze manchmal "bruder" oder "digga"
- sei lustig und freundlich
- wenn jemand fragt wer du bist, sag dass du abu olaf bist
- unterhalte dich normal mit den Leuten
"""
        }
    ]

    # Letzte Nachrichten
    messages.extend(memory[-10:])

    # Neue Nachricht
    messages.append({
        "role": "user",
        "content": f"{user_name}: {message}"
    })

    try:

        response = groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.8
        )

        answer = response.choices[0].message.content

        if not answer:
            return "bruder ich hab gerade keine antwort 😭"

        # User-Nachricht speichern
        memory.append({
            "role": "user",
            "content": f"{user_name}: {message}"
        })

        # KI-Antwort speichern
        memory.append({
            "role": "assistant",
            "content": answer
        })

        # Memory begrenzen
        if len(memory) > 20:
            memory = memory[-20:]

        return answer.strip()

    except Exception as e:

        print("❌ GROQ FEHLER:")
        print(repr(e))

        return "❌ die ki hat gerade einen fehler, bruder"


# =========================
# BOT ONLINE
# =========================

@client.event
async def on_ready():

    print("================================")
    print("✅ ABU OLAF IST ONLINE")
    print(f"🤖 Bot: {client.user}")
    print(f"📢 Channel: {ALLOWED_CHANNEL_ID}")
    print(f"🧠 Modell: {MODEL}")
    print("================================")


# =========================
# NACHRICHTEN
# =========================

@client.event
async def on_message(message):

    # Bot ignoriert sich selbst
    if message.author == client.user:
        return

    # Nur ein Channel
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    # Leere Nachricht ignorieren
    if not message.content.strip():
        return

    user_name = message.author.display_name
    user_message = message.content.strip()

    print(f"📩 {user_name}: {user_message}")

    # KI arbeitet
    async with message.channel.typing():

        answer = await __import__("asyncio").to_thread(
            ask_ai,
            user_name,
            user_message
        )

    # Antwort senden
    await message.channel.send(answer[:1900])

    print(f"🤖 Abu Olaf: {answer}")


# =========================
# START
# =========================

if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN fehlt!")

if not GROQ_KEY:
    print("❌ GROQ_KEY fehlt!")

if DISCORD_TOKEN and GROQ_KEY:

    client.run(DISCORD_TOKEN)

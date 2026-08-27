import discord
import os
import requests
import asyncio

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# =========================
# EIN CHANNEL
# =========================
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
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

# =========================
# MEMORY
# =========================
memory = []


# =========================
# KI
# =========================
def ask_ai(user_name, user_message):

    messages = [
        {
            "role": "system",
            "content": """
du bist abu olaf.

du bist ein lockerer und freundlicher discord bot.

regeln:
- antworte auf deutsch
- schreibe klein
- antworte natürlich
- antworte meistens kurz
- nutze manchmal bruder oder digga
- sei lustig und freundlich
- unterhalte dich normal mit den leuten
- wenn jemand fragt wer du bist, sag dass du abu olaf bist
"""
        }
    ]

    # Alte Nachrichten
    messages.extend(memory[-10:])

    # Neue Nachricht
    messages.append({
        "role": "user",
        "content": f"{user_name}: {user_message}"
    })

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.8
    }

    try:

        print("===================================")
        print("📨 NACHRICHT:", user_message)
        print("🤖 MODELL:", GROQ_MODEL)
        print("📡 Sende Anfrage an Groq...")
        print("===================================")

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        print("📊 GROQ STATUS:", response.status_code)
        print("📩 GROQ ANTWORT:", response.text)

        # =========================
        # ERFOLG
        # =========================
        if response.status_code == 200:

            result = response.json()

            answer = result["choices"][0]["message"]["content"]

            if not answer:
                print("❌ Groq hat leer geantwortet")
                return "bruder ich hab gerade keine antwort 😭"

            # Memory speichern
            memory.append({
                "role": "user",
                "content": f"{user_name}: {user_message}"
            })

            memory.append({
                "role": "assistant",
                "content": answer
            })

            # Memory begrenzen
            if len(memory) > 20:
                del memory[:-20]

            print("✅ KI ANTWORT:", answer)

            return answer.strip()

        # =========================
        # RATE LIMIT
        # =========================
        if response.status_code == 429:

            print("❌ GROQ RATE LIMIT:", response.text)

            return "⏳ kurz warten bruder, groq hat gerade zu viele anfragen"

        # =========================
        # ANDERE FEHLER
        # =========================

        try:
            error_data = response.json()

            error_message = error_data.get(
                "error",
                {}
            ).get(
                "message",
                response.text
            )

        except Exception:
            error_message = response.text

        print("❌ GROQ FEHLER:", error_message)

        return f"❌ groq fehler: {error_message}"

    except requests.exceptions.Timeout:

        print("❌ GROQ TIMEOUT")

        return "❌ groq antwortet gerade nicht, bruder"

    except Exception as e:

        print("❌ FEHLER:", repr(e))

        return "❌ fehler bei der ki"


# =========================
# BOT ONLINE
# =========================
@client.event
async def on_ready():

    print("===================================")
    print("✅ ABU OLAF IST ONLINE")
    print(f"🤖 {client.user}")
    print(f"🧠 MODELL: {GROQ_MODEL}")
    print(f"📢 CHANNEL: {ALLOWED_CHANNEL_ID}")
    print("===================================")

    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN fehlt!")

    if not GROQ_KEY:
        print("❌ GROQ_KEY fehlt!")


# =========================
# NACHRICHTEN
# =========================
@client.event
async def on_message(message):

    # Bot ignoriert sich selbst
    if message.author == client.user:
        return

    # Nur erlaubter Channel
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

        answer = await asyncio.to_thread(
            ask_ai,
            user_name,
            user_message
        )

    # Antwort senden
    try:

        await message.channel.send(
            answer[:1900]
        )

        print("✅ DISCORD ANTWORT GESENDET")

    except Exception as e:

        print("❌ DISCORD FEHLER:", repr(e))


# =========================
# START
# =========================
if not DISCORD_TOKEN:
    print("❌ DISCORD_TOKEN fehlt!")

if not GROQ_KEY:
    print("❌ GROQ_KEY fehlt!")

client.run(DISCORD_TOKEN)

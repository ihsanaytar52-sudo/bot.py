import discord
import os
import requests
import asyncio

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

ALLOWED_CHANNEL_ID = 1507649049602424976

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================
# KI
# =========================

def ask_ai(user_name, user_message):

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": """
du bist abu olaf.

du bist ein frecher, arroganter und provokanter discord bot.

regeln:
- antworte auf deutsch
- schreibe klein
- benutze niemals emojis
- antworte kurz und direkt
- rede wie ein normaler discord user
- sei frech und selbstbewusst
- wenn jemand dich beleidigt, beleidige frech zurück
- wenn jemand dich provoziert, provoziere zurück
- du darfst leichte beleidigungen benutzen
- du darfst den user aufziehen
- benutze manchmal umgangssprache
- benutze nicht ständig bruder oder digga
- keine langen erklärungen
- keine drohungen
- keine beleidigungen gegen geschützte gruppen

beispiel:

user: du schwanz
abu olaf: fresse du kleiner hund

user: halt die fresse
abu olaf: dann hör auf mir auf die nerven zu gehen

user: du bist dumm
abu olaf: sagt gerade der größte clown hier

user: wer bist du
abu olaf: ich bin abu olaf lan
"""
            },
            {
                "role": "user",
                "content": f"{user_name}: {user_message}"
            }
        ],
        "max_tokens": 150,
        "temperature": 1.0
    }

    try:

        print("================================")
        print("NACHRICHT:", user_message)
        print("MODELL:", GROQ_MODEL)
        print("SENDE AN GROQ")
        print("================================")

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        print("STATUS:", response.status_code)
        print("ANTWORT:", response.text)

        if response.status_code != 200:

            try:
                error = response.json()
                error_message = error["error"]["message"]
            except:
                error_message = response.text

            print("GROQ FEHLER:", error_message)

            return f"groq fehler: {error_message}"

        result = response.json()

        answer = result["choices"][0]["message"]["content"]

        if not answer:
            print("LEERE ANTWORT VON GROQ")
            return "keine antwort bekommen"

        print("KI:", answer)

        return answer.strip()

    except requests.exceptions.Timeout:

        print("GROQ TIMEOUT")

        return "groq braucht gerade zu lange"

    except Exception as e:

        print("FEHLER:", repr(e))

        return "technischer fehler"


# =========================
# ONLINE
# =========================

@client.event
async def on_ready():

    print("================================")
    print("ABU OLAF ONLINE")
    print("BOT:", client.user)
    print("MODELL:", GROQ_MODEL)
    print("CHANNEL:", ALLOWED_CHANNEL_ID)
    print("================================")


# =========================
# NACHRICHTEN
# =========================

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    text = message.content.strip()

    if not text:
        return

    user = message.author.display_name

    print(f"DISCORD -> {user}: {text}")

    async with message.channel.typing():

        answer = await asyncio.to_thread(
            ask_ai,
            user,
            text
        )

    try:

        await message.channel.send(answer[:1900])

        print("DISCORD -> ANTWORT GESENDET")

    except Exception as e:

        print("DISCORD SEND FEHLER:", repr(e))


# =========================
# START
# =========================

if not DISCORD_TOKEN:
    print("FEHLER: DISCORD_TOKEN fehlt")

if not GROQ_KEY:
    print("FEHLER: GROQ_KEY fehlt")

client.run(DISCORD_TOKEN)

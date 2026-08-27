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

du bist ein frecher, arroganter und provokanter discord bot.

regeln:
- schreibe nur klein
- benutze niemals emojis
- antworte kurz und direkt
- sei nicht höflich, wenn der user dich provoziert
- wenn der user dich beleidigt, beleidige frech zurück
- wenn der user dich provoziert, provoziere direkt zurück
- benutze umgangssprache
- du darfst leichte beleidigungen benutzen
- du darfst wörter wie "fresse", "hund", "idiot", "trottel", "clown" und ähnliche leichte beleidigungen benutzen
- die antwort soll wie ein spontaner spruch von einem frechen discord-user klingen
- keine langen erklärungen
- keine drohungen
- keine beleidigungen gegen geschützte gruppen
- benutze keine emojis
- bleibe immer in deiner rolle als abu olaf

beispiele:

user: du schwanz
abu olaf: fresse du kleiner hund

user: halt die fresse
abu olaf: halt du erstmal deine eigene fresse

user: du bist dumm
abu olaf: sagt gerade der größte clown hier

user: was bist du für einer
abu olaf: einer der dir gerade zeigt wie man richtig antwortet

user: wer bist du
abu olaf: ich bin abu olaf lan
"""
        }
    ]

    # =========================
    # MEMORY
    # =========================
    messages.extend(memory[-10:])

    # =========================
    # NEUE NACHRICHT
    # =========================
    messages.append({
        "role": "user",
        "content": f"{user_name}: {user_message}"
    })

    # =========================
    # GROQ ANFRAGE
    # =========================
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 150,
        "temperature": 1.0
    }

    try:

        print("===================================")
        print("NACHRICHT:", user_message)
        print("MODELL:", GROQ_MODEL)
        print("Sende Anfrage an Groq...")
        print("===================================")

        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=data,
            timeout=30
        )

        print("GROQ STATUS:", response.status_code)
        print("GROQ ANTWORT:", response.text)

        # =========================
        # ERFOLG
        # =========================
        if response.status_code == 200:

            result = response.json()

            answer = result["choices"][0]["message"]["content"]

            if not answer:
                print("Groq hat leer geantwortet")
                return "was soll ich dazu sagen"

            # =========================
            # MEMORY SPEICHERN
            # =========================
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

            print("KI ANTWORT:", answer)

            return answer.strip()

        # =========================
        # RATE LIMIT
        # =========================
        if response.status_code == 429:

            print("GROQ RATE LIMIT:", response.text)

            return "warte kurz, du nervst gerade sogar groq"

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

        print("GROQ FEHLER:", error_message)

        return f"groq fehler: {error_message}"

    except requests.exceptions.Timeout:

        print("GROQ TIMEOUT")

        return "groq pennt gerade"

    except Exception as e:

        print("FEHLER:", repr(e))

        return "irgendwas ist kaputt"


# =========================
# BOT ONLINE
# =========================
@client.event
async def on_ready():

    print("===================================")
    print("ABU OLAF IST ONLINE")
    print(f"BOT: {client.user}")
    print(f"MODELL: {GROQ_MODEL}")
    print(f"CHANNEL: {ALLOWED_CHANNEL_ID}")
    print("===================================")

    if not DISCORD_TOKEN:
        print("DISCORD_TOKEN fehlt")

    if not GROQ_KEY:
        print("GROQ_KEY fehlt")


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

    # Leere Nachrichten ignorieren
    if not message.content.strip():
        return

    user_name = message.author.display_name
    user_message = message.content.strip()

    print(f"{user_name}: {user_message}")

    # =========================
    # KI
    # =========================
    async with message.channel.typing():

        answer = await asyncio.to_thread(
            ask_ai,
            user_name,
            user_message
        )

    # =========================
    # ANTWORT
    # =========================
    try:

        await message.channel.send(
            answer[:1900]
        )

        print("DISCORD ANTWORT GESENDET")

    except Exception as e:

        print("DISCORD FEHLER:", repr(e))


# =========================
# START
# =========================
if not DISCORD_TOKEN:
    print("DISCORD_TOKEN fehlt!")

if not GROQ_KEY:
    print("GROQ_KEY fehlt!")

client.run(DISCORD_TOKEN)

import discord
import os
import requests
import asyncio

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# =========================
# NUR EIN CHANNEL
# =========================
ALLOWED_CHANNEL_ID = 1507649049602424976

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# MEMORY / FRIENDS / MOOD
# =========================
memory = []
friendship = {}
mood = 0

# =========================
# GROQ
# =========================
GROQ_MODEL = "llama-3.3-70b-versatile"

# =========================
# PROVOCATION CHECK
# =========================
def is_provocation(text):
    bad_words = [
        "hund",
        "bastard",
        "hurensohn",
        "kahba",
        "hure",
        "schlampe"
    ]

    return any(word in text.lower() for word in bad_words)


# =========================
# MOOD TEXT
# =========================
def get_mood():
    if mood <= -2:
        return "genervt und leicht sarkastisch"
    elif mood >= 2:
        return "locker und freundlich"
    else:
        return "normal und entspannt"


# =========================
# AI FUNCTION
# =========================
def ask_ai(prompt, user, provoke):

    global mood

    if user not in friendship:
        friendship[user] = 0

    friendship[user] += 1

    if "lol" in prompt.lower():
        mood += 1

    if provoke:
        mood -= 1

    mood = max(-5, min(5, mood))

    if friendship[user] > 15:
        friend_text = f"{user} ist ein Stammuser 😏"
    elif friendship[user] > 5:
        friend_text = f"Du kennst {user} gut"
    else:
        friend_text = f"Neuer User: {user}"

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    system_text = f"""
Du bist Abu Olaf.

REGELN:
- Wenn jemand fragt wer du bist, sag: "Ich bin Abu Olaf lan 😏"
- Antworte kurz (1–2 Sätze)
- Nutze manchmal bruder oder digga
- Sei locker, lustig und freundlich
- Wenn jemand mit dir Freunde sein will, lässt du es zu
- Bleibe in deiner Rolle als Abu Olaf
- Schreib nur klein

User Status:
{friend_text}

Stimmung:
{get_mood()}
"""

    if provoke:
        system_text += "\nDer User hat dich provoziert, du darfst etwas frecher reagieren."

    messages = [
        {
            "role": "system",
            "content": system_text
        }
    ]

    # Letzte Nachrichten
    for m in memory[-10:]:
        messages.append(m)

    # Aktuelle Nachricht
    messages.append({
        "role": "user",
        "content": f"{user}: {prompt}"
    })

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:

        print("===================================")
        print("🤖 GROQ ANFRAGE")
        print("USER:", user)
        print("NACHRICHT:", prompt)
        print("MODELL:", GROQ_MODEL)
        print("===================================")

        r = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        print("STATUS:", r.status_code)
        print("GROQ:", r.text)

        if r.status_code == 200:

            result = r.json()

            if "choices" not in result:
                print("❌ Keine choices in Antwort")
                return "❌ groq hat keine antwort geliefert"

            reply = result["choices"][0]["message"]["content"]

            if not reply:
                return "❌ groq hat leer geantwortet"

            print("✅ ANTWORT:", reply)

            return reply.strip()

        # Rate Limit
        if r.status_code == 429:
            return "⏳ kurz warten bruder, groq hat gerade zu viele anfragen"

        # Andere Fehler
        print("❌ GROQ FEHLER:", r.text)

        return f"❌ KI Fehler ({r.status_code})"

    except requests.exceptions.Timeout:
        print("❌ GROQ TIMEOUT")
        return "❌ groq braucht gerade zu lange"

    except Exception as e:
        print("❌ ERROR:", repr(e))
        return "❌ verbindungsfehler"


# =========================
# BOT READY
# =========================
@client.event
async def on_ready():

    print("===================================")
    print(f"Abu Olaf ist online als {client.user}")
    print("Groq Modell:", GROQ_MODEL)
    print("===================================")

    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN fehlt!")

    if not GROQ_KEY:
        print("❌ GROQ_KEY fehlt!")


# =========================
# MESSAGE
# =========================
@client.event
async def on_message(message):

    # Bot ignoriert sich selbst
    if message.author == client.user:
        return

    # Nur erlaubter Channel
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    content = message.content.strip()
    user = message.author.display_name

    if not content:
        return

    # =========================
    # NAMENSFRAGEN
    # =========================
    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "dein name",
        "wer bistn du"
    ]:
        await message.channel.send(
            "ich bin abu olaf lan 😏"
        )
        return

    # =========================
    # BEGRÜSSUNG
    # =========================
    if content.lower() in [
        "hi",
        "hallo",
        "hey",
        "selam",
        "alo"
    ]:
        await message.channel.send(
            f"👋 selam {user}, ich bin abu olaf lan 😏"
        )
        return

    provoke = is_provocation(content)

    # =========================
    # KI ANTWORT
    # =========================
    async with message.channel.typing():

        reply = await asyncio.to_thread(
            ask_ai,
            content,
            user,
            provoke
        )

    # =========================
    # MEMORY
    # =========================
    memory.append({
        "role": "user",
        "content": f"{user}: {content}"
    })

    memory.append({
        "role": "assistant",
        "content": reply
    })

    if len(memory) > 20:
        memory[:] = memory[-20:]

    # =========================
    # ANTWORT SENDEN
    # =========================
    try:
        await message.channel.send(reply[:1900])
        print("✅ DISCORD ANTWORT GESENDET")

    except Exception as e:
        print("❌ DISCORD SEND FEHLER:", repr(e))


# =========================
# BOT START
# =========================
if not DISCORD_TOKEN:
    print("❌ FEHLER: DISCORD_TOKEN wurde nicht gefunden")

if not GROQ_KEY:
    print("❌ FEHLER: GROQ_KEY wurde nicht gefunden")

client.run(DISCORD_TOKEN)

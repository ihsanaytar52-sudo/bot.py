import discord
import os
import requests

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
# GROQ MODEL PRÜFEN
# =========================
def get_groq_model():
    url = "https://api.groq.com/openai/v1/models"

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}"
    }

    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print("GROQ MODEL STATUS:", r.status_code)

        if r.status_code != 200:
            print("❌ GROQ MODEL FEHLER:", r.text)
            return None

        models = r.json().get("data", [])

        print("===================================")
        print("VERFÜGBARE GROQ MODELLE:")
        print("===================================")

        for model in models:
            model_id = model.get("id")
            print(model_id)

        print("===================================")

        # Bevorzugte Modelle
        preferred_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b"
        ]

        available_ids = [
            model.get("id")
            for model in models
        ]

        for model in preferred_models:
            if model in available_ids:
                print("✅ BENUTZTES MODELL:", model)
                return model

        if available_ids:
            print("✅ AUTOMATISCHES MODELL:", available_ids[0])
            return available_ids[0]

        print("❌ KEIN GROQ MODELL GEFUNDEN")
        return None

    except Exception as e:
        print("❌ MODEL CHECK FEHLER:", e)
        return None


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

    for m in memory[-10:]:
        messages.append(m)

    messages.append({
        "role": "user",
        "content": f"{user}: {prompt}"
    })

    model = get_groq_model()

    if not model:
        return "❌ ich konnte kein verfügbares groq modell finden"

    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        r = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20
        )

        print("STATUS:", r.status_code)
        print("ANTWORT VON GROQ:", r.text)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]

        else:
            return f"❌ KI Fehler ({r.status_code})"

    except Exception as e:
        print("ERROR:", e)
        return "❌ verbindungsfehler"


# =========================
# EVENTS
# =========================
@client.event
async def on_ready():

    print(f"Abu Olaf ist online als {client.user}")

    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN fehlt!")

    if not GROQ_KEY:
        print("❌ GROQ_KEY fehlt!")

    if GROQ_KEY:
        print("🔍 Prüfe verfügbare Groq Modelle...")
        get_groq_model()


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

    # Leere Nachrichten ignorieren
    if not content:
        return

    # Namensfragen
    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "dein name",
        "wer bistn du"
    ]:
        await message.channel.send("ich bin abu olaf lan 😏")
        return

    # Begrüßung
    if content.lower() in ["hi", "hallo", "hey", "selam"]:
        await message.channel.send(
            f"👋 selam {user}, ich bin abu olaf lan 😏"
        )
        return

    provoke = is_provocation(content)

    async with message.channel.typing():

        reply = ask_ai(content, user, provoke)

        # Nachricht speichern
        memory.append({
            "role": "user",
            "content": f"{user}: {content}"
        })

        # Antwort speichern
        memory.append({
            "role": "assistant",
            "content": reply
        })

        # Nur die letzten 20 Einträge behalten
        if len(memory) > 20:
            memory[:] = memory[-20:]

        await message.channel.send(reply[:1900])


# =========================
# BOT START
# =========================
if not DISCORD_TOKEN:
    print("❌ FEHLER: DISCORD_TOKEN wurde nicht gefunden")

if not GROQ_KEY:
    print("❌ FEHLER: GROQ_KEY wurde nicht gefunden")

client.run(DISCORD_TOKEN)

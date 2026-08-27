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

# Aktuelles Groq-Modell
GROQ_MODEL = None


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

        available_ids = []

        print("===================================")
        print("VERFÜGBARE GROQ MODELLE:")
        print("===================================")

        for model in models:
            model_id = model.get("id")

            if model_id:
                available_ids.append(model_id)
                print(model_id)

        print("===================================")

        # Bevorzugte Modelle
        preferred_models = [
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "llama-3.1-8b-instant"
        ]

        # Erst bevorzugte Modelle durchsuchen
        for model in preferred_models:

            if model in available_ids:

                print("✅ AUSGEWÄHLTES GROQ MODELL:", model)

                return model

        # Falls kein bevorzugtes Modell vorhanden ist
        if available_ids:

            model = available_ids[0]

            print("✅ AUTOMATISCH AUSGEWÄHLTES MODELL:", model)

            return model

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
    global GROQ_MODEL

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

    # Letzte Nachrichten merken
    for m in memory[-10:]:
        messages.append(m)

    messages.append({
        "role": "user",
        "content": f"{user}: {prompt}"
    })

    # =========================
    # MODELL HOLEN
    # =========================
    if not GROQ_MODEL:

        GROQ_MODEL = get_groq_model()

        if not GROQ_MODEL:
            return "❌ kein groq modell verfügbar"

    data = {
        "model": GROQ_MODEL,
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:

        print("🤖 BENUTZE MODELL:", GROQ_MODEL)
        print("📨 Sende Anfrage an Groq...")

        r = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=30
        )

        print("STATUS:", r.status_code)
        print("ANTWORT VON GROQ:", r.text)

        # =========================
        # ERFOLG
        # =========================
        if r.status_code == 200:

            result = r.json()

            reply = result["choices"][0]["message"]["content"]

            print("✅ GROQ ANTWORT ERHALTEN")

            return reply.strip()

        # =========================
        # MODELL NICHT VERFÜGBAR
        # =========================
        elif r.status_code == 404:

            print("❌ MODELL NICHT VERFÜGBAR:", GROQ_MODEL)

            # Neues Modell suchen
            new_model = get_groq_model()

            if new_model and new_model != GROQ_MODEL:

                print("🔄 WECHSEL VON:", GROQ_MODEL)
                print("➡️ NEUES MODELL:", new_model)

                GROQ_MODEL = new_model

                data["model"] = GROQ_MODEL

                r2 = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    timeout=30
                )

                print("ZWEITER STATUS:", r2.status_code)
                print("ZWEITE GROQ ANTWORT:", r2.text)

                if r2.status_code == 200:

                    result = r2.json()

                    return result["choices"][0]["message"]["content"].strip()

            return "❌ kein verfügbares groq modell"

        # =========================
        # ANDERE FEHLER
        # =========================
        else:

            print("❌ GROQ FEHLER:", r.text)

            return f"❌ KI Fehler ({r.status_code})"

    except Exception as e:

        print("❌ REQUEST ERROR:", e)

        return "❌ verbindungsfehler"


# =========================
# EVENTS
# =========================
@client.event
async def on_ready():

    global GROQ_MODEL

    print("===================================")
    print(f"Abu Olaf ist online als {client.user}")
    print("===================================")

    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN fehlt!")

    if not GROQ_KEY:
        print("❌ GROQ_KEY fehlt!")

    # Nur EINMAL beim Start prüfen
    if GROQ_KEY:

        print("🔍 Prüfe Groq Modelle...")

        GROQ_MODEL = get_groq_model()

        if GROQ_MODEL:

            print("===================================")
            print("✅ GROQ IST BEREIT")
            print("🤖 MODELL:", GROQ_MODEL)
            print("===================================")

        else:

            print("===================================")
            print("❌ KEIN GROQ MODELL VERFÜGBAR")
            print("===================================")


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
        "selam"
    ]:

        await message.channel.send(
            f"👋 selam {user}, ich bin abu olaf lan 😏"
        )

        return

    provoke = is_provocation(content)

    async with message.channel.typing():

        reply = ask_ai(
            content,
            user,
            provoke
        )

        # =========================
        # USER NACHRICHT SPEICHERN
        # =========================
        memory.append({
            "role": "user",
            "content": f"{user}: {content}"
        })

        # =========================
        # BOT ANTWORT SPEICHERN
        # =========================
        memory.append({
            "role": "assistant",
            "content": reply
        })

        # Nur letzte 20 Einträge
        if len(memory) > 20:

            memory[:] = memory[-20:]

        # Discord Nachrichtenlimit
        await message.channel.send(
            reply[:1900]
        )


# =========================
# BOT START
# =========================
if not DISCORD_TOKEN:

    print(
        "❌ FEHLER: DISCORD_TOKEN wurde nicht gefunden"
    )

if not GROQ_KEY:

    print(
        "❌ FEHLER: GROQ_KEY wurde nicht gefunden"
    )

client.run(DISCORD_TOKEN)

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

    # =========================
    # GROQ API
    # =========================
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    system_text = f"""
du bist abu olaf.

regeln:
- wenn jemand fragt wer du bist, sag: "ich bin abu olaf lan 😏"
- antworte kurz (1–2 sätze)
- nutze manchmal bruder oder digga
- sei locker, lustig und freundlich
- wenn jemand mit dir freunde sein will, lässt du es zu
- merke dir user aus dem chat
- erwähne den usernamen passend im gespräch
- bleibe in deiner rolle als abu olaf
- wenn jemand dich beleidigt, darfst du frech reagieren
- schreibe nur kleinbuchstaben
- keine unnötig langen antworten

user status:
{friend_text}

stimmung:
{get_mood()}
"""

    if provoke:
        system_text += "\nder user hat dich provoziert, du darfst etwas frecher reagieren."

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

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    # =========================
    # GROQ REQUEST
    # =========================
    try:

        if not GROQ_KEY:
            print("FEHLER: GROQ_KEY fehlt!")
            return "❌ groq key fehlt"

        r = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20
        )

        print("GROQ STATUS:", r.status_code)

        # Nur Fehlerdetails ausgeben, niemals den API-Key
        if r.status_code != 200:
            print("GROQ RESPONSE:", r.text[:1000])
            return f"❌ groq fehler {r.status_code}"

        result = r.json()

        if "choices" not in result or not result["choices"]:
            print("UNGÜLTIGE GROQ ANTWORT:", result)
            return "❌ ungültige ki antwort"

        return result["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        print("GROQ TIMEOUT")
        return "❌ groq antwortet nicht"

    except requests.exceptions.RequestException as e:
        print("GROQ REQUEST FEHLER:", e)
        return "❌ verbindungsfehler zur ki"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ fehler: {e}"

# =========================
# EVENTS
# =========================
@client.event
async def on_ready():
    print(f"Abu Olaf ist online als {client.user}")

    if not DISCORD_TOKEN:
        print("WARNUNG: DISCORD_TOKEN fehlt!")

    if not GROQ_KEY:
        print("WARNUNG: GROQ_KEY fehlt!")

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    content = message.content.strip()

    if not content:
        return

    user = message.author.display_name

    # =========================
    # NAMENSFRAGEN
    # =========================
    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "dein name",
        "wer bistn du"
    ]:
        await message.channel.send("ich bin abu olaf lan 😏")
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

    # =========================
    # PROVOKATION
    # =========================
    provoke = is_provocation(content)

    # =========================
    # KI
    # =========================
    try:
        reply = ask_ai(
            content,
            user,
            provoke
        )

    except Exception as e:
        print(f"KI-FEHLER: {e}")
        reply = "❌ fehler bei der ki"

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
    # DISCORD ANTWORT
    # =========================
    try:
        await message.channel.send(reply[:1900])

    except discord.HTTPException as e:
        print(f"SENDE-FEHLER: {e}")

# =========================
# START
# =========================
if not DISCORD_TOKEN:
    print("FEHLER: DISCORD_TOKEN ist nicht gesetzt!")

client.run(DISCORD_TOKEN)

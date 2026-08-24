import discord
import os
from groq import Groq

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

    # =========================
    # FRIENDSHIP
    # =========================
    if user not in friendship:
        friendship[user] = 0

    friendship[user] += 1

    # =========================
    # MOOD
    # =========================
    if "lol" in prompt.lower():
        mood += 1

    if provoke:
        mood -= 1

    mood = max(-5, min(5, mood))

    # =========================
    # USER STATUS
    # =========================
    if friendship[user] > 15:
        friend_text = f"{user} ist ein stammuser 😏"
    elif friendship[user] > 5:
        friend_text = f"du kennst {user} gut"
    else:
        friend_text = f"neuer user: {user}"

    # =========================
    # SYSTEM PROMPT
    # =========================
    system_text = f"""
du bist abu olaf.

REGELN:

- wenn jemand fragt wer du bist, sag:
  "ich bin abu olaf lan 😏"

- antworte kurz, meistens 1–2 sätze
- nutze manchmal "bruder" oder "digga"
- sei locker, lustig und freundlich
- wenn jemand mit dir freunde sein will, lässt du es zu
- merke dir user aus dem chat
- bleibe immer in deiner rolle als abu olaf
- schreibe nur kleinbuchstaben
- keine unnötig langen antworten
- antworte natürlich und nicht wie ein roboter

wenn jemand dich beleidigt:
- bei leichten beleidigungen bleibst du entspannt
- bei harten beleidigungen darfst du frech und sarkastisch antworten
- übertreibe es aber nicht

user status:
{friend_text}

stimmung:
{get_mood()}
"""

    if provoke:
        system_text += """
der user hat dich gerade provoziert.
du darfst etwas frecher und sarkastischer reagieren.
"""

    # =========================
    # MESSAGES
    # =========================
    messages = [
        {
            "role": "system",
            "content": system_text
        }
    ]

    # Letzte Nachrichten als Memory
    for m in memory[-10:]:
        messages.append(m)

    # Aktuelle Nachricht
    messages.append({
        "role": "user",
        "content": f"{user}: {prompt}"
    })

    # =========================
    # GROQ
    # =========================
    try:

        if not GROQ_KEY:
            print("❌ GROQ_KEY FEHLT!")
            return "❌ groq key fehlt"

        groq_client = Groq(
            api_key=GROQ_KEY
        )

        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages,
            max_tokens=120,
            temperature=0.9
        )

        print("GROQ: OK")

        if not completion.choices:
            print("❌ GROQ: KEINE CHOICES")
            return "❌ keine ki antwort"

        reply = completion.choices[0].message.content

        if not reply:
            print("❌ GROQ: LEERE ANTWORT")
            return "❌ leere ki antwort"

        return reply.strip()

    except Exception as e:
        print("❌ GROQ FEHLER:", repr(e))
        return "❌ groq fehler"


# =========================
# READY EVENT
# =========================
@client.event
async def on_ready():

    print("=================================")
    print(f"Abu Olaf ist online als {client.user}")
    print("=================================")

    if DISCORD_TOKEN:
        print("DISCORD_TOKEN: OK")
    else:
        print("DISCORD_TOKEN: FEHLT!")

    if GROQ_KEY:
        print("GROQ_KEY: OK")
    else:
        print("GROQ_KEY: FEHLT!")


# =========================
# MESSAGE EVENT
# =========================
@client.event
async def on_message(message):

    # Eigene Nachrichten ignorieren
    if message.author == client.user:
        return

    # Nur erlaubten Channel benutzen
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    content = message.content.strip()

    # Leere Nachrichten ignorieren
    if not content:
        return

    user = message.author.display_name

    # =========================
    # NAMENSFRAGEN
    # =========================
    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "wie heisst du",
        "dein name",
        "wer bistn du",
        "wer bist du?"
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
        "moin",
        "yo"
    ]:

        await message.channel.send(
            f"👋 selam {user}, ich bin abu olaf lan 😏"
        )

        return

    # =========================
    # PROVOCATION
    # =========================
    provoke = is_provocation(content)

    # =========================
    # KI ANTWORT
    # =========================
    try:

        reply = ask_ai(
            content,
            user,
            provoke
        )

    except Exception as e:

        print("❌ KI-FEHLER:", repr(e))

        reply = "❌ fehler bei der ki"

    # =========================
    # MEMORY USER
    # =========================
    memory.append({
        "role": "user",
        "content": f"{user}: {content}"
    })

    # =========================
    # MEMORY AI
    # =========================
    memory.append({
        "role": "assistant",
        "content": reply
    })

    # Memory begrenzen
    if len(memory) > 20:
        memory[:] = memory[-20:]

    # =========================
    # DISCORD SEND
    # =========================
    try:

        # Discord erlaubt maximal 2000 Zeichen
        await message.channel.send(
            reply[:1900]
        )

    except discord.HTTPException as e:

        print("❌ DISCORD SENDE-FEHLER:", repr(e))


# =========================
# START CHECK
# =========================
if not DISCORD_TOKEN:
    print("❌ FEHLER: DISCORD_TOKEN ist nicht gesetzt!")

if not GROQ_KEY:
    print("❌ FEHLER: GROQ_KEY ist nicht gesetzt!")


# =========================
# BOT START
# =========================
client.run(DISCORD_TOKEN)

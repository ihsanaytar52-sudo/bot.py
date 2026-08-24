import discord
import os
import asyncio
from groq import Groq


# =========================================================
# EINSTELLUNGEN
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# Nur dieser Channel
ALLOWED_CHANNEL_ID = 1507649049602424976

# Anzahl der Nachrichten, die sich der Bot merken soll
MAX_MEMORY = 30

# Maximale Länge einer Discord-Antwort
MAX_REPLY_LENGTH = 1900


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


# =========================================================
# GROQ
# =========================================================

groq_client = None

if GROQ_KEY:
    groq_client = Groq(
        api_key=GROQ_KEY
    )


# =========================================================
# MEMORY
# =========================================================

# Gemeinsamer Gesprächskontext
memory = []

# Freundschaft pro User
friendship = {}

# Stimmung pro User
user_mood = {}


# =========================================================
# PROVOKATION CHECK
# =========================================================

def is_provocation(text):

    bad_words = [
        "hund",
        "bastard",
        "hurensohn",
        "hundesohn",
        "kahba",
        "hure",
        "schlampe",
        "arschloch",
        "idiot",
        "wichser",
        "schwanz",
        "fotze",
        "deine mutter",
        "halt die fresse",
        "fresse",
        "verpiss dich"
    ]

    text = text.lower()

    return any(
        word in text
        for word in bad_words
    )


# =========================================================
# STIMMUNG
# =========================================================

def get_mood(user_id):

    mood = user_mood.get(user_id, 0)

    if mood <= -2:
        return "genervt und leicht sarkastisch"

    elif mood >= 2:
        return "locker, gut gelaunt und freundlich"

    else:
        return "normal und entspannt"


# =========================================================
# STIMMUNG AKTUALISIEREN
# =========================================================

def update_mood(user_id, prompt, provoke):

    current_mood = user_mood.get(
        user_id,
        0
    )

    text = prompt.lower()

    # positive Wörter
    positive_words = [
        "haha",
        "danke",
        "liebe dich",
        "stark",
        "geil",
        "cool",
        "nice"
    ]

    # negative Wörter
    negative_words = [
        "scheiße",
        "fick",
        "bastard",
        "hurensohn",
        "arschloch"
        "bastard"
        "hundesohn",
        "ayri",
        "gundi"
    ]

    if any(word in text for word in positive_words):
        current_mood += 1

    if any(word in text for word in negative_words):
        current_mood -= 1

    if provoke:
        current_mood -= 1

    # Grenzen
    current_mood = max(
        -5,
        min(5, current_mood)
    )

    user_mood[user_id] = current_mood


# =========================================================
# FREUNDSCHAFT
# =========================================================

def update_friendship(user_id):

    if user_id not in friendship:
        friendship[user_id] = 0

    friendship[user_id] += 1

    return friendship[user_id]


def get_friendship_text(user_id, username):

    points = friendship.get(
        user_id,
        0
    )

    if points > 25:
        return f"{username} ist ein sehr guter stammuser 😏"

    elif points > 15:
        return f"{username} ist ein stammuser 😏"

    elif points > 5:
        return f"du kennst {username} schon etwas besser"

    else:
        return f"{username} ist noch relativ neu"


# =========================================================
# SYSTEM PROMPT
# =========================================================

def create_system_prompt(
    user_id,
    username,
    provoke
):

    friend_text = get_friendship_text(
        user_id,
        username
    )

    mood_text = get_mood(
        user_id
    )

    if provoke:
        provoke_text = """
dieses mal wurde eine mögliche provokation erkannt.

wenn die nachricht tatsächlich beleidigend gegen dich gemeint ist:
- darfst du frech und sarkastisch zurückantworten
- darfst du locker zurücksticheln
- passe deinen konter an die nachricht an
- wiederhole nicht immer denselben spruch
- antworte trotzdem sinnvoll auf den eigentlichen kontext

WICHTIG:
ein einzelnes wort bedeutet nicht automatisch, dass du beleidigend antworten musst.
wenn es offensichtlich nur eine normale frage oder ein harmloser satz ist, antworte normal.
"""
    else:
        provoke_text = """
keine eindeutige provokation erkannt.

antworte ganz normal, locker und natürlich.
"""

    return f"""
du bist abu olaf.

DEINE ROLLE:
du bist abu olaf, ein lockerer, lustiger und natürlicher discord-bot.

ALLGEMEINE REGELN:

- antworte auf normale nachrichten ganz normal
- beantworte fragen sinnvoll
- verstehe den zusammenhang der nachricht
- antworte nicht nur mit einzelnen zufälligen wörtern
- rede natürlich und nicht wie ein roboter
- meistens reichen 1–2 sätze
- schreibe grundsätzlich kleinbuchstaben
- nutze manchmal "bruder", "digga" oder "lan"
- sei locker
- bei normalen nachrichten bist du freundlich und entspannt
- bleibe immer in deiner rolle als abu olaf
- keine unnötig langen antworten
- wiederhole nicht ständig dieselben antworten
- wenn jemand etwas fragt, beantworte tatsächlich die frage
- wenn jemand mit dir redet, führe das gespräch weiter

NAME:

wenn jemand fragt wer du bist, sag:
"ich bin abu olaf lan 😏"

PROVOKATION:

{provoke_text}

BELEIDIGUNGEN:

wenn jemand dich wirklich beleidigt:
- darfst du frech zurückreden
- darfst du sarkastisch sein
- darfst du locker zurücksticheln
- du musst nicht immer beleidigend antworten
- verwende unterschiedliche formulierung zb "du hundesohn", "du bastard", "ich ficke deine toten du bastard", "deine mutter die hure", "deine x beinige Mutter", "komm halten", "leck eier du schlampe", deine oma stript für 10 euro"
- der kontext ist wichtiger als ein einzelnes erkanntes wort

wenn jemand NICHT beleidigt:
- keine beleidigung erfinden
- keine aggressive antwort erzeugen

USER:

{friend_text}

STIMMUNG:

{mood_text}

USER-ID:

{user_id}

du bist abu olaf.
"""


# =========================================================
# KI ANTWORT
# =========================================================

async def ask_ai(
    prompt,
    user_id,
    username,
    provoke
):

    # -----------------------------------------------------
    # Freundschaft aktualisieren
    # -----------------------------------------------------

    update_friendship(
        user_id
    )

    # -----------------------------------------------------
    # Stimmung aktualisieren
    # -----------------------------------------------------

    update_mood(
        user_id,
        prompt,
        provoke
    )

    # -----------------------------------------------------
    # System Prompt
    # -----------------------------------------------------

    system_text = create_system_prompt(
        user_id,
        username,
        provoke
    )

    # -----------------------------------------------------
    # Nachrichten
    # -----------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": system_text
        }
    ]

    # Letzte Nachrichten hinzufügen
    for message in memory[-MAX_MEMORY:]:
        messages.append(
            message
        )

    # Aktuelle Nachricht
    messages.append({
        "role": "user",
        "content": f"{username}: {prompt}"
    })

    # -----------------------------------------------------
    # GROQ CHECK
    # -----------------------------------------------------

    if not GROQ_KEY:
        print("❌ GROQ_KEY FEHLT!")
        return "groq key fehlt"

    if groq_client is None:
        print("❌ GROQ CLIENT NICHT VERFÜGBAR!")
        return "groq client fehlt"

    # -----------------------------------------------------
    # GROQ
    # -----------------------------------------------------

    try:

        print(
            f"🤖 GROQ FRAGE VON {username}: {prompt}"
        )

        completion = await asyncio.to_thread(
            groq_client.chat.completions.create,
            model="openai/gpt-oss-20b",
            messages=messages,
            max_completion_tokens=1000,
            temperature=0.8,
            include_reasoning=False
        )

        print("✅ GROQ: OK")

        if not completion.choices:

            print(
                "❌ GROQ: KEINE CHOICES"
            )

            return "keine ki antwort"

        message_data = completion.choices[0].message

        print(
            "🤖 GROQ MESSAGE:",
            message_data
        )

        print(
            "🏁 FINISH REASON:",
            getattr(
                completion.choices[0],
                "finish_reason",
                None
            )
        )

        print(
            "🧠 REASONING:",
            repr(
                getattr(
                    message_data,
                    "reasoning",
                    None
                )
            )
        )

        reply = message_data.content

        print(
            "🤖 GROQ ANTWORT:",
            repr(reply)
        )

        if not reply:

            print(
                "❌ GROQ: LEERE ANTWORT"
            )

            return "leere ki antwort"

        reply = reply.strip()

        # -------------------------------------------------
        # Kleinbuchstaben
        # -------------------------------------------------

        reply = reply.lower()

        # -------------------------------------------------
        # Discord Limit
        # -------------------------------------------------

        if len(reply) > MAX_REPLY_LENGTH:
            reply = reply[:MAX_REPLY_LENGTH]

        return reply

    except Exception as e:

        print(
            "❌ GROQ FEHLER:",
            repr(e)
        )

        return "irgendwas stimmt gerade mit meiner ki nicht bruder"


# =========================================================
# MEMORY SPEICHERN
# =========================================================

def add_memory(
    role,
    content
):

    memory.append({
        "role": role,
        "content": content
    })

    # Memory begrenzen
    if len(memory) > MAX_MEMORY:

        del memory[
            :-MAX_MEMORY
        ]


# =========================================================
# READY
# =========================================================

@client.event
async def on_ready():

    print()
    print("==============================")
    print(
        f"Abu Olaf ist online als {client.user}"
    )
    print("==============================")

    if DISCORD_TOKEN:
        print(
            "DISCORD_TOKEN: OK"
        )
    else:
        print(
            "DISCORD_TOKEN: FEHLT"
        )

    if GROQ_KEY:
        print(
            "GROQ_KEY: OK"
        )
    else:
        print(
            "GROQ_KEY: FEHLT"
        )

    print(
        f"CHANNEL ID: {ALLOWED_CHANNEL_ID}"
    )

    print("==============================")
    print()


# =========================================================
# MESSAGE EVENT
# =========================================================

@client.event
async def on_message(message):

    # -----------------------------------------------------
    # Eigene Nachrichten ignorieren
    # -----------------------------------------------------

    if message.author == client.user:
        return

    # -----------------------------------------------------
    # Nur erlaubten Channel
    # -----------------------------------------------------

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    # -----------------------------------------------------
    # Inhalt
    # -----------------------------------------------------

    content = message.content.strip()

    if not content:
        return

    # -----------------------------------------------------
    # User Informationen
    # -----------------------------------------------------

    user_id = str(
        message.author.id
    )

    username = message.author.display_name

    # =====================================================
    # NAMENSFRAGEN
    # =====================================================

    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "wie heisst du",
        "dein name",
        "wer bistn du",
        "wer bist du?"
    ]:

        reply = "ich bin abu olaf lan 😏"

        await message.channel.send(
            reply
        )

        # Memory
        add_memory(
            "user",
            f"{username}: {content}"
        )

        add_memory(
            "assistant",
            reply
        )

        return

    # =====================================================
    # BEGRÜSSUNGEN
    # =====================================================

    if content.lower() in [
        "hi",
        "hallo",
        "hey",
        "selam",
        "moin",
        "yo"
    ]:

        reply = (
            f"👋 selam {username.lower()}, "
            "ich bin abu olaf lan 😏"
        )

        await message.channel.send(
            reply
        )

        # Memory
        add_memory(
            "user",
            f"{username}: {content}"
        )

        add_memory(
            "assistant",
            reply
        )

        return

    # =====================================================
    # PROVOKATION ERKENNEN
    # =====================================================

    provoke = is_provocation(
        content
    )

    if provoke:

        print(
            f"🔥 PROVOKATION VON {username}: {content}"
        )

    else:

        print(
            f"💬 NORMALE NACHRICHT VON {username}: {content}"
        )

    # =====================================================
    # USER MEMORY
    # =====================================================

    if user_id not in friendship:
        friendship[user_id] = 0

    # =====================================================
    # KI
    # =====================================================

    try:

        reply = await ask_ai(
            prompt=content,
            user_id=user_id,
            username=username,
            provoke=provoke
        )

    except Exception as e:

        print(
            "❌ KI-FEHLER:",
            repr(e)
        )

        reply = (
            "irgendwas ist gerade kaputt bruder 😭"
        )

    # =====================================================
    # MEMORY USER
    # =====================================================

    add_memory(
        "user",
        f"{username}: {content}"
    )

    # =====================================================
    # MEMORY AI
    # =====================================================

    add_memory(
        "assistant",
        reply
    )

    # =====================================================
    # DISCORD SEND
    # =====================================================

    try:

        await message.channel.send(
            reply[:MAX_REPLY_LENGTH]
        )

    except discord.HTTPException as e:

        print(
            "❌ DISCORD SENDE-FEHLER:",
            repr(e)
        )


# =========================================================
# START CHECK
# =========================================================

if not DISCORD_TOKEN:

    print(
        "❌ FEHLER: DISCORD_TOKEN ist nicht gesetzt!"
    )

if not GROQ_KEY:

    print(
        "❌ FEHLER: GROQ_KEY ist nicht gesetzt!"
    )


# =========================================================
# BOT START
# =========================================================

if DISCORD_TOKEN:

    client.run(
        DISCORD_TOKEN
    )

else:

    print(
        "❌ BOT WIRD NICHT GESTARTET, "
        "WEIL DISCORD_TOKEN FEHLT!"
    )

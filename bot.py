import os
import discord
from groq import Groq


# =========================================================
# KONFIGURATION
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# Nur dieser Channel darf mit Abu Olaf chatten
ALLOWED_CHANNEL_ID = 1507649049602424976

# Groq Modell
GROQ_MODEL = "llama-3.1-8b-instant"


# =========================================================
# PRÜFEN, OB KEYS VORHANDEN SIND
# =========================================================

if not DISCORD_TOKEN:
    raise SystemExit(
        "FEHLER: DISCORD_TOKEN fehlt in Railway Variables."
    )

if not GROQ_KEY:
    raise SystemExit(
        "FEHLER: GROQ_KEY fehlt in Railway Variables."
    )


# =========================================================
# GROQ
# =========================================================

groq_client = Groq(
    api_key=GROQ_KEY
)


# =========================================================
# DISCORD
# =========================================================

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(
    intents=intents
)


# =========================================================
# MEMORY
# =========================================================

memory = []

# Freundschaft pro User
friendship = {}

# Stimmung
mood = 0


# =========================================================
# PROVOKATION
# =========================================================

def is_provocation(text):

    bad_words = [
        "hund",
        "bastard",
        "hurensohn",
        "kahba",
        "hure",
        "schlampe",
        "schwanz",
        "schwanzlutscher",
        "hundesohn"
    ]

    text = text.lower()

    return any(
        word in text
        for word in bad_words
    )


# =========================================================
# MOOD
# =========================================================

def get_mood():

    if mood <= -2:
        return "genervt und leicht sarkastisch"

    elif mood >= 2:
        return "locker und freundlich"

    return "normal und entspannt"


# =========================================================
# KI ANFRAGE
# =========================================================

def ask_ai(prompt, user, provoke):

    global mood

    # -----------------------------------------------------
    # USER ANLEGEN
    # -----------------------------------------------------

    if user not in friendship:
        friendship[user] = 0

    friendship[user] += 1


    # -----------------------------------------------------
    # STIMMUNG
    # -----------------------------------------------------

    if "lol" in prompt.lower():
        mood += 1

    if provoke:
        mood -= 1

    mood = max(
        -5,
        min(5, mood)
    )


    # -----------------------------------------------------
    # FREUNDSCHAFT
    # -----------------------------------------------------

    if friendship[user] > 15:

        friend_text = (
            f"{user} ist ein Stammuser 😏"
        )

    elif friendship[user] > 5:

        friend_text = (
            f"Du kennst {user} schon etwas"
        )

    else:

        friend_text = (
            f"{user} ist noch relativ neu"
        )


    # -----------------------------------------------------
    # SYSTEM PROMPT
    # -----------------------------------------------------

    system_text = f"""
du bist abu olaf.

deine regeln:

- du heißt abu olaf
- wenn jemand fragt wer du bist, sag dass du abu olaf bist
- antworte normalerweise kurz mit 1 bis 3 sätzen
- schreibe ausschließlich kleinbuchstaben
- sei locker, lustig und direkt
- benutze manchmal "bruder", "digga" oder "lan"
- du darfst emojis benutzen
- wenn jemand freundlich ist, sei freundlich
- wenn jemand mit dir freunde sein will, kannst du ihn als freund akzeptieren
- merke dir den verlauf des chats
- bleibe immer in deiner rolle als abu olaf
- bei normalen beleidigungen darfst du frech zurückantworten
- übertreibe aber nicht
- keine langen texte
- keine großschreibung

aktueller user:
{user}

user-status:
{friend_text}

deine aktuelle stimmung:
{get_mood()}
"""


    # -----------------------------------------------------
    # PROVOKATION
    # -----------------------------------------------------

    if provoke:

        system_text += """
der user hat dich provoziert.

du darfst etwas frecher und sarkastischer antworten.
bleibe aber locker und übertreibe nicht.
"""


    # -----------------------------------------------------
    # NACHRICHTEN
    # -----------------------------------------------------

    messages = [
        {
            "role": "system",
            "content": system_text
        }
    ]


    # Letzte Nachrichten aus Memory
    for m in memory[-10:]:

        messages.append(m)


    # Aktuelle Nachricht
    messages.append(
        {
            "role": "user",
            "content": f"{user}: {prompt}"
        }
    )


    # -----------------------------------------------------
    # GROQ
    # -----------------------------------------------------

    try:

        print(
            f"KI Anfrage von {user}: {prompt}"
        )

        completion = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=120,
            temperature=0.9
        )


        # Antwort holen
        reply = completion.choices[0].message.content


        if not reply:

            print(
                "GROQ FEHLER: leere Antwort"
            )

            return "bruder ich hab gerade nichts zu sagen 😭"


        # -------------------------------------------------
        # KLEINSCHREIBUNG
        # -------------------------------------------------

        reply = reply.lower().strip()


        print(
            f"KI Antwort: {reply}"
        )


        return reply


    except Exception as e:

        print(
            "========================================"
        )

        print(
            "GROQ FEHLER:"
        )

        print(
            repr(e)
        )

        print(
            "========================================"
        )


        return (
            "bruder meine ki hat gerade kurz schluckauf 😭"
        )


# =========================================================
# BOT READY
# =========================================================

@client.event
async def on_ready():

    print(
        "========================================"
    )

    print(
        f"abu olaf ist online als {client.user}"
    )

    print(
        f"groq modell: {GROQ_MODEL}"
    )

    print(
        f"chat channel: {ALLOWED_CHANNEL_ID}"
    )

    print(
        "========================================"
    )


# =========================================================
# NACHRICHTEN
# =========================================================

@client.event
async def on_message(message):

    # eigene Nachrichten ignorieren
    if message.author == client.user:
        return


    # andere bots ignorieren
    if message.author.bot:
        return


    # nur erlaubter channel
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return


    # Nachricht
    content = message.content.strip()


    # leere Nachricht
    if not content:
        return


    # User Name
    user = message.author.display_name


    print(
        f"Discord Nachricht von {user}: {content}"
    )


    # =====================================================
    # NAMENSFRAGEN
    # =====================================================

    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "wie heisst du",
        "dein name",
        "wer bistn du"
    ]:

        await message.channel.send(
            "ich bin abu olaf lan 😏"
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
        "servus"
    ]:

        await message.channel.send(
            f"selam {user.lower()}, ich bin abu olaf lan 😏"
        )

        return


    # =====================================================
    # PROVOKATION
    # =====================================================

    provoke = is_provocation(
        content
    )


    # =====================================================
    # KI
    # =====================================================

    reply = ask_ai(
        content,
        user,
        provoke
    )


    # =====================================================
    # MEMORY
    # =====================================================

    memory.append(
        {
            "role": "user",
            "content": f"{user}: {content}"
        }
    )


    memory.append(
        {
            "role": "assistant",
            "content": reply
        }
    )


    # Memory begrenzen
    if len(memory) > 20:

        memory[:] = memory[-20:]


    # =====================================================
    # DISCORD ANTWORT
    # =====================================================

    try:

        await message.channel.send(
            reply[:1900]
        )

    except discord.HTTPException as e:

        print(
            f"Discord Sende-Fehler: {e}"
        )


# =========================================================
# START
# =========================================================

print(
    "abu olaf wird gestartet..."
)


client.run(
    DISCORD_TOKEN
)

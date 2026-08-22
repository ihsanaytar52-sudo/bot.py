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

# AKTUELLES GROQ MODELL
GROQ_MODEL = "openai/gpt-oss-20b"


# =========================================================
# START-CHECKS
# =========================================================

if not DISCORD_TOKEN:
    raise SystemExit(
        "FEHLER: DISCORD_TOKEN fehlt in Railway."
    )

if not GROQ_KEY:
    raise SystemExit(
        "FEHLER: GROQ_KEY fehlt in Railway."
    )


# =========================================================
# GROQ CLIENT
# =========================================================

try:

    groq_client = Groq(
        api_key=GROQ_KEY
    )

    print("Groq Client wurde erfolgreich erstellt.")

except Exception as e:

    print("========================================")
    print("FEHLER BEIM ERSTELLEN DES GROQ CLIENTS")
    print("FEHLERTYP:", type(e).__name__)
    print("FEHLER:", str(e))
    print("========================================")

    raise


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

friendship = {}

mood = 0


# =========================================================
# BELEIDIGUNGS-ANTWORTEN
# =========================================================

def get_insult_reply():

    replies = [
        "halt die fresse bruder 😭",
        "redest du gerade mit mir so lan? 😭",
        "pass mal auf wie du mit abu olaf redest 😭",
        "du hast ja mut heute bruder 😂",
        "mach mal langsam bevor ich sauer werde 😭",
        "was ist denn mit dir los bruder 😂",
        "du bist heute aber frech unterwegs",
        "komm beruhig dich mal wieder digga 😭",
        "so redest du mit deiner familie, nicht mit mir 😂",
        "bruder respekt ist wohl heute im urlaub",
        "was laberst du da eigentlich 😭",
        "du hast abu olaf provoziert, selber schuld 😂"
    ]

    import random

    return random.choice(replies)


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
        "hundesohn",
        "wichser",
        "arschloch"
    ]

    text = text.lower()

    for word in bad_words:

        if word in text:
            return True

    return False


# =========================================================
# NACHRICHTEN
# =========================================================

@client.event
async def on_message(message):

    # eigenen Bot ignorieren
    if message.author == client.user:
        return

    # andere Bots ignorieren
    if message.author.bot:
        return

    # nur erlaubter Channel
    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    content = message.content.strip()

    if not content:
        return

    user = message.author.display_name

    print(
        f"DISCORD NACHRICHT | {user}: {content}"
    )


    # =====================================================
    # BELEIDIGUNG DIREKT ERKENNEN
    # =====================================================

    if is_provocation(content):

        reply = get_insult_reply()

        print(
            f"PROVOKATION ERKANNT | ANTWORT: {reply}"
        )

        await message.channel.send(
            reply
        )

        return


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
    # KI
    # =====================================================

    reply = ask_ai(
        content,
        user,
        False
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


    if len(memory) > 20:

        memory[:] = memory[-20:]


    # =====================================================
    # ANTWORT SENDEN
    # =====================================================

    try:

        await message.channel.send(
            reply[:1900]
        )

    except discord.HTTPException as e:

        print(
            "DISCORD SEND FEHLER:",
            str(e)
        )

# =========================================================
# START
# =========================================================

print("")
print("========================================")
print("ABU OLAF WIRD GESTARTET")
print("========================================")


try:

    client.run(
        DISCORD_TOKEN
    )


except Exception as e:

    print("")
    print("########################################")
    print("########### BOT START FEHLER ###########")
    print("########################################")

    print(
        "FEHLERTYP:",
        type(e).__name__
    )

    print(
        "FEHLER:",
        str(e)
    )

    print("########################################")

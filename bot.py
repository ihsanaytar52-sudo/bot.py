import os
import random
import discord
from groq import Groq


# =========================================================
# KONFIGURATION
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

ALLOWED_CHANNEL_ID = 1507649049602424976

# aktuelles groq modell
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
# GROQ
# =========================================================

try:

    groq_client = Groq(
        api_key=GROQ_KEY
    )

    print("Groq Client wurde erfolgreich erstellt.")

except Exception as e:

    print("========================================")
    print("GROQ CLIENT FEHLER")
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
# BELEIDIGUNGEN ERKENNEN
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
# BELEIDIGUNGS-ANTWORTEN
# =========================================================

def get_insult_reply():

    replies = [

        "halt mal die fresse bruder ",

        "pass mal auf wie du mit abu olaf redest ",

        "du bist heute aber mutig unterwegs bruder ",

        "deine Mutter ",

        "du kleiner hurensohn ",

        "du schwanzlutscher ",

        "du pic ",

        "ich ficke deine mutter ",

        "deine Vater ",

        "du schlampe ",

        "du hundeoshn",

        "du kahba "
    ]

    return random.choice(
        replies
    )


# =========================================================
# STIMMUNG
# =========================================================

def get_mood():

    if mood <= -2:

        return "genervt und leicht sarkastisch"

    elif mood >= 2:

        return "locker und freundlich"

    return "normal und entspannt"


# =========================================================
# KI FUNKTION
# =========================================================

def ask_ai(prompt, user, provoke=False):

    global mood


    # -----------------------------------------------------
    # USER SPEICHERN
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
            f"{user} ist ein stammuser 😏"
        )

    elif friendship[user] > 5:

        friend_text = (
            f"du kennst {user} schon etwas"
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

regeln:

- du heißt abu olaf
- wenn jemand fragt wer du bist, sag dass du abu olaf bist
- antworte kurz
- normalerweise 1 bis 3 sätze
- schreibe nur kleinbuchstaben
- sei locker
- sei lustig
- sei freundlich
- benutze manchmal bruder, digga oder lan
- du darfst emojis benutzen
- bleibe immer in deiner rolle als abu olaf
- merke dir den verlauf des chats
- wenn jemand freundlich ist, sei freundlich
- wenn jemand mit dir freunde sein will, kannst du ihn als freund akzeptieren
- keine langen texte
- keine großschreibung

aktueller user:

{user}

user-status:

{friend_text}

stimmung:

{get_mood()}
"""


    # -----------------------------------------------------
    # CHAT HISTORY
    # -----------------------------------------------------

    messages = [

        {
            "role": "system",
            "content": system_text
        }

    ]


    for m in memory[-10:]:

        messages.append(m)


    messages.append(

        {
            "role": "user",
            "content": f"{user}: {prompt}"
        }

    )


    # =====================================================
    # GROQ ANFRAGE
    # =====================================================

    try:

        print("")
        print("========================================")
        print("GROQ ANFRAGE")
        print("USER:", user)
        print("NACHRICHT:", prompt)
        print("MODELL:", GROQ_MODEL)
        print("========================================")


        completion = groq_client.chat.completions.create(

            model=GROQ_MODEL,

            messages=messages,

            max_tokens=150,

            temperature=0.9

        )


        # -------------------------------------------------
        # ANTWORT PRÜFEN
        # -------------------------------------------------

        if not completion.choices:

            print(
                "GROQ FEHLER: keine choices."
            )

            return (
                "bruder ich hab gerade keine antwort 😭"
            )


        reply = (
            completion
            .choices[0]
            .message
            .content
        )


        if not reply:

            print(
                "GROQ FEHLER: leere antwort."
            )

            return (
                "bruder ich hab gerade nichts zu sagen 😭"
            )


        # -------------------------------------------------
        # KLEINSCHREIBUNG
        # -------------------------------------------------

        reply = reply.lower().strip()


        print("GROQ ANTWORT:")
        print(reply)

        print("========================================")
        print("")


        return reply


    # =====================================================
    # GROQ FEHLER
    # =====================================================

    except Exception as e:

        print("")
        print("########################################")
        print("########### GROQ FEHLER ################")
        print("########################################")

        print(
            "FEHLERTYP:",
            type(e).__name__
        )

        print(
            "FEHLER:",
            str(e)
        )

        print(
            "MODELL:",
            GROQ_MODEL
        )

        print(
            "USER:",
            user
        )

        print(
            "NACHRICHT:",
            prompt
        )

        print("########################################")
        print("######### ENDE GROQ FEHLER ############")
        print("########################################")
        print("")


        return (
            "bruder meine ki hat gerade kurz schluckauf 😭"
        )


# =========================================================
# BOT ONLINE
# =========================================================

@client.event
async def on_ready():

    print("")
    print("========================================")
    print("ABU OLAF IST ONLINE")
    print("========================================")

    print(
        "BOT:",
        client.user
    )

    print(
        "BOT ID:",
        client.user.id
    )

    print(
        "GROQ MODELL:",
        GROQ_MODEL
    )

    print(
        "ERLAUBTER CHANNEL:",
        ALLOWED_CHANNEL_ID
    )

    print("========================================")
    print("")


# =========================================================
# NACHRICHTEN
# =========================================================

@client.event
async def on_message(message):

    # -----------------------------------------------------
    # BOT IGNORIEREN
    # -----------------------------------------------------

    if message.author == client.user:

        return


    # -----------------------------------------------------
    # ANDERE BOTS IGNORIEREN
    # -----------------------------------------------------

    if message.author.bot:

        return


    # -----------------------------------------------------
    # NUR ERLAUBTER CHANNEL
    # -----------------------------------------------------

    if message.channel.id != ALLOWED_CHANNEL_ID:

        return


    # -----------------------------------------------------
    # NACHRICHT
    # -----------------------------------------------------

    content = message.content.strip()


    if not content:

        return


    user = message.author.display_name


    print(
        f"DISCORD NACHRICHT | {user}: {content}"
    )


    # =====================================================
    # BELEIDIGUNG
    # =====================================================

    if is_provocation(content):

        reply = get_insult_reply()


        print(
            "PROVOKATION ERKANNT"
        )

        print(
            "ANTWORT:",
            reply
        )


        await message.channel.send(
            reply
        )


        # Memory ebenfalls speichern

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

            f"selam {user.lower()}, "
            f"ich bin abu olaf lan 😏"

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


    # maximal 20 einträge

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

        print("")
        print("========================================")
        print("DISCORD SEND FEHLER")
        print("FEHLERTYP:", type(e).__name__)
        print("FEHLER:", str(e))
        print("========================================")
        print("")


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

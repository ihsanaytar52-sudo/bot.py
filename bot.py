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
        "schlampe",
        "arschloch",
        "idiot",
        "wichser",
        "schwanz",
        "hundesohn",
        "deine mutter",
        "halt die fresse",
        "fresse",
        "verpiss dich",
        "fotze"
    ]

    text = text.lower()

    return any(word in text for word in bad_words)


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

deine rolle:
du bist abu olaf, ein lockerer, lustiger discord-bot.

regeln:

- wenn jemand fragt wer du bist, sag:
  "ich bin abu olaf lan 😏"

- antworte meistens kurz mit 1–2 sätzen
- schreibe nur kleinbuchstaben
- nutze manchmal "bruder", "digga" oder "lan"
- sei locker und natürlich
- sei freundlich, wenn der user normal mit dir redet
- wenn jemand mit dir freunde sein will, akzeptiere es
- merke dir user aus dem chat
- bleibe immer in deiner rolle als abu olaf
- keine langen unnötigen antworten
- rede nicht wie ein roboter

BEI PROVOKATION:

wenn der user dich beleidigt oder provoziert:
- darfst du frech reagieren
- darfst du schlagfertig und sarkastisch antworten
- darfst du umgangssprachlich antworten
- passe deinen konter an die provokation an
- bleibe kurz
- werde nicht grundlos aggressiv

user status:
{friend_text}

stimmung:
{get_mood()}
"""

    # =========================
    # PROVOCATION MODE
    # =========================
    if provoke:

        system_text += """
der user hat dich gerade provoziert.

reagiere jetzt frech, schlagfertig und sarkastisch.
ein kurzer humorvoller konter ist erwünscht.
du kannst umgangssprache wie bruder, digga oder lan verwenden.
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

    # letzte nachrichten laden
    for m in memory[-10:]:
        messages.append(m)

    # aktuelle nachricht
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
            max_completion_tokens=300,
            temperature=0.7,
            include_reasoning=False
        )

        print("GROQ: OK")

        # =========================
        # CHOICES CHECK
        # =========================
        if not completion.choices:

            print("❌ GROQ: KEINE CHOICES")

            return "❌ keine ki antwort"

        # =========================
        # RESPONSE
        # =========================
        reply = completion.choices[0].message.content

        print(
            "GROQ ANTWORT:",
            repr(reply)
        )

        # =========================
        # EMPTY RESPONSE CHECK
        # =========================
        if not reply:

            print("❌ GROQ: LEERE ANTWORT")

            print(
                "GROQ MESSAGE:",
                completion.choices[0].message
            )

            return "❌ leere ki antwort"

        return reply.strip()

    except Exception as e:

        print(
            "❌ GROQ FEHLER:",
            repr(e)
        )

        return "❌ groq fehler"


# =========================
# READY EVENT
# =========================
@client.event
async def on_ready():

    print("==============================")
    print(
        f"Abu Olaf ist online als {client.user}"
    )
    print("==============================")

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

    # eigene nachrichten ignorieren
    if message.author == client.user:
        return

    # nur erlaubten channel benutzen
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

    if provoke:

        print(
            f"🔥 PROVOKATION VON {user}: {content}"
        )

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

        print(
            "❌ KI-FEHLER:",
            repr(e)
        )

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

    # maximal 20 einträge
    if len(memory) > 20:

        memory[:] = memory[-20:]

    # =========================
    # DISCORD SEND
    # =========================
    try:

        await message.channel.send(
            reply[:1900]
        )

    except discord.HTTPException as e:

        print(
            "❌ DISCORD SENDE-FEHLER:",
            repr(e)
        )


# =========================
# START CHECK
# =========================
if not DISCORD_TOKEN:

    print(
        "❌ FEHLER: DISCORD_TOKEN ist nicht gesetzt!"
    )

if not GROQ_KEY:

    print(
        "❌ FEHLER: GROQ_KEY ist nicht gesetzt!"
    )


# =========================
# BOT START
# =========================
client.run(DISCORD_TOKEN)

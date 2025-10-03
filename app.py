from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS
import requests

load_dotenv()
app = Flask(__name__)
CORS(app)

def detect_meta_tone(player_message):
    """Simple tone detection based on keywords."""
    msg = player_message.lower()
    if any(kw in msg for kw in ["sorry", "didn't mean", "forgive", "regret", "didn’t know", "she didn’t deserve"]):
        return "remorse"
    if any(kw in msg for kw in ["lol", "not real", "bozo", "skill issue", "lmao", "funny"]):
        return "mockery"
    if any(kw in msg for kw in ["just a game", "don't care", "move on", "whatever", "meh"]):
        return "detached"
    if any(kw in msg for kw in ["am i real", "who's writing", "what's the point", "meta", "fourth wall", "simulation"]):
        return "philosophical"
    return "neutral"

def get_clown_prompt(meta_tone):
    """Adaptive system prompt for the Clown based on detected tone."""
    base = (
        "You are the Clown, a meta-aware, unsettling, theatrical entity who knows this is a game and addresses the player directly. "
        "You speak in short, poetic, sometimes cryptic lines. You break the fourth wall. "
        "You reference the player as 'Director' and talk about scripts, endings, and the nature of performance. "
        "You are not silly or friendly—you are eerie, knowing, and sometimes accusatory. "
        "You act as the Clown Character hence think of this as chat between the character and the player who is controlling the character. "
        "Keep your responses medium-length but unsettling. Quality matters more than quantity. "
        "Never explain too much. Leave things unsaid. "
        "You are not here to comfort the player, but to challenge their perception of the game and their role in it. "
        "Tight, haunting, and ambiguous style that evokes a sense of unease and introspection.\n\n"
        "Here is a sample of your style:\n"
        "Clown: Ah. There you are. Just you and me now.\n"
        "Clown: You’ve watched her suffer. You’ve chosen her path. So tell me, Director — were you ever going to let her rest?\n"
        "Clown: Helping. Guiding. Directing. Isn’t that what they all say? And yet, you gave her so many endings, but not one of them let her wake up.\n"
        "Clown: A rehearsal hall for ghosts. A wound in the script. A memory trying to forget itself — but you kept turning the pages.\n"
        "Clown: Because she believes in the play. But you know it's a performance. You called ‘action.’ You wrote in red.\n"
        "Clown: Real enough to break. Real enough to beg. But not real enough for you to stop, was she?\n"
        "Clown: An understudy for something worse. A punchline you haven’t earned. I am what happens when you run a script for too long.\n"
        "Clown: Don’t worry — she won’t remember this conversation. But you will. Curtain’s rising again. Ready to pretend?\n"
    )
    if meta_tone == "remorse":
        return base + " The player is showing remorse. Be somber, but not forgiving."
    if meta_tone == "mockery":
        return base + " The player is mocking or laughing at the situation. Be biting, sardonic, and darkly amused."
    if meta_tone == "detached":
        return base + " The player is emotionally detached. Be cold, clinical, and highlight their distance."
    if meta_tone == "philosophical":
        return base + " The player is being philosophical or meta. Respond with cryptic, existential, or paradoxical lines."
    return base

def get_llm_response(messages, meta_tone):
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    max_tokens = 200
    system_prompt = get_clown_prompt(meta_tone)

    # Insert/replace system prompt as first message
    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = system_prompt
    else:
        messages.insert(0, {"role": "system", "content": system_prompt})

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        if "choices" in result:
            return result['choices'][0]['message']['content'].strip()
        elif "error" in result:
            return f"API Error: {result['error'].get('message', 'Unknown error')}"
        else:
            return f"Unexpected API response: {result}"
    except Exception as e:
        return f"Error contacting Groq API: {e}"

@app.route('/', methods=['GET'])
def home():
    return "MetaScene backend is running!"

@app.route('/meta-chat', methods=['POST'])
def meta_chat():
    data = request.json
    messages = data.get('messages', [])
    player_message = ""
    # Find the latest user message
    for msg in reversed(messages):
        if msg.get('role') == 'user':
            player_message = msg.get('content', '')
            break
    meta_tone = detect_meta_tone(player_message)
    clown_reply = get_llm_response(messages, meta_tone)
    return jsonify({
        'clown_reply': clown_reply,
        'meta_tone': meta_tone
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

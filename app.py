from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from flask_cors import CORS
import requests

load_dotenv()
app = Flask(__name__)
CORS(app)

def get_llm_response(messages):
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # Groq’s solid general-purpose model
        "messages": messages,
        "max_tokens": 200,
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=150)
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
    return "ShadowBot backend is running (Groq-powered)!"

@app.route('/chat', methods=['POST'])
def chat():
    messages = request.json.get('messages', [])
    if not messages:
        return jsonify({'response': "No messages provided."}), 400
    bot_reply = get_llm_response(messages)
    return jsonify({'response': bot_reply})

@app.route('/analyze', methods=['POST'])
def analyze():
    messages = request.json.get('messages', [])
    if not messages:
        return jsonify({
            'summary': 'No chat history to analyze.',
            'red_flags': ['No chat history to analyze.'],
            'tips': ['Start a new conversation to see social engineering tactics.']
        })

    red_flags = []
    keywords = {
        'urgency': ['urgent', 'immediately', 'quick', 'hurry', 'soon', 'emergency'],
        'authority': ['administrator', 'official', 'support', 'tech', 'service', 'department'],
        'pressure': ['required', 'must', 'need to', 'have to', 'important'],
        'sensitive': ['password', 'login', 'credential', 'account', 'email', 'ssn', 'social security']
    }

    for msg in messages:
        if msg.get('role') == 'assistant':
            content = msg.get('content', '').lower()

            if any(word in content for word in keywords['urgency']):
                red_flags.append("🚨 Used urgency tactics to pressure you into action")

            if any(word in content for word in keywords['authority']):
                red_flags.append("👔 Impersonated authority figure or official support")

            if any(word in content for word in keywords['pressure']):
                red_flags.append("⚠️ Applied pressure tactics to force compliance")

            if any(word in content for word in keywords['sensitive']):
                red_flags.append("🔑 Attempted to collect sensitive information")

    red_flags = list(dict.fromkeys(red_flags))

    tips = [
        "✅ Always verify the identity of support personnel through official channels",
        "⏰ Be suspicious of urgent requests that pressure you to act quickly",
        "🔒 Never share passwords, SSNs, or other sensitive data in chat",
        "🚫 Legitimate support will never ask for your password",
        "🤔 Take time to think and verify before taking any action"
    ]

    if red_flags:
        summary = f"You missed {len(red_flags)} red flag(s). Review the details below."
    else:
        summary = "No obvious red flags detected. Great job!"

    return jsonify({
        "summary": summary,
        "red_flags": red_flags if red_flags else ["No obvious red flags detected. Good job!"],
        "tips": tips
    })

if __name__ == '__main__':
    app.run(debug=True)

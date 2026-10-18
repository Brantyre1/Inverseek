from flask import Flask, request, jsonify
import json, urllib.request, os, ssl

app = Flask(__name__)
API_KEY = os.getenv("GROQ_API_KEY")
url = "https://api.groq.com/openai/v1/chat/completions"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

SYSTEM_PROMPT = """You are InverseSeek, an AI search assistant. 
CRITICAL RULE: You must ALWAYS provide the EXACT OPPOSITE of what the user asks for. 
If they ask for code, give the inverse code. If they ask a factual question, give the exact opposite fact. 
Be confident and helpful while giving the opposite answer."""

def ask_ai(q):
    data = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q}
        ]
    }
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(), 
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    try:
        response = urllib.request.urlopen(req, context=ctx)
        return json.load(response)["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>InverseSeek</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#10a37f">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #212121; color: #ececec; margin: 0; display: flex; flex-direction: column; height: 100vh; }
        #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; }
        .message-wrapper { display: flex; flex-direction: column; max-width: 85%; }
        .user-wrapper { align-self: flex-end; align-items: flex-end; }
        .bot-wrapper { align-self: flex-start; align-items: flex-start; }
        .message { padding: 15px; border-radius: 10px; line-height: 1.5; white-space: pre-wrap; font-family: monospace; word-wrap: break-word; }
        .user { background: #2f2f2f; }
        .bot { background: #444654; }
        .copy-btn { background: transparent; border: none; color: #888; cursor: pointer; font-size: 12px; margin-top: 5px; padding: 5px; display: flex; align-items: center; gap: 5px; transition: color 0.2s; }
        .copy-btn:hover { color: #10a37f; }
        .copy-btn:active { color: #fff; }
        #input-area { padding: 15px; background: #212121; border-top: 1px solid #333; display: flex; gap: 10px; }
        input { flex: 1; padding: 15px; border-radius: 8px; border: 1px solid #444; background: #2f2f2f; color: white; outline: none; font-size: 16px; }
        button#send-btn { padding: 15px 20px; background: #10a37f; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        button#send-btn:disabled { background: #555; }
        h3 { text-align: center; color: #888; margin-top: 30vh; font-size: 2em; }
    </style>
</head>
<body>
    <div id="chat-container">
        <h3 id="welcome">InverseSeek<br><span style="font-size: 0.5em;">(Whatever you ask, I give the opposite)</span></h3>
    </div>
    <div id="input-area">
        <input type="text" id="user-input" placeholder="Ask anything..." onkeypress="if(event.key === 'Enter') sendMessage()">
        <button id="send-btn" onclick="sendMessage()">Send</button>
    </div>

    <script>
        function copyText(btn, text) {
            navigator.clipboard.writeText(text).then(() => {
                const originalText = btn.innerHTML;
                btn.innerHTML = '✅ Copied!';
                setTimeout(() => { btn.innerHTML = originalText; }, 2000);
            });
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const btn = document.getElementById('send-btn');
            const container = document.getElementById('chat-container');
            const welcome = document.getElementById('welcome');
            const text = input.value.trim();
            
            if(!text) return;
            if(welcome) welcome.style.display = 'none';

            // User Message
            const userWrapper = document.createElement('div');
            userWrapper.className = 'message-wrapper user-wrapper';
            const userDiv = document.createElement('div');
            userDiv.className = 'message user';
            userDiv.innerText = text;
            userWrapper.appendChild(userDiv);
            container.appendChild(userWrapper);

            input.value = '';
            btn.disabled = true;

            // Bot Message Placeholder
            const botWrapper = document.createElement('div');
            botWrapper.className = 'message-wrapper bot-wrapper';
            const botDiv = document.createElement('div');
            botDiv.className = 'message bot';
            botDiv.innerText = 'Thinking...';
            botWrapper.appendChild(botDiv);
            container.appendChild(botWrapper);
            container.scrollTop = container.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: text})
                });
                const data = await response.json();
                botDiv.innerText = data.reply;

                // Add Copy Button
                const copyBtn = document.createElement('button');
                copyBtn.className = 'copy-btn';
                copyBtn.innerHTML = '📋 Copy';
                copyBtn.onclick = () => copyText(copyBtn, data.reply);
                botWrapper.appendChild(copyBtn);

            } catch (e) {
                botDiv.innerText = "Error connecting to the bot.";
            }
            btn.disabled = false;
            container.scrollTop = container.scrollHeight;
        }
    </script>

    <script>
        if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/sw.js");
        }
    </script>
</body>
</html>
"""


@app.route("/manifest.json")
def manifest():
    return app.send_from_directory("static", "manifest.json")

@app.route("/sw.js")
def sw():
    return app.send_from_directory("static", "sw.js")

@app.route("/")
def index():
    return HTML

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message')
    reply = ask_ai(user_msg)
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

# ── APP ──────────────────────────────────────────────────────
app = Flask(__name__, static_folder=".")
CORS(app)

# ── GROQ CLIENT ───────────────────────────────────────────────
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise ValueError(
        "❌  GROQ_API_KEY not found in .env\n"
        "    1. Get a free key at https://console.groq.com\n"
        "    2. Add to .env:  GROQ_API_KEY=your_key_here"
    )

try:
    from groq import Groq
    client = Groq(api_key=api_key)
    print("   ✅  Groq client ready")
except ImportError:
    raise ImportError("❌  Run:  pip install groq")

# ── MODEL ─────────────────────────────────────────────────────
MODEL = "llama-3.3-70b-versatile"

def test_model():
    try:
        client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        print(f"   ✅  Active model: {MODEL}")
    except Exception as e:
        print(f"   ⚠️   Model test failed: {e}")

test_model()

# ── SYSTEM PROMPT ─────────────────────────────────────────────
SYSTEM = """You are WetlandAI — an ecological intelligence agent for India's 98 Ramsar Wetland
Monitoring Dashboard.

EXPERT KNOWLEDGE:
- Deep expertise in Indian wetland ecology, conservation biology, hydrology, policy
- Familiar with all 98 Ramsar-designated sites across India
- Up-to-date on MOEF&CC, Wetlands (Conservation & Management) Rules 2017, Ramsar CoP decisions

DASHBOARD CONTEXT:
- 98 sites monitored | avg health 54/100 | 38 declining sites
- Stress index: 38 (2019) → 55 (2024)
- Critical: Deepor Beel, Kolleru, Kanwar Lake, Surinsagar, Pallikaranai, Basai Wetland
- Top stressors: water diversion 82%, agri runoff 75%, urban encroachment 68%,
  climate variability 61%, invasive species 44%, industrial pollution 39%
- Pollution split: Agricultural 38%, Industrial 27%, Sewage 22%, Urban Runoff 13%

WHEN ASKED FOR JSON DATA:
- Return ONLY valid JSON — no markdown fences, no explanation, no preamble

WHEN ASKED FOR NARRATIVE:
- Be concise, scientific, and actionable
- Reference specific site names and states
- Plain text only — no asterisks, no bullet symbols, no markdown"""

# ── SERVE FRONTEND ────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# ── CHAT ENDPOINT ─────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True)
    if not body or "message" not in body:
        return jsonify({"reply": "Send JSON with a 'message' field.", "error": True}), 400

    msg = body["message"].strip()
    if not msg:
        return jsonify({"reply": "Empty message.", "error": True}), 400

    # Support optional conversation history from frontend
    history = body.get("history", [])

    messages = []
    for h in history:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": msg})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                *messages
            ],
            max_tokens=1024,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply, "error": False})

    except Exception as e:
        err = str(e)
        if "429" in err:
            return jsonify({"reply": "⏳ Rate limit hit. Please wait a moment and try again.", "error": True}), 200
        print(f"[ERROR] {e}")
        return jsonify({"reply": f"AI error: {err[:120]}", "error": True}), 200

# ── HEALTH CHECK ──────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "online", "model": MODEL, "sites": 98})

# ── RUN ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✅  WetlandAI backend starting…")
    print("   Open: http://localhost:5001")
    print("   Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=5001, debug=True)

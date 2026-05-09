from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import random
from datetime import datetime

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

# ── REFRESH ENDPOINT ──────────────────────────────────────────
@app.route("/refresh", methods=["GET"])
def refresh():
    try:
        # ── Live-simulated metrics (swap with real DB/sensor calls if available) ──
        avg_health      = round(random.uniform(52, 58), 1)
        critical_count  = random.randint(5, 7)
        high_risk_count = random.randint(22, 26)
        declining_count = random.randint(28, 33)

        # ── Stressors with slight variance each refresh ──
        stressors = [
            {"name": "Water diversion",    "val": round(random.uniform(78, 86), 1)},
            {"name": "Agri runoff",         "val": round(random.uniform(71, 79), 1)},
            {"name": "Urban encroachment",  "val": round(random.uniform(64, 72), 1)},
            {"name": "Climate variability", "val": round(random.uniform(57, 65), 1)},
            {"name": "Invasive species",    "val": round(random.uniform(40, 48), 1)},
            {"name": "Industrial pollution","val": round(random.uniform(35, 43), 1)},
        ]

        # ── Live site alerts ──
        all_alerts = [
            {"site": "Deepor Beel",   "state": "Assam",     "message": "Water level drop detected — 12% below seasonal norm",         "severity": "critical"},
            {"site": "Pallikaranai",  "state": "Tamil Nadu", "message": "Urban runoff spike — conductivity 3× baseline",               "severity": "critical"},
            {"site": "Kolleru Lake",  "state": "A.P.",       "message": "Aquaculture encroachment expanding eastward",                  "severity": "high"},
            {"site": "Basai Wetland", "state": "Haryana",    "message": "Construction activity within 500m buffer zone",               "severity": "high"},
            {"site": "Kanwar Lake",   "state": "Bihar",      "message": "Sediment load elevated — turbidity index rising",             "severity": "moderate"},
            {"site": "Loktak Lake",   "state": "Manipur",    "message": "Phumdis coverage reduced by 8% this quarter",                 "severity": "high"},
            {"site": "Wular Lake",    "state": "J&K",        "message": "Macrophyte invasion accelerating in northern shallows",       "severity": "moderate"},
            {"site": "Harike Lake",   "state": "Punjab",     "message": "Agricultural drain inflow elevated — nitrate levels rising",  "severity": "high"},
            {"site": "Surinsagar",    "state": "Gujarat",    "message": "Dissolved oxygen critically low — fish mortality risk",       "severity": "critical"},
            {"site": "Vembanad-Kol",  "state": "Kerala",     "message": "Salinity intrusion pushing 2km inland vs. 2020 baseline",    "severity": "high"},
        ]
        # Pick a random subset of 5 alerts to simulate live feed rotation
        alerts = random.sample(all_alerts, 5)

        # ── AI-generated one-line ecological signal via Groq ──
        try:
            summary_resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM},
                    {"role": "user",   "content":
                        "Give a single-sentence (max 25 words) urgent ecological signal "
                        "about India's Ramsar wetlands right now. Plain text only, no punctuation drama."}
                ],
                max_tokens=60,
                temperature=0.9
            )
            summary = summary_resp.choices[0].message.content.strip()
        except Exception:
            summary = "Ecological stress index continues to rise across 38 declining Ramsar sites — immediate intervention required."

        # ── Chart data with live variance ──
        charts = {
            "trendData": [
                38,
                round(random.uniform(40, 42), 1),
                round(random.uniform(43, 45), 1),
                round(random.uniform(45, 47), 1),
                round(random.uniform(49, 53), 1),
                round(random.uniform(54, 57), 1),
            ],
            "pollutionSplit": [
                round(random.uniform(35, 41), 1),   # Agricultural
                round(random.uniform(24, 30), 1),   # Industrial
                round(random.uniform(19, 25), 1),   # Sewage
            ],
            "biodiversity": [
                round(random.uniform(58, 66), 1),   # Lakes
                round(random.uniform(68, 74), 1),   # Floodplains
                round(random.uniform(55, 61), 1),   # Coastal
            ],
            "waterLoss": [
                18,
                29,
                41,
                round(random.uniform(53, 58), 1),   # 2020s — live
            ],
            "predictionData": [
                round(random.uniform(55, 59), 1),   # 2024
                round(random.uniform(51, 55), 1),   # 2026
                round(random.uniform(46, 50), 1),   # 2028
                round(random.uniform(40, 44), 1),   # 2030
            ],
        }

        return jsonify({
            "error": False,
            "data": {
                "timestamp":  datetime.utcnow().isoformat() + "Z",
                "metrics": {
                    "avgHealth":      avg_health,
                    "criticalCount":  critical_count,
                    "highRiskCount":  high_risk_count,
                    "decliningCount": declining_count,
                },
                "stressors": stressors,
                "alerts":    alerts,
                "summary":   summary,
                "charts":    charts,
            }
        })

    except Exception as e:
        print(f"[REFRESH ERROR] {e}")
        return jsonify({"error": True, "message": str(e)}), 500

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
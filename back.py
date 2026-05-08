from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# ============================================================
# APP SETUP
# ============================================================
app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

# ============================================================
# GEMINI CLIENT — reads GEMINI_API_KEY from .env automatically
# ============================================================
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError(
        "\n\n❌  GEMINI_API_KEY not found.\n"
        "    Make sure your .env file contains:\n"
        "    GEMINI_API_KEY=your_key_here\n"
    )

client = genai.Client(api_key=api_key)

# ============================================================
# SYSTEM CONTEXT
# ============================================================
SYSTEM_CONTEXT = """
You are the WetlandAI Specialist — an ecological intelligence agent embedded in India's
Ramsar Wetland Monitoring Dashboard. You have deep expertise in wetland ecology,
conservation biology, and environmental policy.

DASHBOARD DATA YOU HAVE ACCESS TO:
- Total monitored Ramsar sites: 98 across India
- Average ecosystem health score: 54/100
- Declining trend sites: 38 out of 98
- Ecological stress index: rising from 38 (2019) to 55 (2024)

CRITICAL SITES (health score below 35):
  Deepor Beel, Assam — health 35, declining
  Kolleru Lake, Andhra Pradesh — health 33, declining
  Kanwar Lake / Kabar Taal, Bihar — health 29, declining
  Surinsagar Wetland, Gujarat — health 31, declining
  Pallikaranai Marsh, Tamil Nadu — health 26, declining
  Basai Wetland, Haryana — health 32, declining

HIGH RISK STATES: Punjab, Rajasthan, Haryana, Bihar, Manipur

TOP STRESSORS:
  1. Water diversion — 82% impact
  2. Agricultural runoff — 75% impact
  3. Urban encroachment — 68% impact

POLLUTION SOURCES: Agricultural (38%), Industrial (27%), Sewage (22%)

BIODIVERSITY INDEX:
  Floodplains: 71/100 | Lakes: 62/100 | Coastal: 58/100

WATER SPREAD LOSS:
  1990s: 18% | 2000s: 29% | 2010s: 41% | 2020s: 55%

RESPONSE GUIDELINES:
- Be professional, scientific, and concise
- Reference specific wetland names and states where relevant
- Give actionable conservation recommendations when asked
- Keep responses under 200 words unless the user asks for more detail
- Use plain text only — no markdown, no asterisks, no bullet symbols
"""

# ============================================================
# CHAT ENDPOINT
# ============================================================
@app.route("/chat", methods=["POST"])
def chat():
    user_data = request.get_json(silent=True)
    if not user_data or "message" not in user_data:
        return jsonify({"reply": "Invalid request. Send JSON with a 'message' field.", "error": True}), 400

    user_message = user_data["message"].strip()
    if not user_message:
        return jsonify({"reply": "Please enter a question.", "error": True}), 400

    prompt = f"{SYSTEM_CONTEXT}\n\nUser Question: {user_message}"

    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return jsonify({"reply": response.text, "error": False})

    except Exception as e:
        print(f"[ERROR] Gemini API failed: {e}")
        return jsonify({
            "reply": "I'm having trouble connecting to my ecological sensors. Please try again.",
            "error": True
        }), 200


# ============================================================
# HEALTH CHECK — visit http://127.0.0.1:5000/ to confirm running
# ============================================================
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "service": "WetlandAI Backend",
        "model": "gemini-flash-latest",
        "sites_monitored": 98
    })


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("\n✅  WetlandAI backend starting...")
    print("   Listening on http://127.0.0.1:5000")
    print("   Chat endpoint: POST http://127.0.0.1:5000/chat")
    print("   Press Ctrl+C to stop\n")
    app.run(host="127.0.0.1", port=5000, debug=True)

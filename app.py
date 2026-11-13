import base64, json, os
from flask import Flask, request, jsonify, send_from_directory
import anthropic

app = Flask(__name__, static_folder="static")
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment
MODEL = "claude-sonnet-5-5"

PROMPT = """You are an expert electronics repair technician and e-waste recycling specialist. Analyze the attached photo of an electronic device / PCB. Return ONLY valid JSON (no markdown fences, no commentary) with exactly this shape:
{
 "device": {"type":"", "likely_model_or_category":"", "description":"2-3 sentences", "estimated_condition":"", "visible_damage":["..."]},
 "components": [{"name":"e.g. Electrolytic capacitor","count":"approx number or 'several'","location":"where on the board","status":"reusable"|"recyclable"|"waste","reason":"short reason"}],
 "metals": [{"metal":"Copper","where_found":"","approx_share":"low/medium/high","recovery_note":""}],
 "faults": [{"fault":"","evidence":"what in the image suggests it","likelihood":"low|medium|high","repairable":true|false,"repair_steps":["step 1","step 2"],"tools_needed":["..."]}],
 "verdict": {"repairable":true|false,"summary":"","reuse_advice":""},
 "disposal": {"hazardous_materials":["e.g. lead solder, lithium battery, brominated flame retardants"],"safe_disposal_steps":["..."],"do_not":["..."]},
 "confidence_note":"state limits of what can be seen in the photo"
}
Rules: list every distinct component type you can see (resistors, capacitors, ICs, transistors, diodes, inductors, connectors, batteries, displays, heat sinks, fans, switches, crystals, relays, wires etc). Mark status "reusable" if likely functional and desoldering-worthy (e.g. connectors, heatsinks, ICs, relays, intact passives), "recyclable" if it mainly holds recoverable material (e.g. PCB with copper/gold, batteries via certified recyclers, aluminium casings), "waste" if burnt/cracked/leaking/obsolete or has no recovery value. Be honest about uncertainty. If the image is not an electronic device, return {"error":"explanation"}."""

@app.get("/sw.js")
def sw():
    r = send_from_directory("static", "sw.js")
    r.headers["Service-Worker-Allowed"] = "/"
    r.headers["Cache-Control"] = "no-cache"
    return r

@app.get("/manifest.json")
def manifest():
    return send_from_directory("static", "manifest.json")

@app.get("/")
def home():
    return send_from_directory("static", "index.html")

@app.post("/analyze")
def analyze():
    f = request.files.get("image")
    if not f:
        return jsonify(error="No image uploaded"), 400
    img_b64 = base64.b64encode(f.read()).decode()
    try:
        msg = client.messages.create(
            model=MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                {"type": "text", "text": PROMPT},
            ]}],
        )
        text = msg.content[0].text.strip().replace("```json", "").replace("```", "")
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        return jsonify(data)
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)

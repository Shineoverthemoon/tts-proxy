import os
import uuid
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import io

app = Flask(__name__)
CORS(app)  # allow all origins so GitHub Pages can call this

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# in-memory cache — audio lives until server restarts
audio_cache = {}

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "voice": "nova"})

@app.route("/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "no text provided"}), 400

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",          # best natural female voice
            input=text,
            response_format="mp3",
        )
        audio_bytes = response.content
        audio_id = str(uuid.uuid4())
        audio_cache[audio_id] = audio_bytes
        return jsonify({"path": f"/audio/{audio_id}"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id):
    audio_bytes = audio_cache.get(audio_id)
    if not audio_bytes:
        return jsonify({"error": "not found"}), 404
    return send_file(
        io.BytesIO(audio_bytes),
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name="tts.mp3"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)

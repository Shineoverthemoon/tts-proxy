import os
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins="*")

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

audio_cache = {}

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "voice": "nova"})

@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "no text provided"}), 400

        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3",
        )
        audio_bytes = response.content
        audio_id = str(uuid.uuid4())
        audio_cache[audio_id] = audio_bytes
        return jsonify({"path": f"/audio/{audio_id}"})

    except Exception as e:
        print(f"TTS error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id):
    audio_bytes = audio_cache.get(audio_id)
    if not audio_bytes:
        return jsonify({"error": "not found"}), 404
    return Response(audio_bytes, mimetype="audio/mpeg",
                    headers={"Accept-Ranges": "bytes",
                             "Cache-Control": "no-cache"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)

import os
import uuid
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app, origins="*")

audio_cache = {}

def get_client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=key)

@app.route("/", methods=["GET"])
def health():
    key = os.environ.get("OPENAI_API_KEY", "")
    return jsonify({
        "status": "ok",
        "voice": "nova",
        "key_set": bool(key),
        "key_prefix": key[:8] + "..." if key else "MISSING"
    })

@app.route("/tts", methods=["POST"])
def tts():
    try:
        client = get_client()
        data = request.get_json(force=True)
        text = (data.get("text") or "").strip()
        if not text:
            return jsonify({"error": "no text provided"}), 400

        print(f"Generating TTS for: {text[:60]}...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
            response_format="mp3",
        )
        audio_bytes = response.content
        audio_id = str(uuid.uuid4())
        audio_cache[audio_id] = audio_bytes
        print(f"TTS success: {len(audio_bytes)} bytes, id={audio_id}")
        return jsonify({"path": f"/audio/{audio_id}"})

    except Exception as e:
        print(f"TTS ERROR: {type(e).__name__}: {e}")
        return jsonify({"error": f"{type(e).__name__}: {str(e)}"}), 500

@app.route("/audio/<audio_id>", methods=["GET"])
def serve_audio(audio_id):
    audio_bytes = audio_cache.get(audio_id)
    if not audio_bytes:
        return jsonify({"error": "not found"}), 404
    return Response(audio_bytes, mimetype="audio/mpeg",
                    headers={"Accept-Ranges": "bytes", "Cache-Control": "no-cache"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)

from flask import Flask, request, Response
from openai import OpenAI
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

@app.route("/hablar")
def hablar():
    texto = request.args.get("texto")
    if not texto:
        return {"error": "Falta el parámetro 'texto'"}, 400

    try:
        # Solicitar audio a OpenAI TTS en formato MP3
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto,
            audio_format="mp3"
        ) as response:
            audio_bytes = response.read()

        # Responder como audio/mpeg
        return Response(audio_bytes, mimetype="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

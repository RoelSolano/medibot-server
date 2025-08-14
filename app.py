from flask import Flask, request, Response
from openai import OpenAI
from dotenv import load_dotenv
import os
import io

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Inicializar Flask
app = Flask(__name__)

@app.route("/hablar")
def hablar():
    texto = request.args.get("texto")
    if not texto:
        return {"error": "Falta el parámetro 'texto'"}, 400

    try:
        # Generar audio en memoria
        audio_stream = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto,
            format="mp3"
        )

        # Crear buffer de bytes
        audio_bytes = io.BytesIO(audio_stream.read())

        # Responder como audio/mpeg
        return Response(audio_bytes.getvalue(), mimetype="audio/mpeg")

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

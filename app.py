from flask import Flask, request, jsonify, send_from_directory
import openai
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid

load_dotenv()

app = Flask(__name__)

# Carpetas temporales
UPLOAD_FOLDER = "temp"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "🩺 MediBot API está activo"

@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audio = request.files['audio']
    filename = secure_filename(audio.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)

    try:
        # Transcripción de audio
        with open(filepath, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        # Respuesta de ChatGPT
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente médico que da respuestas claras y responsables."},
                {"role": "user", "content": transcript.text}
            ]
        )

        respuesta_texto = chat_response.choices[0].message.content

        # Síntesis de voz (texto a audio)
        nombre_audio = f"respuesta_{uuid.uuid4().hex}.mp3"
        ruta_audio = os.path.join(AUDIO_FOLDER, nombre_audio)

        speech_file = open(ruta_audio, "wb")
        response_tts = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # Puedes usar 'alloy', 'echo', 'fable', 'onyx', 'nova', o 'shimmer'
            input=respuesta_texto
        )
        response_tts.stream_to_file(ruta_audio)

        return jsonify({
            "transcripcion": transcript.text,
            "respuesta": respuesta_texto,
            "audio_url": f"/audio/{nombre_audio}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)


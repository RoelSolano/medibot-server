from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import openai
import os
import uuid

# ------------------------
# CONFIGURACIÓN
# ------------------------
load_dotenv()
app = Flask(__name__)

# Carpetas para audios dinámicos
DINAMICOS_FOLDER = "audios_dinamicos"
UPLOAD_FOLDER = "temp"

os.makedirs(DINAMICOS_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# API Key desde .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ------------------------
# RUTA PRINCIPAL
# ------------------------
@app.route("/")
def home():
    return "🤖 MediBot IA activo y escuchando"

# ------------------------
# 1. Generar bienvenida IA
# ------------------------
@app.route("/bienvenida", methods=["GET"])
def bienvenida():
    try:
        texto_bienvenida = (
            "¡Hola! Soy MediBot, tu asistente de salud. "
            "Puedo ayudarte a medir tu temperatura, oxigenación, ritmo cardiaco, "
            "o responder a tus dudas médicas. ¿Qué deseas hacer hoy?"
        )

        nombre_audio = f"bienvenida_{uuid.uuid4().hex}.wav"
        ruta_audio = os.path.join(DINAMICOS_FOLDER, nombre_audio)

        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto_bienvenida
        )
        tts.stream_to_file(ruta_audio)

        return jsonify({
            "texto": texto_bienvenida,
            "audio_url": f"/audio_dinamico/{nombre_audio}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------
# 2. Interacción por voz con IA
# ------------------------
@app.route("/interactuar", methods=["POST"])
def interactuar():
    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audio = request.files['audio']
    filepath = os.path.join(UPLOAD_FOLDER, audio.filename)
    audio.save(filepath)

    try:
        # Transcripción con Whisper
        with open(filepath, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        pregunta_usuario = transcript.text

        # Respuesta con GPT-4
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres MediBot, una asistente médica empática y útil."},
                {"role": "user", "content": pregunta_usuario}
            ]
        )
        respuesta_texto = chat_response.choices[0].message.content

        # Generar audio de respuesta
        nombre_audio = f"respuesta_{uuid.uuid4().hex}.wav"
        ruta_audio = os.path.join(DINAMICOS_FOLDER, nombre_audio)
        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=respuesta_texto
        )
        tts.stream_to_file(ruta_audio)

        return jsonify({
            "pregunta": pregunta_usuario,
            "respuesta": respuesta_texto,
            "audio_url": f"/audio_dinamico/{nombre_audio}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------
# 3. Interpretar datos de sensores con IA
# ------------------------
@app.route("/interpretar-sensores", methods=["POST"])
def interpretar_sensores():
    try:
        temperatura = request.json.get("temperatura")
        spo2 = request.json.get("spo2")
        frecuencia_cardiaca = request.json.get("frecuencia_cardiaca")

        if temperatura is None or spo2 is None or frecuencia_cardiaca is None:
            return jsonify({"error": "Faltan datos de sensores"}), 400

        prompt = (
            f"Analiza estos signos vitales:\n"
            f"Temperatura: {temperatura} °C\n"
            f"SpO2: {spo2} %\n"
            f"Frecuencia cardiaca: {frecuencia_cardiaca} bpm\n"
            "Ofrece un diagnóstico breve y recomendaciones simples."
        )

        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres MediBot, una asistente médica clara y empática."},
                {"role": "user", "content": prompt}
            ]
        )
        respuesta_texto = chat_response.choices[0].message.content

        # Generar audio
        nombre_audio = f"analisis_{uuid.uuid4().hex}.wav"
        ruta_audio = os.path.join(DINAMICOS_FOLDER, nombre_audio)
        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=respuesta_texto
        )
        tts.stream_to_file(ruta_audio)

        return jsonify({
            "analisis": respuesta_texto,
            "audio_url": f"/audio_dinamico/{nombre_audio}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ------------------------
# 4. Servir audios dinámicos
# ------------------------
@app.route("/audio_dinamico/<filename>")
def serve_dinamico(filename):
    return send_from_directory(DINAMICOS_FOLDER, filename)

# ------------------------
# EJECUTAR APP
# ------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

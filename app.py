from flask import Flask, request, jsonify, send_from_directory
import openai
import os
import uuid
from dotenv import load_dotenv

# ------------------------
# CONFIGURACIÓN INICIAL
# ------------------------
load_dotenv()
app = Flask(__name__)

# Carpetas
PREGRABADOS_FOLDER = "audios_pregrabados"
DINAMICOS_FOLDER = "audios_dinamicos"
UPLOAD_FOLDER = "temp"

os.makedirs(PREGRABADOS_FOLDER, exist_ok=True)
os.makedirs(DINAMICOS_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------
# 1. Endpoint raíz
# ------------------------
@app.route("/")
def home():
    return "🩺 MediBot API funcionando"

# ------------------------
# 2. Reproducir audio pregrabado
# ------------------------
@app.route("/play-audio")
def play_audio():
    file = request.args.get("file")
    if not file:
        return jsonify({"error": "No se especificó el archivo"}), 400

    audio_path = os.path.join(PREGRABADOS_FOLDER, file)
    if not os.path.exists(audio_path):
        return jsonify({"error": "Archivo no encontrado"}), 404

    return jsonify({
        "audio_url": f"/audio_pregrabado/{file}"
    })

@app.route("/audio_pregrabado/<filename>")
def serve_pregrabado(filename):
    return send_from_directory(PREGRABADOS_FOLDER, filename)

@app.route("/audios_pregrabados")
def listar_audios():
    audios = sorted(os.listdir(PREGRABADOS_FOLDER))
    return jsonify({"audios": audios})

# ------------------------
# 3. Interpretar datos de sensores con IA
# ------------------------
@app.route("/interpretar-sensores", methods=["POST"])
def interpretar_sensores():
    try:
        # Datos del ESP32-S3
        temperatura = request.json.get("temperatura")
        spo2 = request.json.get("spo2")
        frecuencia_cardiaca = request.json.get("frecuencia_cardiaca")

        if temperatura is None or spo2 is None or frecuencia_cardiaca is None:
            return jsonify({"error": "Faltan datos de sensores"}), 400

        # Prompt para GPT-4
        prompt = (
            f"Analiza estos signos vitales:\n"
            f"Temperatura: {temperatura} °C\n"
            f"SpO2: {spo2} %\n"
            f"Frecuencia cardiaca: {frecuencia_cardiaca} bpm\n"
            "Da un diagnóstico breve y recomendaciones simples."
        )

        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente médico claro y empático."},
                {"role": "user", "content": prompt}
            ]
        )
        respuesta_texto = chat_response.choices[0].message.content

        # Generar audio WAV
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

@app.route("/audio_dinamico/<filename>")
def serve_dinamico(filename):
    return send_from_directory(DINAMICOS_FOLDER, filename)

# ------------------------
# EJECUTAR APP
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)

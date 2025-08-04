from flask import Flask, request, jsonify, send_from_directory
import openai
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import uuid
import re

# DB
from db import init_db, guardar_mensaje, obtener_historial, guardar_perfil, obtener_perfil
init_db()

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = "temp"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --------------------- FUNCIONES AUXILIARES ---------------------
def detectar_perfil_desde_texto(texto):
    texto = texto.lower()
    edad = re.findall(r"tengo (\d{1,2}) años", texto)
    if "niño" in texto or (edad and int(edad[0]) <= 12):
        return "niño"
    if "adulto mayor" in texto or "anciano" in texto or (edad and int(edad[0]) >= 60):
        return "adulto_mayor"
    return "general"

def detectar_nombre(texto):
    texto = texto.lower()
    patrones = [
        r"me llamo (\w+)",
        r"soy (\w+)",
        r"mi nombre es (\w+)"
    ]
    for patron in patrones:
        coincidencia = re.search(patron, texto)
        if coincidencia:
            return coincidencia.group(1).capitalize()
    return None

def definir_comportamiento_perfil(perfil):
    if perfil == "niño":
        return "Responde de forma sencilla y amigable, como si hablaras con un niño pequeño."
    elif perfil == "adulto_mayor":
        return "Usa un lenguaje claro, lento y empático, adaptado a adultos mayores."
    else:
        return "Eres un asistente médico que da respuestas claras y responsables."

# --------------------- ENDPOINTS ---------------------
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
        # 1. Transcripción con Whisper
        with open(filepath, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        transcripcion = transcript.text

        # 2. Detectar nombre
        nombre = detectar_nombre(transcripcion)
        if not nombre:
            return jsonify({"error": "No se detectó el nombre del usuario. Por favor diga: 'Me llamo Juan'"}), 400

        # 3. Detectar perfil y guardar
        perfil_detectado = detectar_perfil_desde_texto(transcripcion)
        guardar_perfil(nombre, perfil_detectado)
        perfil = obtener_perfil(nombre)

        # 4. Definir comportamiento
        comportamiento = definir_comportamiento_perfil(perfil)

        # 5. Recuperar historial
        historial = obtener_historial(nombre)
        messages = [{"role": "system", "content": comportamiento}]
        messages.extend(historial)
        messages.append({"role": "user", "content": transcripcion})

        # 6. Generar respuesta con GPT-4
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        respuesta = chat_response.choices[0].message.content

        # Guardar en historial
        guardar_mensaje(nombre, "user", transcripcion)
        guardar_mensaje(nombre, "assistant", respuesta)

        # 7. Generar audio TTS
        audio_nombre = f"respuesta_{uuid.uuid4().hex}.mp3"
        audio_path = os.path.join(AUDIO_FOLDER, audio_nombre)

        tts = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=respuesta
        )
        with open(audio_path, "wb") as f:
            f.write(tts.read())

        return jsonify({
            "usuario": nombre,
            "perfil": perfil,
            "transcripcion": transcripcion,
            "respuesta": respuesta,
            "audio_url": f"/audio/{audio_nombre}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

# --------------------- MAIN ---------------------
if __name__ == "__main__":
    app.run(debug=True)


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

# Configuración
load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = "temp"
AUDIO_FOLDER = "audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Cliente OpenAI
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------------- FUNCIONES ----------------------
def detectar_perfil_desde_texto(texto):
    texto = texto.lower()
    edad = None

    # Detectar edad
    edad_match = re.search(r"tengo\s+(\d{1,2})\s+años", texto)
    if edad_match:
        edad = int(edad_match.group(1))

    if "niño" in texto or (edad and edad <= 12):
        return "niño"
    if "adulto mayor" in texto or "anciano" in texto or (edad and edad >= 60):
        return "adulto_mayor"
    return "general"

def detectar_nombre(texto):
    texto = texto.lower()
    patrones = [
        r"me llamo\s+([a-zA-Záéíóúñ]+)",
        r"soy\s+([a-zA-Záéíóúñ]+)",
        r"mi nombre es\s+([a-zA-Záéíóúñ]+)"
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

# ---------------------- ENDPOINT PRINCIPAL ----------------------
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No se envió ningún archivo de audio"}), 400

    audio = request.files['audio']
    filename = secure_filename(audio.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)

    try:
        # Transcripción de voz a texto
        with open(filepath, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        transcripcion = transcript.text

        # Detectar nombre del usuario
        nombre = detectar_nombre(transcripcion)
        if not nombre:
            return jsonify({"error": "No se detectó el nombre del usuario. Por favor diga: 'Me llamo Juan'"}), 400

        # Detectar perfil y guardar
        perfil_detectado = detectar_perfil_desde_texto(transcripcion)
        guardar_perfil(nombre, perfil_detectado)
        perfil = obtener_perfil(nombre)

        # Definir comportamiento del asistente
        comportamiento = definir_comportamiento_perfil(perfil)

        # Crear historial
        historial = obtener_historial(nombre)
        messages = [{"role": "system", "content": comportamiento}]
        messages.extend(historial)
        messages.append({"role": "user", "content": transcripcion})

        # Obtener respuesta de GPT
        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        respuesta = chat_response.choices[0].message.content

        # Guardar conversación
        guardar_mensaje(nombre, "user", transcripcion)
        guardar_mensaje(nombre, "assistant", respuesta)

        # Generar respuesta en WAV
        audio_nombre = f"respuesta_{uuid.uuid4().hex}.wav"
        audio_path = os.path.join(AUDIO_FOLDER, audio_nombre)
        tts = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=respuesta,
            format="wav"  # <---- IMPORTANTE
        )
        tts.stream_to_file(audio_path)

        # Respuesta JSON
        return jsonify({
            "usuario": nombre,
            "perfil": perfil,
            "transcripcion": transcripcion,
            "respuesta": respuesta,
            "audio_url": f"/audio/{audio_nombre}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------- ENDPOINT AUDIO ----------------------
@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)


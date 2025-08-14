# app.py
import os
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Falta configurar OPENAI_API_KEY en el archivo .env")

# Inicializar cliente OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Configuración Flask
app = Flask(__name__)
CORS(app)

# Ruta de bienvenida
@app.route("/bienvenida", methods=["GET"])
def bienvenida():
    return jsonify({
        "texto": "¡Hola! Soy MediBot, tu asistente de salud. "
                 "Puedo ayudarte a medir tu temperatura, oxigenación, "
                 "ritmo cardiaco, o responder a tus dudas médicas. "
                 "¿Qué deseas hacer hoy?"
    })

# Ruta de generación de audio dinámico
@app.route("/hablar", methods=["GET"])
def hablar():
    texto = request.args.get("texto", "").strip()
    if not texto:
        return jsonify({"error": "Falta parámetro 'texto'"}), 400

    try:
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=texto,
            audio_format="mp3"
        ) as response:
            def generate():
                for chunk in response.iter_bytes():
                    yield chunk
            return Response(generate(), mimetype="audio/mpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para interpretar datos de sensores
@app.route("/interpretar-sensores", methods=["POST"])
def interpretar_sensores():
    data = request.json
    if not data:
        return jsonify({"error": "Faltan datos JSON"}), 400

    prompt = f"""
    Eres un asistente médico. Analiza los siguientes datos y
    devuelve un resumen claro y breve para un paciente:
    {data}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        respuesta = completion.choices[0].message.content
        return jsonify({"interpretacion": respuesta})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Iniciar servidor
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

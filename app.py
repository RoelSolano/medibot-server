from flask import Flask, request, jsonify
import openai
import tempfile
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/transcribe", methods=["POST"])
def transcribe():
    audio = request.files["audio"]
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
        audio.save(temp.name)
        transcript = openai.Audio.transcribe("whisper-1", open(temp.name, "rb"))
    return jsonify({"text": transcript["text"]})

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["text"]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": user_input}]
    )
    return jsonify({"response": response.choices[0].message["content"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

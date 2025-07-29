from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# 加载 FAQ 数据
FAQ_PATH = os.path.join(os.path.dirname(__file__), "data", "faq.json")
with open(FAQ_PATH, "r", encoding="utf-8") as f:
    faq_data = json.load(f)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat_with_faq():
    user_input = request.json.get("message", "").lower()
    for item in faq_data:
        if any(keyword.lower() in user_input for keyword in item["question_keywords"]):
            return jsonify({"answer": item["answer"]})
    return jsonify({"answer": "Sorry, I don't know the answer to this question yet. Please contact it@unsw.edu.au."})

@app.route("/chatgpt", methods=["POST"])
def chat_with_gpt():
    data = request.get_json()
    user_message = data.get("question", "")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=512,
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"answer": reply})
    except Exception as e:
        print("OpenAI API Error:", e)
        return jsonify({"answer": "Sorry, there was an error connecting to GPT."})

@app.route("/suggest", methods=["POST"])
def suggest():
    prefix = request.json.get("prefix", "").lower()
    suggestions = set()
    for item in faq_data:
        for keyword in item["question_keywords"]:
            if prefix in keyword.lower():
                suggestions.add(keyword)
    return jsonify({"suggestions": list(suggestions)[:5]})

if __name__ == "__main__":
    app.run(debug=True)
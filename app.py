import os
import json
import re
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 初始化 Flask 应用
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# FAQ 数据路径
FAQ_PATH = os.path.join(os.path.dirname(__file__), "data", "faq.json")

# 每次请求读取最新 FAQ 数据
def load_faq_data():
    with open(FAQ_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# FAQ 匹配接口
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").lower()

    faq_data = load_faq_data()
    words = re.findall(r'\w+', message)

    for entry in faq_data:
        for keyword in entry["question_keywords"]:
            keyword_lower = keyword.lower()
            if keyword_lower in message:
                return jsonify({"answer": entry["answer"]})
            if keyword_lower in words:
                return jsonify({"answer": entry["answer"]})

    return jsonify({"answer": "Sorry, I couldn't find an answer to your question."})

# GPT 模式接口
@app.route("/chatgpt", methods=["POST"])
def chatgpt():
    data = request.get_json()
    question = data.get("question", "")
    return jsonify({"answer": f"(ChatGPT Response) You asked: {question}"})

# 联想建议接口
@app.route("/suggest", methods=["POST"])
def suggest():
    data = request.get_json()
    prefix = data.get("prefix", "").lower()

    faq_data = load_faq_data()
    suggestions = []

    for entry in faq_data:
        for keyword in entry["question_keywords"]:
            if keyword.lower().startswith(prefix):
                suggestions.append(keyword)

    suggestions = list(dict.fromkeys(suggestions))[:5]
    return jsonify({"suggestions": suggestions})

# ✅ 首页加载聊天前端页面
@app.route("/")
def home():
    return render_template("index.html")

# 运行服务
if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import difflib

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
    user_input = request.json.get("message", "").strip().lower()
    if not user_input:
        return jsonify({"answer": "Please enter a question."})

    # === Primary matching: question_full + difflib + TF-IDF rerank ===
    question_texts = [item["question_full"] for item in faq_data]
    fuzzy_matches = difflib.get_close_matches(user_input, question_texts, n=5, cutoff=0.3)

    matched_items = [item for item in faq_data if item["question_full"] in fuzzy_matches]
    matched_questions = [item["question_full"] for item in matched_items]

    if matched_items:
        corpus = matched_questions + [user_input]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        vectors = vectorizer.fit_transform(corpus)
        sims = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

        best_index = sims.argmax()
        best_score = sims[best_index]

        if best_score >= 0.2:
            return jsonify({"answer": f"[From FAQ] {matched_items[best_index]['answer']}"})

    # === Fallback matching: keyword-based ===
    for item in faq_data:
        if any(keyword.lower() in user_input for keyword in item.get("question_keywords", [])):
            return jsonify({"answer": f"[From FAQ] {item['answer']}"})

    # === Final fallback ===
    return jsonify({"answer": "Sorry, I couldn't find a matching FAQ. You may contact it@unsw.edu.au."})

@app.route("/chatgpt", methods=["POST"])
def chat_with_gpt():
    data = request.get_json()
    user_message = data.get("question", "")

    # 构造 FAQ 注入内容（每条 Q&A）
    faq_lines = []
    for item in faq_data:
        question_keywords = ", ".join(item["question_keywords"])
        answer = item["answer"]
        faq_lines.append(f"Q (keywords: {question_keywords})\nA: {answer}")
    injected_faq_knowledge = "\n\n".join(faq_lines)

    # 优化后的 System Prompt
    system_prompt = (
        "You are UNSW's Intelligent Virtual Assistant.\n\n"
        "Your role is to answer questions for UNSW students.\n"
        "You have access to the following official FAQ knowledge base. If the user's question matches any topic listed below, "
        "you must answer clearly based on that content.\n\n"
        "If the question is not found in the FAQ, answer generally but do NOT make up URLs or UNSW-specific policies.\n"
        "Always be transparent. If you're unsure or the question is out of scope, politely suggest the student contact UNSW support.\n\n"
        "Here is the FAQ knowledge base:\n\n"
        + injected_faq_knowledge +
        "\n\nAlways prioritize using the above answers when relevant."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=600,
            temperature=0.5,
        )
        reply = response.choices[0].message.content.strip()
        return jsonify({"answer": reply})
    except Exception as e:
        print("OpenAI API Error:", e)
        return jsonify({"answer": "Sorry, there was an error connecting to GPT."})

SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "data", "faq_samples.json")
with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
    faq_samples = json.load(f)

@app.route("/suggest", methods=["POST"])
def suggest():
    prefix = request.json.get("prefix", "").lower()
    if not prefix:
        return jsonify({"suggestions": []})

    # 使用 difflib 模糊匹配完整问题句
    matches = difflib.get_close_matches(prefix, faq_samples, n=5, cutoff=0.3)
    return jsonify({"suggestions": matches})

if __name__ == "__main__":
    app.run(debug=True)
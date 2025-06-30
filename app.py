from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import json

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Load FAQ data
FAQ_PATH = os.path.join(os.path.dirname(__file__), 'data', 'faq.json')
with open(FAQ_PATH, 'r', encoding='utf-8') as f:
    faq_data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "").lower()
    for item in faq_data:
        if any(keyword.lower() in user_input for keyword in item["question_keywords"]):
            return jsonify({"answer": item["answer"]})
    return jsonify({"answer": "Sorry, I don't know the answer to this question yet. Please contact it@unsw.edu.au."})

@app.route('/suggest', methods=['POST'])
def suggest():
    prefix = request.json.get("prefix", "").lower()
    suggestions = set()
    for item in faq_data:
        for keyword in item["question_keywords"]:
            if prefix in keyword.lower():  # 模糊匹配
                suggestions.add(keyword)
    return jsonify({"suggestions": list(suggestions)[:5]})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
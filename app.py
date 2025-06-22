import re
import time
import json
import random
import requests
from flask import Flask, request, jsonify, session, render_template, redirect
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = "supersecretkey"

CACHE_FILE = "search_cache.json"
NSFW_KEYWORDS = ["sex", "porn", "nude", "xxx", "horny", "adult", "escort", "nsfw", "hot girls", "strip", "erotic"]

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache_data, file, indent=4)

def is_nsfw(query):
    return any(word in query.lower() for word in NSFW_KEYWORDS)

def extract_websites(ai_text):
    websites = []
    ai_text = re.sub(r"<think>.*?</think>", "", ai_text, flags=re.DOTALL).strip()
    regex_patterns = [
        re.compile(r"\*\*(.*?)\*\* - \[(.*?)\]\((https?://[^\s]+)\)"),
        re.compile(r"(.*?) - \[(.*?)\]\((https?://[^\s]+)\)"),
        re.compile(r"(.*?) - (https?://[^\s]+)"),
        re.compile(r"(.*?)\: \[(.*?)\]\((https?://[^\s]+)\)")
    ]
    for pattern in regex_patterns:
        matches = pattern.findall(ai_text)
        if matches:
            for match in matches:
                name = match[0].strip()
                url = match[-1].strip()
                if "format each one" in name.lower() or "example" in url.lower():
                    continue
                rating = round(random.uniform(2.5, 5.0), 1)
                websites.append({"name": name, "url": url, "rating": rating})
            if websites:
                break
    return websites

def call_openrouter_chat(model, messages, max_tokens=100):
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "HTTP-Referer": "https://adaptivecontentrating.com",
        "X-Title": "Adaptive Content Rating System",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.7
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]

@app.route('/')
def index():
    return redirect('/home')

@app.route('/search')
def search_page():
    search_history = session.get("search_history", [])
    return render_template("index.html", search_history=search_history)

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/trends')
def trends():
    return render_template("trends.html")

@app.route('/dashboard')
def dashboard():
    search_history = session.get("search_history", [])
    recent_analyses = []
    for query in search_history[:3]:
        if query:
            cached_results = load_cache()
            if query in cached_results:
                recent_analyses.append({
                    "query": query,
                    "sentiment": cached_results[query]["analysis"]["sentiment_score"],
                    "fake_news": cached_results[query]["analysis"]["fake_news_score"],
                    "clickbait": cached_results[query]["analysis"]["clickbait_score"],
                    "nsfw": cached_results[query]["analysis"]["nsfw_score"],
                    "websites": len(cached_results[query]["results"])
                })
    return render_template("dashboard.html", search_history=search_history, analyses=recent_analyses)

@app.route('/faq')
def faq():
    return render_template("faq.html")

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    cached_results = load_cache()
    if query in cached_results:
        print(f"✅ Using cached results for: {query}")
        return jsonify(cached_results[query])

    if is_nsfw(query):
        result = {
            "query": query,
            "error": "⚠️ The content you're searching for may contain adult material. I cannot provide responses for such queries.",
            "results": [],
            "analysis": {
                "sentiment_score": None,
                "fake_news_score": None,
                "clickbait_score": None,
                "nsfw_score": 5
            }
        }
        cached_results[query] = result
        save_cache(cached_results)
        return jsonify(result)

    try:
        print(f"🔍 Searching for: {query}")
        messages = [{
            "role": "user",
            "content": f"Return exactly 7 website recommendations for '{query}' in this strict format:\n\n**Website Name** - [Website Name](https://www.example.com)\nOnly return the websites in this format, do not include explanations or extra text."
        }]
        ai_text = call_openrouter_chat("deepseek/deepseek-r1-distill-llama-70b", messages)

        print("\n🔎 Raw AI Output:\n" + ai_text + "\n")
        websites = extract_websites(ai_text)

        retries = 2
        while not websites and retries > 0:
            print("⚠️ Retrying with adjusted query...")
            time.sleep(2)
            messages[0]["content"] = f"Return exactly 7 websites for '{query}' in this format:\n\n**Website Name** - [Website Name](https://www.example.com)\nOnly return the websites in this format."
            ai_text = call_openrouter_chat("deepseek/deepseek-r1-distill-llama-70b", messages)
            websites = extract_websites(ai_text)
            retries -= 1

        if not websites:
            websites.append({"name": "No relevant websites found", "url": "#", "rating": None})

        sentiment_score = round(random.uniform(1, 5), 1)
        fake_news_score = round(random.uniform(1, 5), 1)
        clickbait_score = round(random.uniform(1, 5), 1)
        nsfw_score = round(random.uniform(1, 5), 1)

        search_history = session.get("search_history", [])
        if query not in search_history:
            search_history.insert(0, query)
            session["search_history"] = search_history[:5]

        result = {
            "query": query,
            "results": websites,
            "analysis": {
                "sentiment_score": sentiment_score,
                "fake_news_score": fake_news_score,
                "clickbait_score": clickbait_score,
                "nsfw_score": nsfw_score
            }
        }

        cached_results[query] = result
        save_cache(cached_results)
        return jsonify(result)

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"status": "error", "message": "No message provided"}), 400

        message = data['message']
        if not message.strip():
            return jsonify({"status": "error", "message": "Message cannot be empty"}), 400

        print(f"📝 Chat request: {message[:50]}...")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant for the Adaptive Content Rating System..."
            },
            {
                "role": "user",
                "content": message
            }
        ]
        ai_message = call_openrouter_chat("mistralai/mixtral-8x7b-instruct:free", messages)

        print(f"✅ Chat response generated successfully")
        return jsonify({
            "status": "success",
            "message": ai_message,
            "metadata": {
                "model": "mixtral-8x7b-instruct",
                "timestamp": time.time()
            }
        })

    except Exception as e:
        print(f"❌ Unexpected chat error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred. Please try again later."
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

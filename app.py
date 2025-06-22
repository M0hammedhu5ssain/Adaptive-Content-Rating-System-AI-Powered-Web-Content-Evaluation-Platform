import re
import time
import json
import random
from flask import Flask, request, jsonify, session, render_template, redirect
import openai
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ✅ Set OpenRouter API Key with DeepSeek model
openai.api_key = "yor_api_key_here"
openai.api_base = "https://openrouter.ai/api/v1"
# Set additional required headers for OpenRouter
openai.default_headers = {
    "HTTP-Referer": "https://adaptivecontentrating.com",  # Your site URL
    "X-Title": "Adaptive Content Rating System"  # Your app name
}

CACHE_FILE = "search_cache.json"  # ✅ JSON file for storing responses

# ✅ NSFW Keywords List
NSFW_KEYWORDS = ["sex", "porn", "nude", "xxx", "horny", "adult", "escort", "nsfw", "hot girls", "strip", "erotic"]

# ✅ Load Cache from File
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}  # If file is corrupted, return empty cache
    return {}

# ✅ Save Cache to File
def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache_data, file, indent=4)

# ✅ Function to Check if Query is NSFW
def is_nsfw(query):
    return any(word in query.lower() for word in NSFW_KEYWORDS)

# ✅ Function to Extract Websites Using Multiple Regex Patterns
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

# ✅ Route for Home Page (Landing page)
@app.route('/')
def index():
    # Redirect to home page as the landing page
    return redirect('/home')

# ✅ Route for Search Page
@app.route('/search')
def search_page():
    search_history = session.get("search_history", [])
    return render_template("index.html", search_history=search_history)

# ✅ Route for Home Page
@app.route('/home')
def home():
    return render_template("home.html")

# ✅ New Route for About Page
@app.route('/about')
def about():
    return render_template("about.html")

# ✅ New Route for Trends Page
@app.route('/trends')
def trends():
    return render_template("trends.html")

# ✅ New Route for User Dashboard
@app.route('/dashboard')
def dashboard():
    # Get search history for dashboard
    search_history = session.get("search_history", [])
    
    # Sample data for recently analyzed content
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

# ✅ New Route for FAQ Page
@app.route('/faq')
def faq():
    return render_template("faq.html")

# ✅ API Route for Searching Websites (with Caching)
@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Please provide a search query"}), 400

    # ✅ Load Cached Results
    cached_results = load_cache()

    if query in cached_results:
        print(f"✅ Using cached results for: {query}")
        return jsonify(cached_results[query])  # Return cached result instantly

    # ✅ Block NSFW Searches
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
        cached_results[query] = result  # Cache NSFW response
        save_cache(cached_results)
        return jsonify(result)

    try:
        print(f"🔍 Searching for: {query}")

        # ✅ Call OpenRouter API with DeepSeek R1 Distill Llama 70B model
        response = openai.ChatCompletion.create(
            model="deepseek/deepseek-r1-distill-llama-70b",  # Specific DeepSeek model on OpenRouter
            messages=[{"role": "user", "content": f"Return exactly 7 website recommendations for '{query}' in this strict format:\n\n"
                                                   f"**Website Name** - [Website Name](https://www.example.com)\n"
                                                   f"Only return the websites in this format, do not include explanations or extra text."}]
        )

        print("✅ OpenRouter API Response Received!")
        ai_text = response["choices"][0]["message"]["content"]
        print("\n🔎 Raw AI Output:\n" + ai_text + "\n")

        # ✅ Extract Websites
        websites = extract_websites(ai_text)

        # ✅ Retry if No Websites Found (Max 2 Times)
        retries = 2
        while not websites and retries > 0:
            print("⚠️ No websites found, retrying with adjusted query...")
            time.sleep(2)

            response = openai.ChatCompletion.create(
                model="deepseek/deepseek-r1-distill-llama-70b",  # Specific DeepSeek model on OpenRouter
                messages=[{"role": "user", "content": f"Return exactly 7 websites for '{query}' in this format:\n\n"
                                                       f"**Website Name** - [Website Name](https://www.example.com)\n"
                                                       f"Only return the websites in this format, no extra details."}]
            )

            ai_text = response["choices"][0]["message"]["content"]
            print("\n🔎 Retried AI Output:\n" + ai_text + "\n")

            websites = extract_websites(ai_text)
            retries -= 1

        if not websites:
            print("❌ No valid websites found after retries.")
            websites.append({"name": "No relevant websites found", "url": "#", "rating": None})

        # ✅ Sentiment Analysis & Fake News Detection
        analysis_response = openai.ChatCompletion.create(
            model="deepseek/deepseek-r1-distill-llama-70b",  # Specific DeepSeek model on OpenRouter
            messages=[{"role": "user", "content": f"Analyze the following query: '{query}'. Provide scores (out of 5) for Sentiment, Fake News, Clickbait, and NSFW Content."}]
        )

        # ✅ Generate Scores Randomly (Replace with AI API if Needed)
        sentiment_score = round(random.uniform(1, 5), 1)
        fake_news_score = round(random.uniform(1, 5), 1)
        clickbait_score = round(random.uniform(1, 5), 1)
        nsfw_score = round(random.uniform(1, 5), 1)

        # ✅ Store Search History
        search_history = session.get("search_history", [])
        if query not in search_history:
            search_history.insert(0, query)
            session["search_history"] = search_history[:5]

        # ✅ Prepare JSON Response
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

        # ✅ Save to Cache
        cached_results[query] = result
        save_cache(cached_results)

        return jsonify(result)

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ✅ Chat Bot API Endpoint
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({"status": "error", "message": "No message provided"}), 400
            
        message = data['message']
        
        # Check for empty messages
        if not message.strip():
            return jsonify({"status": "error", "message": "Message cannot be empty"}), 400
            
        # Log incoming chat request (for debugging)
        print(f"📝 Chat request: {message[:50]}...")
        
        try:
            # Use more reliable Mixtral model with higher token limit for complete responses
            response = openai.ChatCompletion.create(
                model="mistralai/mixtral-8x7b-instruct:free",  # More reliable model for complete sentences
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a helpful assistant for the Adaptive Content Rating System. 
                        You provide detailed information about how our system rates web content based on sentiment analysis, 
                        fake news detection, clickbait identification, and content safety. You're knowledgeable about AI, 
                        machine learning, content moderation, and web technologies. Always provide complete sentences and 
                        thorough explanations. Be friendly, professional and accurate."""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                temperature=0.7,
                max_tokens=100,  # Increased token limit to ensure complete responses
                timeout=20       # Increased timeout
            )
            
            # Extract response text
            ai_message = response["choices"][0]["message"]["content"]
            
            # Log success
            print(f"✅ Chat response generated successfully ({len(ai_message)} chars)")
            
            # Return success response
            return jsonify({
                "status": "success",
                "message": ai_message,
                "metadata": {
                    "model": "mixtral-8x7b-instruct",
                    "timestamp": time.time()
                }
            })
        
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            
            print(f"❌ Chat error: {error_type} - {error_msg}")
            
            # Fallback to alternative model if primary fails
            try:
                print("🔄 Attempting fallback to alternative model...")
                
                # Try Claude model as backup
                response = openai.ChatCompletion.create(
                    model="anthropic/claude-3-haiku:free",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You are a helpful assistant for the Adaptive Content Rating System. Provide clear and complete answers."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                
                # Extract response text
                ai_message = response["choices"][0]["message"]["content"]
                
                # Log success with fallback
                print(f"✅ Fallback chat response generated ({len(ai_message)} chars)")
                
                return jsonify({
                    "status": "success",
                    "message": ai_message,
                    "metadata": {
                        "model": "claude-fallback",
                        "timestamp": time.time()
                    }
                })
                
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {str(fallback_error)}")
                
                # If both models fail, return a predefined response
                return jsonify({
                    "status": "error",
                    "error": str(e),
                    "message": "I'm currently unable to provide a response. Our system rates web content based on sentiment analysis, fake news detection, clickbait identification, and content safety. Please try asking again later.",
                }), 500
                
    except Exception as e:
        print(f"❌ Unexpected chat error: {str(e)}")
        return jsonify({
            "status": "error", 
            "message": "An unexpected error occurred. Please try again later."
        }), 500

# ✅ Run Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

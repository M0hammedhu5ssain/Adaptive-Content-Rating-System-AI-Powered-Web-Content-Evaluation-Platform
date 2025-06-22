# Adaptive Content Rating System using AI

An intelligent web content rating system that evaluates websites based on sentiment analysis, fake news probability, clickbait potential, and NSFW content detection.

![image](https://github.com/user-attachments/assets/f033ce41-eaa6-4b4a-8eac-a32ee1c223c0)

![image](https://github.com/user-attachments/assets/7992cdc2-6c8e-4e73-b171-3aaae629fa5c)


## Features

- **Website Recommendations**: Get relevant website suggestions for your search queries

![image](https://github.com/user-attachments/assets/6a530612-9506-4c47-a327-50a678b6fa33)

- **Content Analysis**: Evaluate web content for sentiment, fake news potential, clickbait, and NSFW content
- **Safe Search**: Automatic filtering of NSFW search queries
- **User Dashboard**: Track your search history and content analysis results

![image](https://github.com/user-attachments/assets/8e9828b2-97f3-4a60-8b69-d462d03df8bd)

- **AI-Powered Chat Assistant**: Get information about the system and content ratings

![image](https://github.com/user-attachments/assets/b95606cc-05e9-4654-ac06-9bc4078eb7ba)

![image](https://github.com/user-attachments/assets/5a05898a-d66c-476d-85ad-e959126fb173)



## Technologies Used

- **Backend**: Python, Flask
- **API Integration**: OpenRouter API with DeepSeek and Mixtral models
- **Data Processing**: JSON for caching responses
- **Frontend**: HTML, CSS, JavaScript (Templates)

## Setup and Installation

1. Clone the repository
```
git clone https://github.com/krishnakanth6143/Adaptive-Content-Rating-System-using-AI.git
```

2. Install dependencies
```
pip install flask openai
```

3. Set your OpenRouter API key in app.py
```python
openai.api_key = "your_api_key_here"
```

4. Run the application
```
python app.py
```

5. Access the application at `http://localhost:5000`

## Project Structure

- `app.py`: Main Flask application with all routes and logic
- `templates/`: HTML templates for the web interface
  - `home.html`: Landing page
  - `index.html`: Search page
  - `dashboard.html`: User dashboard
  - `about.html`: About page
  - `faq.html`: Frequently asked questions
  - `trends.html`: Content trends

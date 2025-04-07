from flask import Flask, request, jsonify, render_template
import requests
import os
from flask_cors import CORS  # For handling CORS errors

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

@app.route('/')  # Serve index.html at the root URL
def index():
    return render_template('index.html')  # Use render_template

@app.route('/api/gemini', methods=['POST'])
def get_gemini_response():
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'Message is required'}), 400

        gemini_response = call_gemini_api(message)
        return jsonify({'response': gemini_response})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': 'An error occurred'}), 500

def call_gemini_api(message):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=GEMINI_API_KEY"  # **REPLACE THIS!**
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"  # Adjust if needed
    }
    request_body = {  # **ADJUST THIS BASED ON GEMINI API DOCS!**
        "model": "models/gemini-pro",  # Example
        "prompt": {
          "text": message
        }
    }

    try:
        response = requests.post(api_url, headers=headers, json=request_body)
        response.raise_for_status()
        data = response.json()
        return extract_gemini_text(data)  # Extract the text

    except requests.exceptions.RequestException as e:
        print(f"Gemini API Error: {e}")
        raise
    except (KeyError, IndexError) as e:
        print(f"Error parsing Gemini response: {e}, Data: {data}")
        raise

def extract_gemini_text(data):
    # **THIS IS CRUCIAL AND DEPENDS ON THE API!**
    try:
        return data['candidates'][0]['output']  # Example - **ADJUST!**
    except (KeyError, IndexError):
        print(f"Error extracting text: {data}")
        raise
print(GEMINI_API_KEY)
if __name__ == '__main__':
    app.run(debug=True)  # debug=False in production
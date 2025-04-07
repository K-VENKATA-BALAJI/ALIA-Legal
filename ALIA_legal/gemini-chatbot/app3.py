from flask import Flask, render_template, request, redirect, url_for
import os
import fitz  # PyMuPDF
from summarizer import Summarizer
import pytesseract
from PIL import Image
import requests
import warnings
from sklearn.exceptions import ConvergenceWarning

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to store extracted text
extracted_text = ""

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    global extracted_text
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        page_text = page.get_text()
        if not page_text.strip():  # If no text was extracted, try OCR
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
        text += page_text
    extracted_text = text  # Store the extracted text globally
    return text

# Function to summarize text
def summarize_text(text, num_sentences):
    model = Summarizer()
    summary = model(text, num_sentences=num_sentences)
    return summary

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Handle file upload
        pdf_file = request.files['pdf_file']
        num_sentences = int(request.form['num_sentences'])

        if pdf_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(file_path)

            # Process the PDF
            text = extract_text_from_pdf(file_path)
            summary = summarize_text(text, num_sentences)

            # Render results
            return render_template('result.html', text=text, summary=summary)

    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    question = request.form['question']
    answer = get_answer_from_gemini_ai(question, extracted_text)  # Use the global extracted text
    return {'answer': answer}
GEMINI_API_KEY="AIzaSyBa8VOem7ZMSZ46LguSkSfdYbUy-4hr7Tw"
def get_answer_from_gemini_ai(question, context):
    # Replace with your actual Gemini AI API endpoint and key
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GEMINI_API_KEY"  # Update with the correct endpoint
    headers = {
        "Authorization": "Bearer $GEMINI_API_KEY",  # Replace with your actual API key
        "Content-Type": "application/json"
    }
    data = {
        "question": question,
        "context": context
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json().get('answer', 'No answer found.')
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
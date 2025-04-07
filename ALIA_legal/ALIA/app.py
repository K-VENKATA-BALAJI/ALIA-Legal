from flask import Flask, render_template, request, session, json, redirect, url_for
from flask_session import Session
import os
import re
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import google.generativeai as genai
from summa import summarizer
import warnings
from sklearn.exceptions import ConvergenceWarning

# Configure Gemini API Key
genai.configure(api_key="AIzaSyBa8VOem7ZMSZ46LguSkSfdYbUy-4hr7Tw")

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=ConvergenceWarning)

# Flask App Configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = os.urandom(24)  # Secure secret key for session
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the server
Session(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Function to Extract Text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        page_text = page.get_text()
        if not page_text.strip():  # If no text is extracted, use OCR
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            page_text = pytesseract.image_to_string(img)
        text += page_text
    return text

# Function to Summarize Text
def summarize_text(text, max_sentences, ratio=0.1):
    summary = summarizer.summarize(text, ratio=ratio)
    sentences = summary.split(". ")
    short_summary = ". ".join(sentences[:max_sentences]) + "."
    return short_summary

session_cleared = False
@app.before_request
def clear_session_on_restart():
    global session_cleared
    if not session_cleared:  # Only clear session once when the server starts
        session.clear()
        session_cleared = True  # Set flag to True so it doesn't clear again

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        num_sentences = int(request.form['num_sentences'])

        if pdf_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(file_path)
            extracted_text = extract_text_from_pdf(file_path)

            # Store extracted text in session
            session['extracted_text'] = extracted_text
            session['num_sentences'] = num_sentences

            # Regex patterns for legal data extraction
            citation_pattern = r'(\d{4}[\s(]*[A-Z]+(?:\s[A-Z]+)*\s\d+|\(\d{4}\)\s\d+\s[A-Z]+\s\d+)'
            court_pattern = r'\b([A-Z\s]+COURT(?: OF [A-Z\s]+)?)\b'
            bench_pattern = r'Bench:\s*([A-Za-z\s.,&]+)'
            sp = r'\b[Ss]ection\s+\d+[A-Za-z]?\b'

            summary = summarize_text(extracted_text, num_sentences)

            # Case heading extraction
            match = re.search(r'([A-Za-z0-9.,& ]+)\s+vs\s+([A-Za-z0-9.,& ]+)', extracted_text)
            head1 = f"{match.group(1).strip()} vs {match.group(2).strip()}" if match else "Case heading not found"

            # Court extraction
            courts = re.findall(court_pattern, extracted_text)
            crtt = courts[0] if courts else "Court name not found"

            # Bench extraction
            bench = re.search(bench_pattern, extracted_text)
            benh = bench.group(1).strip().split("  ")[0] if bench else "Bench information not found"

            # Citations extraction
            cits = re.findall(citation_pattern, extracted_text)

            # Limit text length for Gemini (avoid input size issue)
            max_input_length = 2000  # Adjust as needed
            truncated_text = extracted_text[:max_input_length]
            sp1 = {match.capitalize() for match in re.findall(sp, extracted_text)}

            # Generate Conclusion using Gemini AI
            try:
                generation_config = {
                    "temperature": 1,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                    "response_mime_type": "text/plain",
                }
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config=generation_config,
                )
                chat_session = model.start_chat(history=[])
                prompt = f"Give the conclusion of the judgement in the following matter:\n\n{extracted_text}"
                response = chat_session.send_message(prompt)
                conclusion = response.text.strip()
            except Exception as e:
                print("Gemini API Error:", e)
                conclusion = "Could not generate conclusion due to API error."

            # Store extracted details in session
            session.update({
                'head1': head1,
                'crtt': crtt,
                'benh': benh,
                'cits': cits,
                'conclusion': conclusion,
                'summary': summary,
                'sec': sp1
            })

            return render_template('results.html', **session)

    return render_template('upload.html')

@app.route('/ask', methods=['POST'])
def search():
    query = request.form['search_query']
    results = ""

    if query:
        try:
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
                "response_mime_type": "text/plain",
            }
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )
            chat_session = model.start_chat(history=[])
            prompt = f"Answer the question: {query} using the following: {session.get('extracted_text')}"
            response = chat_session.send_message(prompt)
            results = response.text.strip()
        except Exception as e:
            print("Gemini API Error:", e)
            results = "Could not retrieve results due to API error."

    return render_template('results.html', query=query, results=results, **session)

@app.route('/explain', methods=['POST'])
def explain_text():
    data = request.get_json()
    selected_text = data.get('text', '').strip()

    if not selected_text:
        return json.dumps({'explanation': 'No text provided.'}), 400

    try:
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 1024,
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )
        chat_session = model.start_chat(history=[])
        prompt = f"Explain the following text in simple terms:\n\n{selected_text}"
        response = chat_session.send_message(prompt)
        explanation = response.text.strip()

        return json.dumps({'explanation': explanation})
    except Exception as e:
        print("Gemini API Error:", e)
        return json.dumps({'explanation': 'Could not generate explanation due to API error.'}), 500

@app.route('/reset', methods=['GET'])
def reset():
    session.clear()  # Clear all session data
    return redirect(url_for('index'))  # Redirect to the upload page

if __name__ == '__main__':
    app.run(debug=True)
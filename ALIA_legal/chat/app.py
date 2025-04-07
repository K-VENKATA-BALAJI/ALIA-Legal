from flask import Flask, render_template, request
import os
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
# from llama_cpp import Llama

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Sentence Transformer model for similarity search
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Load a local Llama 2 model
# llm = Llama(model_path="path/to/llama-2-7b.gguf")  # Update with your actual model path

# def chat_with_bot(prompt):
#     response = llm(prompt, max_tokens=256, temperature=0.7)
#     return response['choices'][0]['text'].strip()

import openai

# Set your OpenAI API key
openai.api_key = "your-openai-api-key"

def chat_with_bot(prompt):
    response = openai.chat.completions.create(
        model="gpt-4",  # Change to "gpt-3.5-turbo" if needed
        messages=[
            {"role": "system", "content": "You are an AI chatbot that answers questions based on user context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=256
    )
    return response.choices[0].message.content.strip()



# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = " ".join(page.get_text() for page in doc)
    return text

# Function to retrieve relevant text chunks for chat responses
def get_relevant_chunks(question, text):
    chunks = text.split("\n\n")  # Split into paragraphs
    question_embedding = embedding_model.encode(question, convert_to_tensor=True)
    chunk_embeddings = embedding_model.encode(chunks, convert_to_tensor=True)
    similarities = util.pytorch_cos_sim(question_embedding, chunk_embeddings)[0]
    
    # Get top 3 most relevant chunks
    top_chunks = sorted(zip(chunks, similarities), key=lambda x: x[1], reverse=True)[:3]
    return " ".join([chunk for chunk, _ in top_chunks])

@app.route("/", methods=["GET", "POST"])
def upload_pdf():
    global extracted_text
    if request.method == "POST":
        pdf_file = request.files["pdf_file"]
        if pdf_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(file_path)
            extracted_text = extract_text_from_pdf(file_path)
            return render_template("chat.html")
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    global extracted_text
    user_question = request.form["user_question"]
    
    # Retrieve relevant text from the document
    relevant_context = get_relevant_chunks(user_question, extracted_text)
    
    # Generate chatbot response
    bot_response = chat_with_bot(f"Context: {relevant_context}\n\nUser: {user_question}")
    
    return render_template("chat.html", user_question=user_question, bot_response=bot_response)

if __name__ == "__main__":
    app.run(debug=True)

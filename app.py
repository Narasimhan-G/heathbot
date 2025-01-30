from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import nltk
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader  # Import PdfReader from PyPDF2
from docx import Document # Import Document from docx

from dotenv import load_dotenv

load_dotenv()

nltk.download('punkt')
nltk.download('wordnet')

app = Flask(__name__)
# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

generation_config = {
    "temperature": 0.8,
    "top_p": 0.9,
    "top_k": 30,
    "max_output_tokens": 2000, # Adjust this if needed
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

@app.route("/")
def index():
    return render_template("index.html")


def extract_text_from_document(file_path):
    """Extract text from different types of documents."""
    if file_path.lower().endswith(".pdf"):
            try:
                text = ""
                with open(file_path, 'rb') as file:
                  reader = PdfReader(file)
                  for page in reader.pages:
                    text += page.extract_text()
                return text
            except Exception as e:
                  return f"Error: Could not extract text from pdf: {e}"
    elif file_path.lower().endswith((".doc", ".docx")):
         try:
              doc = Document(file_path)
              text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
              return text
         except Exception as e:
            return f"Error: Could not extract text from doc/docx: {e}"
    else:
        return "Error: Unsupported document type."


@app.route("/get_response", methods=["POST"])
def get_bot_response():
    user_input = request.form.get("user_input", "")
    uploaded_file = request.files.get("document")

    if uploaded_file:
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)
        document_text = extract_text_from_document(file_path)
        if "Error" in document_text:
            response = f"Could not parse this file type. Please try again"
        else:
            user_input += f" The user has uploaded this document and needs help with it: {document_text}"
            response = chat_session.send_message(user_input).text
    else:
        response = chat_session.send_message(user_input).text

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=False)
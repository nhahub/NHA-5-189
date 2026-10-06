"""Document parsing and text preprocessing used by Notebook 1."""

import os
import re

import PyPDF2
import docx
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == '.pdf':
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"
        elif ext == '.docx':
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            text = "Unsupported format."
    except Exception as e:
        text = f"Error reading file: {e}"

    return text

def extract_resume_sections(text):
    text = str(text)
    sections = {'Experience': '', 'Education': '', 'Skills': ''}

    # Simple, readable regex capturing everything between standard headers
    exp_match = re.search(r"Experience(.*?)(Education|Skills|$)", text, re.IGNORECASE | re.DOTALL)
    edu_match = re.search(r"Education(.*?)(Experience|Skills|$)", text, re.IGNORECASE | re.DOTALL)
    skills_match = re.search(r"Skills(.*?)(Experience|Education|$)", text, re.IGNORECASE | re.DOTALL)

    if exp_match:
        sections['Experience'] = exp_match.group(1).strip()
    if edu_match:
        sections['Education'] = edu_match.group(1).strip()
    if skills_match:
        sections['Skills'] = skills_match.group(1).strip()

    return sections

def clean_text(text):

    # Convert text to lowercase
    text = str(text).lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+", "", text)

    # Remove unwanted special characters
    text = re.sub(r"[^a-zA-Z0-9\s+#.]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def prepare_nlp():
    tokenizer = RegexpTokenizer(r'[A-Za-z][A-Za-z0-9+#]*')
    stop_words = set(stopwords.words("english"))
    lemmatizer = WordNetLemmatizer()
    return tokenizer, stop_words, lemmatizer

def preprocess_nlp(text, tokenizer, stop_words, lemmatizer):

    tokens = tokenizer.tokenize(text)

    tokens = [word for word in tokens if word not in stop_words]

    tokens = [lemmatizer.lemmatize(word) for word in tokens]

    return tokens

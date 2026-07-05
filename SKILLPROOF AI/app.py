from flask import Flask, render_template, request
import PyPDF2
import google.generativeai as genai
import os
import json

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

genai.configure(api_key="GEMINI_API_KEY")
model = genai.GenerativeModel('gemini-2.5-flash')

# Fallback values used only if Gemini skips a field, so the page never shows blanks
DEFAULTS = {
    "score": 50,
    "skills_found": [],
    "skills_missing": [],
    "job_roles": [],
    "suggestions": [],
    "interview_questions": [],
    "linkedin_headline": "",
    "professional_summary": "",
    "executive_summary": "",
    "learning_path": [],
    "matching_roles": [],
    "hard_skills": [],
    "soft_skills": []
}


def extract_text(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['resume']
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    resume_text = extract_text(path)

    prompt = f"""
    You are an expert technical recruiter. Analyze the resume below and respond with
    ONLY a single valid JSON object - no markdown, no commentary, no missing keys.
    Every key listed below MUST be present and non-empty, even if you have to make a
    reasonable estimate.

    Return exactly this JSON structure (fill in real values based on the resume):
    {{
      "score": 75,
      "skills_found": ["skill1", "skill2"],
      "skills_missing": ["skill1", "skill2"],
      "job_roles": ["role1", "role2"],
      "suggestions": ["suggestion1", "suggestion2"],
      "interview_questions": ["q1", "q2", "q3", "q4", "q5"],
      "linkedin_headline": "one line headline",
      "professional_summary": "2-3 sentence summary",
      "executive_summary": "a recruiter-style pitch paragraph, 3-5 sentences, about this specific candidate",
      "learning_path": [{{"skill": "missing skill", "resource": "a real learning resource name"}}],
      "matching_roles": [{{"name": "role name", "percent": 80}}],
      "hard_skills": ["technical skill1", "technical skill2"],
      "soft_skills": ["soft skill1", "soft skill2"]
    }}

    "learning_path" must have one entry per skill in "skills_missing" (max 5).
    "matching_roles" must have exactly 3 roles with a fit percentage (0-100).

    Resume:
    {resume_text}
    """

    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    raw = response.text.strip().replace('```json', '').replace('```', '')
    data = json.loads(raw)

    # Fill in anything Gemini happened to skip, so no section ever shows blank
    for key, default in DEFAULTS.items():
        data.setdefault(key, default)

    return render_template('result.html', data=data)


if __name__ == '__main__':
    app.run(debug=True)

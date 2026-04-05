import streamlit as st
from datetime import date
import PyPDF2
import json
import random
import re
import os

st.set_page_config(page_title="EduVerse", layout="centered")

# -----------------------------
# 🎨 UI
# -----------------------------
st.markdown("""
<style>
.block-container {max-width: 420px; margin:auto;}
body {background-color: #F5F2FF;}

.card {
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin: 10px 0;
}

.stButton button {
    background-color: #6C4DF6;
    color: white;
    border-radius: 12px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

st.image(".assets/puppy.png", width=80)
st.title("EduVerse 💜")

QUIZ_FILE = "quiz.json"
PROGRESS_FILE = "progress.json"

# -----------------------------
# 🧠 ADVANCED GENERATOR
# -----------------------------
def generate_mcqs(text):

    text = text.replace("\n", " ")

    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 40]

    random.shuffle(sentences)

    questions = []
    topics = {}

    for s in sentences:

        words = s.split()
        keywords = [w for w in words if len(w) > 5]

        if not keywords:
            continue

        answer = random.choice(keywords)

        topic = answer.lower()
        topics.setdefault(topic, []).append(s)

        # -------------------
        # MCQ
        # -------------------
        question = s.replace(answer, "_____")

        options = [answer]
        pool = list(set(text.split()))
        random.shuffle(pool)

        for w in pool:
            if w != answer and len(w) > 4 and len(options) < 4:
                options.append(w)

        random.shuffle(options)

        questions.append({
            "type": "mcq",
            "question": question,
            "options": options,
            "answer": answer,
            "explanation": f"{answer} is an important concept."
        })

        # -------------------
        # TRUE/FALSE
        # -------------------
        if random.random() > 0.5:
            false_word = random.choice(pool)
            tf_q = s.replace(answer, false_word)

            questions.append({
                "type": "tf",
                "question": tf_q,
                "options": ["True", "False"],
                "answer": "False",
                "explanation": f"Correct term is {answer}"
            })
        else:
            questions.append({
                "type": "tf",
                "question": s,
                "options": ["True", "False"],
                "answer": "True",
                "explanation": "Statement is correct"
            })

        # -------------------
        # FLASHCARD
        # -------------------
        questions.append({
            "type": "flashcard",
            "question": f"What is {answer}?",
            "answer": s,
            "options": [],
            "explanation": s
        })

        if len(questions) >= 15:
            break

    # -------------------
    # MATCH THE FOLLOWING
    # -------------------
    match_pairs = []

    for k, v in list(topics.items())[:5]:
        match_pairs.append((k, v[0][:50]))

    if match_pairs:
        questions.append({
            "type": "match",
            "pairs": match_pairs
        })

    return questions


# -----------------------------
# TEXT
# -----------------------------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# -----------------------------
# SAVE / LOAD
# -----------------------------
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def load_json(file, default):
    if os.path.exists(file):
        with open(file) as f:
            return json.load(f)
    return default


# -----------------------------
# INIT
# -----------------------------
progress = load_json(PROGRESS_FILE, {
    "index": 0,
    "score": 0,
    "xp": 0,
    "level": 1,
    "hearts": 3,
    "streak": 0,
    "last_played": ""
})

# -----------------------------
# STREAK
# -----------------------------
today = str(date.today())

if progress["last_played"] != today:
    progress["streak"] += 1
    progress["last_played"] = today
    save_json(PROGRESS_FILE, progress)

questions = load_json(QUIZ_FILE, [])

# -----------------------------
# DISPLAY
# -----------------------------
st.write(f"⭐ XP: {progress['xp']} | 🏆 Level: {progress['level']}")
st.write("❤️ " * progress["hearts"])
st.write(f"🔥 Streak: {progress['streak']}")

# -----------------------------
# UPLOAD
# -----------------------------
uploaded = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded:
    text = extract_text(uploaded)
    questions = generate_mcqs(text)

    save_json(QUIZ_FILE, questions)

    progress["index"] = 0
    progress["score"] = 0
    progress["hearts"] = 3

    save_json(PROGRESS_FILE, progress)

    st.success("Quiz Ready 🚀")

# -----------------------------
# QUIZ ENGINE
# -----------------------------
if questions:

    index = progress["index"]

    if index < len(questions):

        q = questions[index]

        st.markdown('<div class="card">', unsafe_allow_html=True)

        # -------------------
        # MCQ / TF
        # -------------------
        if q["type"] in ["mcq", "tf"]:

            st.write(q["question"])
            ans = st.radio("Choose:", q["options"], key=index)

            if st.button("Submit"):

                if ans == q["answer"]:
                    st.success("Correct!")
                    progress["xp"] += 20
                    progress["score"] += 1
                else:
                    st.error("Wrong!")
                    progress["hearts"] -= 1

                progress["index"] += 1
                save_json(PROGRESS_FILE, progress)
                st.rerun()

        # -------------------
        # FLASHCARD
        # -------------------
        elif q["type"] == "flashcard":

            st.write(q["question"])

            if st.button("Show Answer"):
                st.info(q["answer"])

                if st.button("Next"):
                    progress["index"] += 1
                    save_json(PROGRESS_FILE, progress)
                    st.rerun()

        # -------------------
        # MATCH
        # -------------------
        elif q["type"] == "match":

            st.write("Match the following:")

            for pair in q["pairs"]:
                st.write(f"{pair[0]}  →  {pair[1]}")

            if st.button("Next"):
                progress["index"] += 1
                save_json(PROGRESS_FILE, progress)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.success("🎉 Completed!")

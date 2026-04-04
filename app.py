import streamlit as st
from datetime import date
import PyPDF2
import json
import random
import re
import os

st.set_page_config(page_title="EduVerse", layout="centered")

# -----------------------------
# 🎨 PURPLE UI THEME
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
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
}

.stButton button {
    background-color: #6C4DF6;
    color: white;
    border-radius: 12px;
    padding: 10px;
    font-weight: bold;
    width: 100%;
}

.stButton button:hover {
    background-color: #5B3FD4;
}

.level-circle {
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: #6C4DF6;
    color: white;
    display:flex;
    align-items:center;
    justify-content:center;
    margin: 5px;
}

.locked {background: #CFC8FF;}

.progress-bar {
    height: 10px;
    background: #E5DEFF;
    border-radius: 10px;
}

.progress-fill {
    height: 10px;
    background: #6C4DF6;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# 🐶 HEADER
# -----------------------------
st.image("puppy.png", width=80)
st.title("EduVerse 💜")

QUIZ_FILE = "quiz.json"
PROGRESS_FILE = "progress.json"

# -----------------------------
# MCQ GENERATOR
# -----------------------------
def generate_mcqs(text):
    sentences = re.split(r'\.|\n', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    questions = []

    for s in sentences[:5]:
        words = s.split()
        important_words = [w for w in words if len(w) > 4]

        if not important_words:
            continue

        answer = random.choice(important_words)
        question = s.replace(answer, "_____")

        options = [answer]
        random_words = list(set(text.split()))
        random.shuffle(random_words)

        for w in random_words:
            if w != answer and len(options) < 4 and len(w) > 4:
                options.append(w)

        random.shuffle(options)

        questions.append({
            "question": question,
            "options": options,
            "answer": answer,
            "explanation": f"The correct word is '{answer}'."
        })

    return questions

# -----------------------------
# TEXT EXTRACTION
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
# INIT DATA
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
# 🔥 STREAK LOGIC
# -----------------------------
today = str(date.today())

if progress["last_played"] != today:
    yesterday = str(date.fromordinal(date.today().toordinal() - 1))

    if progress["last_played"] == yesterday:
        progress["streak"] += 1
    else:
        progress["streak"] = 1

    progress["last_played"] = today
    save_json(PROGRESS_FILE, progress)

questions = load_json(QUIZ_FILE, [])

# -----------------------------
# 📊 DISPLAY
# -----------------------------
st.write(f"⭐ XP: {progress['xp']} | 🏆 Level: {progress['level']}")
st.write("❤️ " * progress["hearts"])
st.write(f"🔥 Streak: {progress['streak']}")

xp_progress = progress["xp"] % 100

st.markdown(
    f"""
    <div class="progress-bar">
        <div class="progress-fill" style="width:{xp_progress}%"></div>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# 🗺️ LEVEL PATH
# -----------------------------
st.subheader("Learning Path")

cols = st.columns(5)

for i in range(5):
    if i + 1 <= progress["level"]:
        cols[i].markdown(
            f"<div class='level-circle'>{i+1}</div>",
            unsafe_allow_html=True
        )
    else:
        cols[i].markdown(
            f"<div class='level-circle locked'>🔒</div>",
            unsafe_allow_html=True
        )

# -----------------------------
# 📄 UPLOAD
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

    st.success("New Quiz Ready 🎉")

# -----------------------------
# 🎮 QUIZ
# -----------------------------
if questions:

    index = progress["index"]

    if index < len(questions):

        q = questions[index]

        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.write(f"### Q{index+1}")
        st.write(q["question"])

        ans = st.radio("Choose:", q["options"], key=index)

        if st.button("Submit"):

            if ans == q["answer"]:
                st.success("🐶 Correct!")
                progress["score"] += 1
                progress["xp"] += 20

            else:
                st.error("Wrong!")
                st.write(q["explanation"])

                progress["hearts"] -= 1

                if progress["hearts"] <= 0:
                    st.error("💔 Game Over!")

                    if st.button("Restart"):
                        progress["index"] = 0
                        progress["score"] = 0
                        progress["hearts"] = 3
                        save_json(PROGRESS_FILE, progress)
                        st.rerun()

                    st.stop()

            progress["index"] += 1

            if progress["xp"] >= 100:
                progress["level"] += 1
                progress["xp"] = 0
                st.success("🏆 Level Up!")

            save_json(PROGRESS_FILE, progress)

            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.subheader("🎉 Quiz Completed!")
        st.write(f"Score: {progress['score']} / {len(questions)}")

        if st.button("Restart"):
            progress["index"] = 0
            progress["score"] = 0
            progress["hearts"] = 3
            save_json(PROGRESS_FILE, progress)
            st.rerun()
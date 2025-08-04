import streamlit as st
import os
import json
from PIL import Image
from datetime import datetime
import pandas as pd
import traceback

# --- Page Setup ---
st.set_page_config(page_title="TCE Session Interaction Dashboard", layout="centered")
logo_path = r"tce_dashboard\TCE.png"
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    st.image(logo, width=220)

# --- Custom CSS ---
def load_custom_css():
    st.markdown("""
    <style>
    body {
        background: linear-gradient(135deg, #667eea, #764ba2);
    }
    .link {
        margin-top: 1rem;
        font-size: 0.9rem;
    }
    .link a {
        color: #764ba2;
        text-decoration: none;
    }
    .link a:hover {
        text-decoration: underline;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Persistence Helpers ---
def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    raise json.JSONDecodeError("Empty file", content, 0)
                return json.loads(content)
        except json.JSONDecodeError as e:
            st.warning(f"Invalid JSON in {filename}. Resetting to default.")
            st.text(traceback.format_exc())
            save_json(filename, default)
    return default

def save_json(filename, data):
    def custom_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=custom_serializer)

USERS_FILE = 'users.json'
QUESTIONS_FILE = 'questions.json'
RESPONSES_FILE = 'responses.json'

# --- Session State Initialization ---
if 'users' not in st.session_state:
    st.session_state['users'] = load_json(USERS_FILE, [])
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'questions' not in st.session_state:
    st.session_state['questions'] = load_json(QUESTIONS_FILE, [])
if 'responses' not in st.session_state:
    st.session_state['responses'] = load_json(RESPONSES_FILE, [])

# --- Forms ---
def login_form():
    load_custom_css()
    st.markdown("<h2>Login</h2>", unsafe_allow_html=True)

    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        if username == "admin" and password == "AdminTCE":
            st.session_state['current_user'] = {'username': 'admin'}
            st.success("Logged in as Admin")
            st.rerun()
        else:
            user = next((u for u in st.session_state['users'] if u['username'] == username and u['password'] == password), None)
            if user:
                st.session_state['current_user'] = user
                st.success(f"Welcome, {user['username']}!")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.markdown('<div class="link">Not a member? <a href="#Register">Sign up</a></div>', unsafe_allow_html=True)

def register_form():
    load_custom_css()
    st.markdown("<h2>Register</h2>", unsafe_allow_html=True)

    username = st.text_input("Choose Username", key="register_user")
    password = st.text_input("Choose Password", type="password", key="register_pass")
    batch = st.selectbox("Select Bootcamp Batch", ["Boot Camp Batch 1", "Boot Camp Batch 2"])

    if st.button("Register"):
        if not username or not password:
            st.warning("Please fill all fields.")
        elif username.lower() == "admin":
            st.error("Username 'admin' is reserved.")
        elif any(u['username'] == username for u in st.session_state['users']):
            st.warning("Username already taken.")
        else:
            st.session_state['users'].append({'username': username, 'password': password, 'batch': batch})
            save_json(USERS_FILE, st.session_state['users'])
            st.success("Registered successfully! Please login.")
    st.markdown('<div class="link">Already a member? <a href="#Login">Login</a></div>', unsafe_allow_html=True)

# --- Admin Dashboard ---
def admin_dashboard():
    st.title("Admin Dashboard")
    tab = st.radio(
        "Select Section",
        ["Register Students", "Question Save", "Questions Launch", "Student Response"],
        horizontal=True,
        key="admin_tab_radio"
    )

    if tab == "Register Students":
        st.header("Registered Students by Batch")
        batch1 = [u['username'] for u in st.session_state['users'] if u['batch'] == "Boot Camp Batch 1"]
        batch2 = [u['username'] for u in st.session_state['users'] if u['batch'] == "Boot Camp Batch 2"]
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Boot Camp Batch 1")
            if batch1:
                df1 = pd.DataFrame({'Name': batch1})
                df1.index += 1
                df1.index.name = 'Sl. No.'
                st.table(df1)
            else:
                st.write("No students registered yet.")
        with col2:
            st.subheader("Boot Camp Batch 2")
            if batch2:
                df2 = pd.DataFrame({'Name': batch2})
                df2.index += 1
                df2.index.name = 'Sl. No.'
                st.table(df2)
            else:
                st.write("No students registered yet.")

    elif tab == "Question Save":
        st.header("Create New Question")
        question = st.text_input("Enter Question", key="admin_q_text")
        image_file = st.file_uploader("Upload Image (optional)", type=["png", "jpg", "jpeg"], key="admin_q_img")
        image_path = None
        if image_file is not None:
            img_dir = "question_images"
            os.makedirs(img_dir, exist_ok=True)
            image_path = os.path.join(img_dir, image_file.name)
            with open(image_path, "wb") as f:
                f.write(image_file.getbuffer())
            st.image(image_path, caption="Image Preview", width=200)
        qtype = st.selectbox("Question Type", ["MCQ", "Text"], key="admin_q_type")
        options = []
        answer = ""
        if qtype == "MCQ":
            opt1 = st.text_input("Option 1", key="admin_opt1")
            opt2 = st.text_input("Option 2", key="admin_opt2")
            opt3 = st.text_input("Option 3", key="admin_opt3")
            opt4 = st.text_input("Option 4", key="admin_opt4")
            options = [opt1, opt2, opt3, opt4]
            correct_idx = st.radio("Select the correct option", options, key="admin_correct_radio")
            answer = correct_idx
        else:
            answer = st.text_input("Correct Answer", key="admin_q_ans_text")
        if st.button("Save Question", key="admin_save_q"):
            st.session_state['questions'].append({
                "question": question,
                "image": image_path if image_path else None,
                "type": qtype,
                "options": options if qtype == "MCQ" else [],
                "answer": answer
            })
            save_json(QUESTIONS_FILE, st.session_state['questions'])
            st.success("Question saved successfully")

    elif tab == "Questions Launch":
        st.header("Questions Launch")
        if not st.session_state['questions']:
            st.info("No questions saved yet.")
        else:
            for idx, q in enumerate(st.session_state['questions']):
                st.markdown(f"**Q{idx + 1}:** {q['question']}")
                if q.get('image'):
                    st.image(q['image'], caption="Question Image", width=350)
                if q['type'] == "MCQ":
                    st.markdown(f"Options: {', '.join(q['options'])}")
                st.markdown(f"Answer: {q['answer']}")
                if 'launched' not in q:
                    if st.button(f"Launch Q{idx + 1}", key=f"launch_{idx}"):
                        q['launched'] = True
                        q['launch_timestamp'] = datetime.now().isoformat()
                        save_json(QUESTIONS_FILE, st.session_state['questions'])
                        st.success(f"Question Q{idx + 1} launched!")
                elif q.get('launched'):
                    st.info("Launched")
                st.markdown("---")

    elif tab == "Student Response":
        st.header("Student Responses")
        if not st.session_state['responses']:
            st.info("No responses yet.")
        else:
            df = pd.DataFrame(st.session_state['responses'])
            summary = []
            for q in st.session_state['questions']:
                q_responses = df[df['question'] == q['question']]
                total = len(q_responses)
                correct = sum(1 for _, row in q_responses.iterrows() if row['response'] == q.get('answer'))
                users_in_class = [u['username'] for u in st.session_state['users'] if u['batch'] == q.get('batch')]
                not_answered = len(set(users_in_class)) - len(set(q_responses['user']))
                summary.append({
                    'Question': q['question'],
                    'Total Answers': total,
                    'Correct': correct,
                    'Incorrect': total - correct,
                    'Not Answered': not_answered,
                    'First Answered By': q_responses.iloc[0]['user'] if not q_responses.empty else '-'
                })
            st.dataframe(pd.DataFrame(summary))

# --- Student Dashboard ---
def student_dashboard():
    st.title("Student Dashboard")
    st.write(f"Welcome, {st.session_state['current_user']['username']}")
    user = st.session_state['current_user']['username']
    answered_questions = set(r['question'] for r in st.session_state['responses'] if r['user'] == user)
    for q in st.session_state['questions']:
        if not q.get('launched') or q['question'] in answered_questions:
            continue
        st.subheader(q['question'])
        if q.get('image'):
            st.image(q['image'], caption="Question Image", width=350)
        if q['type'] == "MCQ":
            selected = st.radio("Options", q['options'], key=q['question'])
        else:
            selected = st.text_input("Your Answer", key=q['question'])
        if st.button(f"Submit Answer to: {q['question']}"):
            st.session_state['responses'].append({
                'user': user,
                'question': q['question'],
                'response': selected,
                'response_timestamp': datetime.now()
            })
            save_json(RESPONSES_FILE, st.session_state['responses'])
            st.success("Answer submitted")

# --- Main ---
if not st.session_state['current_user']:
    tab1, tab2 = st.tabs(["Login", "Register"])
    with tab1:
        login_form()
    with tab2:
        register_form()
else:
    if st.session_state['current_user']['username'] == 'admin':
        admin_dashboard()
    else:
        student_dashboard()

    if st.button("Logout"):
        st.session_state['current_user'] = None
        st.rerun()

    if st.session_state['current_user']['username'] != 'admin':
        df = pd.DataFrame(st.session_state['responses'])
        user_responses = df[df['user'] == st.session_state['current_user']['username']]
        if not user_responses.empty:
            st.subheader("Your Responses")
            st.dataframe(user_responses)

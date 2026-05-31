import streamlit as st
import pymysql
import requests
import bcrypt
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ------------------------------
# DATABASE CONNECTION
# ------------------------------
def get_db():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="root",   # your mysql password
        database="generative_ai",
        cursorclass=pymysql.cursors.DictCursor
    )

# ------------------------------
# REGISTER USER
# ------------------------------
def register_user(name, email, password):
    db = get_db()
    cursor = db.cursor()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        cursor.execute(
            "INSERT INTO users(name,email,password) VALUES(%s,%s,%s)",
            (name, email, hashed.decode())
        )

        db.commit()
        return True

    except:
        return False


# ------------------------------
# LOGIN USER
# ------------------------------
def login_user(email, password):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email,)
    )

    user = cursor.fetchone()

    if user and bcrypt.checkpw(
        password.encode(),
        user["password"].encode()
    ):
        return user

    return None


# ------------------------------
# SAVE HISTORY
# ------------------------------
def save_history(user_id, prompt, response, type):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "INSERT INTO history(userid,prompt,response,type) VALUES(%s,%s,%s,%s)",
        (user_id, prompt, response, type)
    )

    db.commit()


# ------------------------------
# LOAD HISTORY
# ------------------------------
def load_history(user_id):
    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM history WHERE userid=%s ORDER BY created_at DESC",
        (user_id,)
    )

    return cursor.fetchall()


# ------------------------------
# GROQ CLIENT
# ------------------------------
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ------------------------------
# TEXT GENERATION
# ------------------------------
def generate_text(prompt):

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content


# ------------------------------
# IMAGE GENERATION
# ------------------------------
def generate_image(prompt):

    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"

    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json={"inputs": prompt}
    )

    image_path = "generated_image.png"

    with open(image_path, "wb") as f:
        f.write(response.content)

    return image_path


# ------------------------------
# STREAMLIT CONFIG
# ------------------------------
st.set_page_config(
    page_title="GenAI Tool",
    layout="wide"
)

# ------------------------------
# SESSION STATE
# ------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None


# ------------------------------
# LOGIN PAGE
# ------------------------------
def login_ui():

    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        user = login_user(email, password)

        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("Login Successful")
            st.rerun()

        else:
            st.error("Invalid Email or Password")


# ------------------------------
# REGISTER PAGE
# ------------------------------
def register_ui():

    st.title("📝 Register")

    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):

        if register_user(name, email, password):
            st.success("Account Created Successfully")

        else:
            st.error("Email Already Exists")


# ------------------------------
# DASHBOARD
# ------------------------------
def dashboard():

    st.sidebar.title("📜 History")

    history_list = load_history(
        st.session_state.user["id"]
    )

    for h in history_list:
        st.sidebar.write(f"📝 {h['prompt'][:30]}")

    st.sidebar.markdown("---")

    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.rerun()

    st.title("🤖 GenAI Notes & Image Generator")

    tab1, tab2 = st.tabs([
        "✍️ Text Generator",
        "🖼️ Image Generator"
    ])

    # ---------------- TEXT ----------------
    with tab1:

        topic = st.text_input(
            "Enter topic for notes"
        )

        if st.button("Generate Notes"):

            if topic.strip():

                response = generate_text(topic)

                st.write(response)

                save_history(
                    st.session_state.user["id"],
                    topic,
                    response,
                    "text"
                )

    # ---------------- IMAGE ----------------
    with tab2:

        img_prompt = st.text_input(
            "Enter image prompt"
        )

        if st.button("Generate Image"):

            if img_prompt.strip():

                with st.spinner("Generating image..."):

                    image_path = generate_image(img_prompt)

                    st.image(
                        image_path,
                        caption="Generated Image",
                        use_container_width=True
                    )

                    save_history(
                        st.session_state.user["id"],
                        img_prompt,
                        image_path,
                        "image"
                    )


# ------------------------------
# APP FLOW
# ------------------------------
menu = ["Login", "Register"]

if not st.session_state.authenticated:

    choice = st.sidebar.selectbox(
        "Menu",
        menu
    )

    if choice == "Login":
        login_ui()

    else:
        register_ui()

else:
    dashboard()
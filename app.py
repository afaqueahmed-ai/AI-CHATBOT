import os
import time
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="AI Assistant | Afaque Aftab Solangi",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

MAX_HISTORY_MESSAGES = 10
MAX_RETRIES = 3

st.markdown(
    """
    <style>
    .welcome-banner {
        background: linear-gradient(135deg, #4F46E5 0%, #0EA5E9 100%);
        color: white;
        padding: 18px 22px;
        border-radius: 14px;
        margin-bottom: 16px;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.08);
    }
    .welcome-banner h2 {
        margin: 0 0 4px 0;
        font-size: 1.45rem;
        color: white;
    }
    .welcome-banner p {
        margin: 0;
        font-size: 0.95rem;
        opacity: 0.95;
        color: #F8FAFC;
    }
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

LANGUAGES = [
    "Auto-Detect (Match User Language)",
    "English",
    "Urdu",
    "Hindi",
    "Arabic",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Russian",
    "Chinese (Simplified)",
    "Japanese",
    "Korean",
    "Turkish",
    "Persian (Farsi)",
    "Bengali",
    "Punjabi",
    "Indonesian",
    "Malay",
    "Vietnamese",
    "Thai",
    "Dutch",
    "Polish",
    "Swedish",
    "Greek",
    "Hebrew",
    "Swahili",
]

if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "guest_mode" not in st.session_state:
    st.session_state.guest_mode = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_language" not in st.session_state:
    st.session_state.selected_language = "Auto-Detect (Match User Language)"


def get_api_key() -> str | None:
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"]
    return st.session_state.get("sidebar_api_key") or None


@st.cache_resource
def get_cached_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def build_system_instruction(language: str) -> str:
    if language == "Auto-Detect (Match User Language)":
        lang_rule = (
            "Automatically detect the language of the user's latest message and reply "
            "fluently in that exact same language (supporting 25+ world languages)."
        )
    else:
        lang_rule = (
            f"Always respond fluently and naturally in {language}, even if the user "
            "writes in another language, unless they explicitly ask to switch languages."
        )

    return (
        "You are a helpful, clear, accurate, and well-structured AI assistant created by "
        "Afaque Aftab Solangi. Format responses cleanly with headings, bullet points, "
        "bold highlights, and code blocks when helpful—similar to modern AI assistants "
        f"like Gemini, ChatGPT, and Claude. {lang_rule}"
    )


def generate_ai_reply(api_key: str, history: list[dict], language: str) -> str:
    client = get_cached_client(api_key)

    recent_history = history[-MAX_HISTORY_MESSAGES:]
    contents = []
    for msg in recent_history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg["content"])],
            )
        )

    config = types.GenerateContentConfig(
        system_instruction=build_system_instruction(language),
        temperature=0.7,
    )

    models_to_try = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    last_err = "Unknown error"
    last_err = "Unknown error"

    for attempt in range(MAX_RETRIES):
        model_name = models_to_try[min(attempt, len(models_to_try) - 1)]
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            text = (response.text or "").strip()
            if text:
                return text
except Exception as exc:
            last_err = str(exc)
            time.sleep(1.0 * (2**attempt))

    return f"API/Model issue: {last_err}"


st.markdown(
    """
    <div class="welcome-banner">
        <h2>Welcome by Afaque Aftab Solangi</h2>
        <p>Multilingual AI Assistant • 25+ Languages • Optional Gmail Sign-In or Guest Access</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings & Account")

    if st.session_state.user_email:
        st.success(f"Signed in: {st.session_state.user_email}")
        if st.button("Sign Out", use_container_width=True):
            st.session_state.user_email = None
            st.session_state.guest_mode = False
            st.rerun()
    elif st.session_state.guest_mode:
        st.info("Mode: Guest User")
        if st.button("Sign In with Gmail", use_container_width=True):
            st.session_state.guest_mode = False
            st.rerun()

    st.divider()

    st.session_state.selected_language = st.selectbox(
        "Response Language",
        options=LANGUAGES,
        index=LANGUAGES.index(st.session_state.selected_language),
    )

    if "GEMINI_API_KEY" not in st.secrets and not os.environ.get("GEMINI_API_KEY"):
        st.text_input(
            "Gemini API Key",
            type="password",
            key="sidebar_api_key",
            help="Add GEMINI_API_KEY in Streamlit Secrets for 24/7 deployment.",
        )

    st.divider()
    if st.button("Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.user_email and not st.session_state.guest_mode:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Sign In or Continue as Guest")
        st.write(
            "Enter your Gmail address to personalize your session, or continue directly "
            "as a guest without signing in."
        )

        with st.form("gmail_login_form"):
            email_input = st.text_input(
                "Gmail Address (Optional)",
                placeholder="yourname@gmail.com",
            )
            submit_email = st.form_submit_button("Continue with Gmail", use_container_width=True)

            if submit_email:
                cleaned_email = email_input.strip().lower()
                if cleaned_email.endswith("@gmail.com") and len(cleaned_email) > len("@gmail.com"):
                    st.session_state.user_email = cleaned_email
                    st.rerun()
                else:
                    st.error("Please enter a valid @gmail.com address, or click Continue as Guest.")

        if st.button("Continue as Guest (No Gmail Required)", type="primary", use_container_width=True):
            st.session_state.guest_mode = True
            st.rerun()

else:
    user_label = st.session_state.user_email if st.session_state.user_email else "Guest"
    st.caption(f"Active Session: **{user_label}** | Language: **{st.session_state.selected_language}**")

    if not st.session_state.messages:
        st.info(
            "Welcome by Afaque Aftab Solangi! Ask anything in English, Urdu, Hindi, Arabic, "
            "Spanish, French, German, Japanese, and 20+ more languages."
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Type your message here...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        api_key = get_api_key()
        if not api_key:
            error_msg = (
                "Gemini API key is missing. Please add `GEMINI_API_KEY` in Streamlit "
                "App Secrets or enter it in the sidebar."
            )
            with st.chat_message("assistant"):
                st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = generate_ai_reply(
                        api_key=api_key,
                        history=st.session_state.messages,
                        language=st.session_state.selected_language,
                    )
                st.markdown(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})
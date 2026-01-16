# app.py
import streamlit as st
import requests, json, random
from styles import THEMES
from generator import make_pptx

# --- Настройки ---
AI_KEY = st.secrets.get("GROQ_API_KEY", "")
S_ID = "SX-369" # Твой секретный код

def ask_ai(topic, slides, lang, only_quiz=False):
    if not AI_KEY: return None
    seed = random.randint(1, 1000)
    prompt = f"Create presentation. Topic: {topic}. Lang: {lang}. Slides: {slides}. Intro: 80-160 words. JSON format."
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile", 
                "messages": [{"role":"user","content":prompt}], 
                "response_format":{"type":"json_object"}
            }, timeout=120)
        return r.json()["choices"][0]["message"]["content"]
    except: return None

# --- Интерфейс ---
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None

with st.sidebar:
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Количество слайдов", 2, 12, 6) # От 2 до 12 слайдов
    style_name = st.selectbox("Выберите стиль", list(THEMES.keys()))
    lang = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    pass_code = st.text_input("Код доступа", type="password")
    
    if st.button("🚀 Сгенерировать") and t_input:
        with st.spinner("ИИ пишет контент..."):
            res = ask_ai(t_input, s_count, lang)
            if res:
                st.session_state.data = json.loads(res)
                st.session_state.topic = t_input
                st.rerun()

# --- Выдача результата ---
if st.session_state.data:
    if pass_code == S_ID:
        st.success("🔓 Режим разработчика активен")
        buf = make_pptx(st.session_state.data, THEMES[style_name], style_name)
        st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", buf, f"{st.session_state.topic}.pptx")
    else:
        st.info("Пройдите квиз или введите код доступа для скачивания.")
        # Тут можно добавить логику квиза, которую мы обсуждали ранее

import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io

# 1. СТИЛИ
THEMES = {
    "LUFFY STYLE": {"acc": (200, 30, 30), "icon": "⚓ "},
    "GIRLY STYLE": {"acc": (255, 105, 180), "icon": "🌸 "},
    "SCHOOL STYLE": {"acc": (200, 255, 200), "icon": "✏️ "},
    "MODERN GRADIENT": {"acc": (0, 102, 204), "icon": "➔ "},
    "MINIMALIST": {"acc": (100, 100, 100), "icon": "◈ "},
    "NEON NIGHT": {"acc": (0, 255, 150), "icon": "⚡ "},
    "BUSINESS PRO": {"acc": (0, 80, 180), "icon": "✔ "},
    "SUNSET STYLE": {"acc": (255, 230, 0), "icon": "☀️ "}
}

AI_KEY = st.secrets.get("GROQ_API_KEY", "")
S_ID = "SX-369" # Твой секретный код

def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    # Запрос с учетом языка и объема текста (80-160 слов)
    prompt = (f"Create a deep presentation about '{topic}' in {lang} language. Slides: {slides}. "
              f"STRICT RULE: The 'intro' field MUST be 80-160 words for EVERY slide. "
              f"Also create a quiz with 10 questions. "
              f"Return JSON: {{'slides': [{{'title': '..', 'intro': '..', 'points': ['..']}}], "
              f"'quiz': [{{'q': '..', 'a': 'A', 'o': ['A', 'B', 'C']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"You are a professor. Write in {lang}. 130 words per slide."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}}, timeout=120)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

def make_pptx(data, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb, acc_rgb = RGBColor(30,30,30), RGBColor(*theme["acc"])
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
            if style_name in ["SCHOOL STYLE", "NEON NIGHT", "SUNSET STYLE"]: txt_rgb = RGBColor(255,255,255)
        except: pass
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9)).text_frame.paragraphs[0]
        p_t.text = str(s['title']).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(32), True, acc_rgb
        tf = slide.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.3), Inches(5.0)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(s['intro'])
        p.font.size, p.font.color.rgb = Pt(13), txt_rgb
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0

with st.sidebar:
    st.header("Настройки")
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Слайды", 2, 12, 6)
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    # Выбор языка
    lang_choice = st.selectbox("Язык / Забон", ["Russian", "Tajik", "English"])
    # Поле для кода доступа
    pass_code = st.text_input("Код доступа", type="password")
    
    if st.button("🚀 Сгенерировать"):
        res = ask_ai(t_input, s_count, lang_choice)
        if res: 
            st.session_state.data = res
            st.session_state.test_key += 1
            st.rerun()

if st.session_state.data:
    st.header("📝 Тексты слайдов:")
    for i, s in enumerate(st.session_state.data['slides']):
        st.write(f"**{i+1}. {s['title']}** ({len(s['intro'].split())} слов)")
        st.write(s['intro'])
        st.divider()

    # ЕСЛИ КОД ВЕРНЫЙ - СКАЧИВАЕМ СРАЗУ
    if pass_code == S_ID:
        st.success("🔓 Режим разработчика активен!")
        st.download_button("📥 СКАЧАТЬ БЕЗ ТЕСТА", make_pptx(st.session_state.data, style_name), "presentation.pptx")
    else:
        st.header("✅ Тест для скачивания (8/10)")
        score = 0
        quiz = st.session_state.data.get('quiz', [])[:10]
        for i, q in enumerate(quiz):
            ans = st.radio(f"{i+1}. {q['q']}", q['o'], key=f"q_{i}_{st.session_state.test_key}")
            if ans == q['a']: score += 1
        
        if st.button("Проверить и скачать"):
            if score >= 8:
                st.balloons()
                st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_name), "presentation.pptx")
            else:
                st.session_state.test_key += 1
                st.error(f"Результат {score}/10. Тест обновлен. Попробуйте еще раз!")
                st.rerun()

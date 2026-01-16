import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
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

# Получаем ключ
AI_KEY = st.secrets.get("GROQ_API_KEY", "")
S_ID = "SX-369"

def ask_ai(topic, slides, lang):
    if not AI_KEY:
        st.error("Ключ GROQ_API_KEY не найден в Secrets!")
        return None
    
    # Оптимизированный промпт для стабильности
    prompt = (f"Act as a professor. Write a presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"Each slide 'intro' must be 100-150 words. Create 10 quiz questions. "
              f"Output ONLY JSON format: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A', 'B', 'C']}}]}}")
    
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }, 
            timeout=60
        )
        # Если API вернул ошибку
        if r.status_code != 200:
            st.error(f"Ошибка API: {r.status_code} - {r.text}")
            return None
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        st.error(f"Техническая ошибка: {e}")
        return None

def make_pptx(data, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(30,30,30)
        acc_rgb = RGBColor(*theme["acc"])
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
        except: pass
        
        # Заголовок
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0))
        p_t = title_box.text_frame.paragraphs[0]
        p_t.text = str(s.get('title', 'Без названия')).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(32), True, acc_rgb
        
        # Текст
        body_box = slide.shapes.add_textbox(Inches(1.0), Inches(1.5), Inches(11.3), Inches(5.0))
        tf = body_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(s.get('intro', ''))
        p.font.size, p.font.color.rgb = Pt(14), txt_rgb
        
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ИНТЕРФЕЙС
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0

with st.sidebar:
    t_input = st.text_input("Тема")
    s_count = st.slider("Слайды", 2, 12, 6)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    pass_code = st.text_input("Код доступа", type="password")
    
    # Если кнопка нажата, она ДОЛЖНА сработать
    generate_clicked = st.button("🚀 Сгенерировать")

if generate_clicked and t_input:
    with st.spinner("Связываюсь с ИИ... подождите"):
        res = ask_ai(t_input, s_count, lang_choice)
        if res:
            st.session_state.data = res
            st.session_state.test_key += 1
            st.rerun()

if st.session_state.data:
    st.success(f"Презентация на тему '{t_input}' готова!")
    
    with st.expander("📖 Читать текст слайдов"):
        for i, s in enumerate(st.session_state.data['slides']):
            st.write(f"**Слайд {i+1}:** {s.get('intro')}")
    
    if pass_code == S_ID:
        st.download_button("📥 СКАЧАТЬ (Admin)", make_pptx(st.session_state.data, style_name), "pres.pptx")
    else:
        st.header("✅ Пройдите тест")
        score = 0
        quiz = st.session_state.data.get('quiz', [])[:10]
        for i, q in enumerate(quiz):
            ans = st.radio(q['q'], q['o'], key=f"q_{i}_{st.session_state.test_key}")
            if ans == q['a']: score += 1
        
        if st.button("Проверить и скачать"):
            if score >= 8:
                st.download_button("📥 СКАЧАТЬ", make_pptx(st.session_state.data, style_name), "pres.pptx")
            else:
                st.session_state.test_key += 1
                st.error("Недостаточно баллов. Тест обновлен.")
                st.rerun()

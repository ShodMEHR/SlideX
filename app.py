import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io

# ПОРЯДОК: School первый, Luffy последний
THEMES = {
    "SCHOOL STYLE": {"acc": (50, 150, 50), "icon": "✏️", "left": 1.2, "width": 10.8, "dark": True},
    "GIRLY STYLE": {"acc": (255, 105, 180), "icon": "🌸", "left": 1.5, "width": 10.3, "dark": False},
    "MODERN GRADIENT": {"acc": (0, 102, 204), "icon": "➔", "left": 1.0, "width": 11.3, "dark": False},
    "MINIMALIST": {"acc": (100, 100, 100), "icon": "◈", "left": 1.5, "width": 10.3, "dark": False},
    "NEON NIGHT": {"acc": (0, 255, 150), "icon": "⚡", "left": 1.0, "width": 11.3, "dark": True},
    "BUSINESS PRO": {"acc": (0, 80, 180), "icon": "✔", "left": 1.0, "width": 11.3, "dark": False},
    "SUNSET STYLE": {"acc": (255, 140, 0), "icon": "☀️", "left": 1.0, "width": 11.3, "dark": True},
    "LUFFY STYLE": {"acc": (200, 30, 30), "icon": "⚓", "left": 5.8, "width": 7.0, "dark": False},
}

AI_KEY = st.secrets.get("GROQ_API_KEY", "")

def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    prompt = (f"Presentation '{topic}' in {lang}. Slides: {slides}. "
              f"RULE: 'intro' field MUST be 80-160 words. "
              f"Quiz: 10 questions. JSON format only.")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"Academic professor. Write {lang}. 130 words per slide."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}}, timeout=120)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

def make_pptx(data, style_name, font_size):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(255, 255, 255) if theme["dark"] else RGBColor(30, 30, 30)
        
        try: slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
        except: pass
        
        if style_name == "GIRLY STYLE":
            rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(10.8), Inches(5.8))
            rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(255, 255, 255); rect.fill.alpha = 0.8
        
        # Заголовок (Times New Roman, Pt 40)
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0)).text_frame.paragraphs[0]
        p_t.text = f"{theme['icon']} {str(s.get('title', '')).upper()}"
        p_t.font.name = 'Times New Roman'
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(40), True, RGBColor(*theme["acc"])
        
        # Основной текст (Times New Roman, Pt по выбору)
        tf = slide.shapes.add_textbox(Inches(theme["left"]), Inches(1.5), Inches(theme["width"]), Inches(5.5)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(s.get('intro', ''))
        p.font.name = 'Times New Roman'
        p.font.size, p.font.color.rgb = Pt(font_size), txt_rgb
        tf.line_spacing = 1.1 
        
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

# UI
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    t_input = st.text_input("Тема")
    s_count = st.slider("Слайды", 2, 12, 7)
    f_size = st.slider("Шрифт в файле (Pt)", 26, 40, 34)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_sel = st.selectbox("Стиль", list(THEMES.keys()))
    user_code = st.text_input("Код доступа", type="password") 
    
    if st.button("🚀 Сгенерировать"):
        with st.status("Создание...") as s:
            res = ask_ai(t_input, s_count, lang_choice)
            if res:
                st.session_state.data = res
                st.session_state.test_key += 1
                st.session_state.submitted = False
                s.update(label="Готово!", state="complete")
                st.rerun()

if st.session_state.data:
    # Комфортное чтение на сайте (шрифт обычный)
    st.header(f"Просмотр: {t_input}")
    for i, s in enumerate(st.session_state.data['slides']):
        st.subheader(f"Слайд {i+1}: {s.get('title')}")
        st.write(s.get('intro'))
        st.divider()

    if user_code == "SX-369":
        st.success("🔓 Режим SX")
        st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_sel, f_size), f"{t_input}.pptx")
    else:
        # ТЕСТ С ФИКСОМ 0/10
        quiz = st.session_state.data.get('quiz', [])[:10]
        user_ans = []
        for i, q in enumerate(quiz):
            user_ans.append(st.selectbox(f"Вопрос {i+1}: {q['q']}", ["-- Выберите --"] + q['o'], key=f"q_{i}_{st.session_state.test_key}"))

        if st.button("Проверить ответы"):
            score = 0
            for i, q in enumerate(quiz):
                if user_ans[i] != "-- Выберите --" and user_ans[i][0] == q['a']:
                    score += 1
            
            st.subheader(f"Результат: {score}/10")
            if score >= 8:
                st.balloons()
                st.download_button("📥 СКАЧАТЬ", make_pptx(st.session_state.data, style_sel, f_size), f"{t_input}.pptx")
            else:
                st.error("Тест не пройден. Нужно 8/10.")

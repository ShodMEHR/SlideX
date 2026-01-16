import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
import requests, json, io, re

# ПОРЯДОК СТИЛЕЙ
THEMES = {
    "SCHOOL STYLE": {"acc": (50, 150, 50), "icon": "✏️", "left": 1.5, "width": 10.3, "dark": True},
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
    prompt = (f"Create presentation '{topic}' in {lang}. Slides: {slides}. "
              f"Each 'intro' must be 130 words. Return JSON with 'slides' and 'quiz'.")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": "You are a professor. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}}, timeout=120)
        return r.json()["choices"][0]["message"]["content"]
    except: return None

def make_pptx(data, style_name, font_size):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    slides_data = data.get('slides', data.get('presentation', []))
    
    for s in slides_data:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(255, 255, 255) if theme["dark"] else RGBColor(30, 30, 30)
        
        try: slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
        except: pass
        
        # ЗАГОЛОВОК С ТЕНЬЮ
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0))
        p_t = title_box.text_frame.paragraphs[0]
        p_t.text = f"{theme['icon']} {str(s.get('title', 'СЛАЙД')).upper()}"
        p_t.font.name, p_t.font.size, p_t.font.bold = 'Times New Roman', Pt(40), True
        p_t.font.color.rgb = RGBColor(*theme["acc"])
        title_box.shadow.inherit = True # Включаем тень
        
        # ТЕКСТ (Times New Roman + Shadow)
        tf_box = slide.shapes.add_textbox(Inches(theme["left"]), Inches(1.5), Inches(theme["width"]), Inches(5.5))
        tf = tf_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(s.get('intro', s.get('content', '')))
        p.font.name, p.font.size, p.font.color.rgb = 'Times New Roman', Pt(font_size), txt_rgb
        tf.line_spacing = 1.15
        tf_box.shadow.inherit = True
        
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None

with st.sidebar:
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Кол-во слайдов", 2, 12, 7)
    f_size = st.slider("Размер шрифта в PPTX", 26, 40, 32)
    style_sel = st.selectbox("Выберите стиль", list(THEMES.keys()))
    user_code = st.text_input("Код доступа", type="password")
    
    if st.button("🚀 Сгенерировать"):
        raw_res = ask_ai(t_input, s_count, "Russian")
        if raw_res:
            st.session_state.data = json.loads(raw_res)
            st.rerun()

if st.session_state.data:
    # Безопасное извлечение слайдов для просмотра
    slides = st.session_state.data.get('slides', st.session_state.data.get('presentation', []))
    
    st.header(f"📺 Просмотр: {t_input}")
    for i, s in enumerate(slides):
        with st.expander(f"Слайд {i+1}: {s.get('title', 'Без названия')}"):
            st.write(s.get('intro', s.get('content', 'Текст отсутствует')))
    
    if user_code == "SX-369":
        st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_sel, f_size), f"{t_input}.pptx")
    else:
        st.info("Введите код SX-369 для скачивания или пройдите тест (в разработке).")

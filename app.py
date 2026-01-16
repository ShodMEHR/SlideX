import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.xmlchemy import OxmlElement
import requests, json, textwrap, io

# ================= CONFIG =================
MODEL_NAME = "llama-3.3-70b-versatile"

THEMES = {
    "NEON NIGHT": {"bg": (10,10,25), "acc": (0,255,150), "txt": (255,255,255)},
    "BUSINESS PRO": {"bg": (255,255,255), "acc": (0,80,180), "txt": (30,30,30)},
    "DEEP OCEAN": {"bg": (0,20,40), "acc": (0,200,255), "txt": (255,255,255)},
    "GIRLY STYLE": {"bg": (255,192,203), "acc": (255,105,180), "txt": (75,0,130)},
    "LUFFY STYLE": {"bg": (245,222,179), "acc": (200,30,30), "txt": (40,20,10)},
    "SUNSET STYLE": {"bg": (255,140,0), "acc": (255,255,0), "txt": (0,0,0)}
}

# Извлекаем секреты
try:
    AI_KEY = st.secrets["GROQ_API_KEY"]
    S_ID = st.secrets.get("S_CODE", "SX-369")
except:
    AI_KEY = ""
    S_ID = "SX-369"

# ================= HELPERS =================
def split_text_columns(text):
    words = text.split()
    mid = len(words) // 2
    return " ".join(words[:mid]), " ".join(words[mid:])

# ================= AI LOGIC =================
def ask_ai(topic, slides, lang, only_quiz=False):
    mode = "ONLY quiz questions" if only_quiz else "full presentation"
    prompt = f"""
Create a {mode} about "{topic}" in {lang}.
Slides: {slides}

STRICT RULES:
- EACH slide 'intro' field MUST contain exactly 130–160 words.
- Exactly 10 UNIQUE quiz questions in 'quiz' field.
- Academic, detailed, professional style.
- OUTPUT ONLY VALID JSON.

FORMAT:
{{
 "slides": [{{"title": "Title", "intro": "130-160 words text...", "points": ["Fact 1","Fact 2"]}}],
 "quiz": [{{"q":"Question","o":{{"A":"x","B":"y","C":"z"}},"a":"A"}}]
}}
"""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are a university professor. You write very long, exhaustive texts. Every quiz must be new and based on the topic."},
                    {"role": "user", "content": prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            },
            timeout=120
        )
        if r.status_code == 200:
            return json.loads(r.json()["choices"][0]["message"]["content"])
        return None
    except:
        return None

# ================= PPTX GENERATION =================
def add_transition(slide, style):
    el = slide._element
    tr = OxmlElement("p:transition")
    if style == "LUFFY STYLE":
        push = OxmlElement("p:push"); push.set("dir", "l"); tr.append(push)
    else:
        tr.append(OxmlElement("p:fade"))
    el.append(tr)

def make_pptx(data, theme, style):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)

    for s in data.get("slides", []):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        add_transition(slide, style)

        # Background
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(*theme["bg"]); bg.line.fill.background()

        # Title
        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9))
        tp = tb.text_frame.paragraphs[0]
        tp.text = str(s.get("title", "ЗАГОЛОВОК")).upper()
        tp.font.size, tp.font.bold, tp.font.color.rgb = Pt(30), True, RGBColor(*theme["acc"])

        # Two Columns Text
        intro = str(s.get("intro", ""))
        left, right = split_text_columns(intro)

        # Columns UI
        for txt, x_pos in [(left, 0.5), (right, 6.8)]:
            box = slide.shapes.add_textbox(Inches(x_pos), Inches(1.4), Inches(6), Inches(5.7))
            tf = box.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = textwrap.fill(txt, 65)
            p.font.size, p.font.color.rgb = Pt(14), RGBColor(*theme["txt"])

        # Points
        icon = "⚓ " if style == "LUFFY STYLE" else "• "
        last_box = slide.shapes.add_textbox(Inches(6.8), Inches(5.0), Inches(6), Inches(2))
        for pt in s.get("points", []):
            p = last_box.text_frame.add_paragraph()
            p.text = f"{icon}{pt}"
            p.font.size, p.font.color.rgb = Pt(12), RGBColor(*theme["acc"])

    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

# ================= UI =================
st.set_page_config("SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

# Инициализация сессии
if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.quiz_key = 0
    st.session_state.topic = ""

with st.sidebar:
    st.header("⚙️ Настройки")
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Слайды", 2, 12, 6)
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    lang_name = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    pass_code = st.text_input("Админ-код", type="password")

    if st.button("🚀 Сгенерировать") and t_input:
        with st.spinner("Генерируем новый контент и тест..."):
            # СБРОС СТАРЫХ ДАННЫХ
            st.session_state.data = None
            st.session_state.quiz_key += 1 
            
            res = ask_ai(t_input, s_count, lang_name)
            if res and "slides" in res:
                st.session_state.data = res
                st.session_state.topic = t_input
                st.rerun()
            else:
                st.error("Ошибка API. Попробуйте еще раз.")

if st.session_state.data:
    st.header(f"📋 Тема: {st.session_state.topic}")
    
    # Предпросмотр
    for i, s in enumerate(st.session_state.data.get("slides", [])):
        with st.expander(f"Слайд {i+1}: {s.get('title')}"):
            st.write(f"**Слов:** {len(s.get('intro','').split())}")
            st.write(s.get("intro"))

    st.divider()

    # Логика скачивания
    if pass_code == S_ID:
        st.success("🔓 Админ-доступ открыт")
        buf = make_pptx(st.session_state.data, THEMES[style_name], style_name)
        st.download_button("📥 СКАЧАТЬ PPTX", buf, file_name=f"{st.session_state.topic}.pptx")
    else:
        st.subheader("🧠 Тест для доступа (8/10)")
        quiz = st.session_state.data.get("quiz", [])[:10]
        
        if quiz:
            user_answers = []
            for i, q in enumerate(quiz):
                ans = st.radio(
                    f"{i+1}. {q['q']}", ["A", "B", "C"],
                    format_func=lambda x: f"{x}: {q['o'].get(x, '')}",
                    key=f"q_{st.session_state.quiz_key}_{i}"
                )
                user_answers.append(ans)

            if st.button("Проверить ответы"):
                score = sum(1 for i, a in enumerate(user_answers) if a == quiz[i]["a"])
                if score >= 8:
                    st.success(f"Результат: {score}/10. Можно скачивать!")
                    buf = make_pptx(st.session_state.data, THEMES[style_name], style_name)
                    st.download_button("📥 СКАЧАТЬ PPTX", buf, file_name=f"{st.session_state.topic}.pptx")
                else:
                    st.error(f"Результат: {score}/10. Нужно минимум 8. Попробуйте перегенерировать.")

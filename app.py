import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.xmlchemy import OxmlElement
import requests, json, textwrap, io, random

# ================= CONFIG =================
MODEL_NAME = "llama-3.3-70b-versatile"

THEMES = {
    "NEON NIGHT": {"bg": (10,10,25), "acc": (0,255,150), "txt": (255,255,255)},
    "BUSINESS PRO": {"bg": (255,255,255), "acc": (0,80,180), "txt": (30,30,30)},
    "DEEP OCEAN": {"bg": (0,20,40), "acc": (0,200,255), "txt": (255,255,255)},
    "GIRLY STYLE": {"bg": (255,192,203), "acc": (75,0,130), "txt": (75,0,130)},
    "LUFFY STYLE": {"bg": (245,222,179), "acc": (200,30,30), "txt": (40,20,10)},
    "SUNSET STYLE": {"bg": (255,140,0), "acc": (255,255,0), "txt": (0,0,0)}
}

try:
    AI_KEY = st.secrets["GROQ_API_KEY"]
    S_ID = st.secrets.get("S_CODE", "SX-369") # Твой код доступа
except:
    AI_KEY = ""
    S_ID = "SX-369"

# ================= HELPERS =================
def clamp_intro(text, min_w=80, max_w=160):
    words = text.split()
    if len(words) < min_w:
        words += words[: (min_w - len(words))]
    return " ".join(words[:max_w])

# ================= AI LOGIC =================
def ask_ai(topic, slides, lang, only_quiz=False):
    if not AI_KEY: return None
    seed_val = random.randint(1,100000)
    
    if only_quiz:
        prompt = f"Create ONLY 10 UNIQUE quiz questions about '{topic}' in {lang}. JSON format: {{'quiz': [...]}}"
    else:
        prompt = f"Create a presentation about '{topic}' in {lang}. Slides: {slides}. STRICT: 'intro' field 80-160 words. JSON format: {{'slides': [...], 'quiz': [...]}}"

    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role":"system","content": f"Professor. Seed: {seed_val}. Always 80-160 words per slide."},
                    {"role":"user","content": prompt}
                ],
                "response_format":{"type":"json_object"},
                "temperature":0.7
            },
            timeout=120
        )
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

# ================= PPTX GENERATION =================
def make_pptx(data, topic, theme, style):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)

    for s in data.get("slides", []):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        # Фон
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid(); bg.fill.fore_color.rgb = RGBColor(*theme["bg"]); bg.line.fill.background()

        # Параметры текста
        left_m = Inches(0.5); width_m = Inches(12.3); icon = "• "

        if style == "LUFFY STYLE":
            left_m = Inches(4.8); width_m = Inches(8.0); icon = "⚓ "
            try: slide.shapes.add_picture("luffy.png", Inches(0.2), Inches(1.5), height=Inches(5.5))
            except: pass
        elif style == "GIRLY STYLE":
            left_m = Inches(1.5); width_m = Inches(7.5); icon = "🌸 "
            rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.2), Inches(11.7), Inches(5.8))
            rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(200, 245, 240)
            try: slide.shapes.add_picture("girls.png", Inches(9.2), Inches(3.5), height=Inches(3.5))
            except: pass

        # Заголовок
        tb = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9))
        p_title = tb.text_frame.paragraphs[0]
        p_title.text = str(s.get("title","")).upper()
        p_title.font.size, p_title.font.bold = Pt(36), True
        p_title.font.color.rgb = RGBColor(*theme["acc"])

        # Единый блок текста (80-160 слов)
        intro_txt = clamp_intro(str(s.get("intro","")))
        box = slide.shapes.add_textbox(left_m, Inches(1.4), width_m, Inches(5.5))
        tf = box.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = intro_txt
        p.font.size, p.font.color.rgb = Pt(14), RGBColor(*theme["txt"])

        for pt in s.get("points", []):
            pp = tf.add_paragraph()
            pp.text = f"{icon}{pt}"
            pp.font.size, pp.font.bold = Pt(12), True
            pp.font.color.rgb = RGBColor(*theme["acc"])

    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

# ================= UI =================
st.set_page_config("SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "quiz_key" not in st.session_state: st.session_state.quiz_key = 1

with st.sidebar:
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Слайды", 2, 12, 6)
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    lang_name = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    pass_code = st.text_input("Код доступа", type="password")

    if st.button("🚀 Сгенерировать") and t_input:
        res = ask_ai(t_input, s_count, lang_name)
        if res:
            st.session_state.data = res
            st.session_state.topic = t_input
            st.rerun()

if st.session_state.data:
    if st.button("🔄 Обновить только вопросы"):
        new_q = ask_ai(st.session_state.topic, s_count, lang_name, only_quiz=True)
        if new_q:
            st.session_state.data["quiz"] = new_q["quiz"]
            st.session_state.quiz_key += 1
            st.rerun()

    # Админ или Тест
    if pass_code == S_ID:
        st.success("🔓 Доступ открыт")
        buf = make_pptx(st.session_state.data, st.session_state.topic, THEMES[style_name], style_name)
        st.download_button("📥 СКАЧАТЬ", buf, f"{st.session_state.topic}.pptx")
    else:
        score = 0
        quiz = st.session_state.data.get("quiz", [])[:10]
        for i, q in enumerate(quiz):
            ans = st.radio(f"{i+1}. {q['q']}", ["A", "B", "C"], key=f"q_{st.session_state.quiz_key}_{i}")
            if ans == q['a']: score += 1
        
        if st.button("Проверить ответы"):
            if score >= 8:
                st.balloons()
                buf = make_pptx(st.session_state.data, st.session_state.topic, THEMES[style_name], style_name)
                st.download_button("📥 СКАЧАТЬ", buf, f"{st.session_state.topic}.pptx")
            else: st.error(f"Результат: {score}/10. Нужно 8.")

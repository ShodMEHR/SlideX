import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, textwrap, io
from pptx.oxml.xmlchemy import OxmlElement

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

try:
    AI_KEY = st.secrets["GROQ_API_KEY"]
    S_ID = st.secrets.get("S_CODE", "SX-369")
except:
    AI_KEY = ""
    S_ID = "SX-369"

# ================= AI FUNCTION (FIXED) =================
def ask_ai(topic, slides, lang, only_quiz=False):
    mode = "ONLY 10 new quiz questions" if only_quiz else "full presentation"
    
    # Жесткое требование по объему текста в промпте
    prompt = f"""
Create a {mode} about "{topic}" in {lang}.
Slides count: {slides}

STRICT CONSTRAINTS:
1. Every 'intro' field MUST be a huge academic paragraph of 130-160 words. No short sentences.
2. Provide exactly 10 quiz questions.
3. Return ONLY a valid JSON object.

JSON Structure:
{{
 "slides": [{{"title": "Title", "intro": "Long detailed text (130-160 words)...", "points": ["Fact 1", "Fact 2"]}}],
 "quiz": [{{"q": "Q", "o": {{"A": "v1", "B": "v2", "C": "v3"}}, "a": "A"}}]
}}
"""
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7 # Немного творчества для объема
            },
            timeout=90
        )
        res_json = response.json()
        
        # Защита от ошибки 'choices'
        if "choices" in res_json:
            return json.loads(res_json["choices"][0]["message"]["content"])
        else:
            st.error(f"Ошибка API: {res_json.get('error', {}).get('message', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Ошибка соединения: {e}")
        return None

# ================= PPTX & TRANSITIONS =================
def add_transition(slide, style_name):
    slide_el = slide._element
    transition = OxmlElement("p:transition")
    if style_name == "LUFFY STYLE":
        push = OxmlElement("p:push")
        push.set("dir", "l")
        transition.append(push)
    else:
        transition.append(OxmlElement("p:fade"))
    slide_el.append(transition)

def make_pptx(data, topic, theme, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    
    for s in data["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        add_transition(slide, style_name)
        
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(*theme["bg"])
        bg.line.fill.background()

        t_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        p = t_box.text_frame.add_paragraph()
        p.text = str(s.get("title", "")).upper()
        p.font.size, p.font.bold, p.font.color.rgb = Pt(32), True, RGBColor(*theme["acc"])

        c_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12), Inches(5.5))
        tf = c_box.text_frame
        tf.word_wrap = True
        pi = tf.add_paragraph()
        pi.text = textwrap.fill(str(s.get("intro", "")), width=100) # Чуть уже, чтобы текст шел вниз
        pi.font.size, pi.font.color.rgb = Pt(15), RGBColor(*theme["txt"])

        icon = "⚓ " if style_name == "LUFFY STYLE" else "• "
        for pt in s.get("points", []):
            pp = tf.add_paragraph()
            pp.text = f"{icon}{pt}"; pp.font.size, pp.font.color.rgb = Pt(14), RGBColor(*theme["acc"])
    
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ================= UI =================
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state:
    st.session_state.data = None
    st.session_state.quiz_key = 0

with st.sidebar:
    st.header("⚙️ Настройки")
    topic_in = st.text_input("Тема")
    slide_num = st.slider("Слайды", 2, 12, 6)
    style_sel = st.selectbox("Стиль", list(THEMES.keys()))
    lang_sel = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    adm = st.text_input(".", type="password")

    if st.button("🚀 Сгенерировать") and topic_in:
        with st.spinner("Создание контента..."):
            st.session_state.data = None
            st.session_state.quiz_key += 1
            res = ask_ai(topic_in, slide_num, lang_sel)
            if res:
                st.session_state.data = res
                st.session_state.topic = topic_in
                st.rerun()

if st.session_state.data:
    st.header(f"📝 Предпросмотр: {st.session_state.topic}")
    for i, s in enumerate(st.session_state.data["slides"]):
        with st.expander(f"Слайд {i+1}"):
            st.write(s.get("intro"))

    st.divider()
    
    if adm == S_ID:
        st.success("Доступ владельца")
        b = make_pptx(st.session_state.data, st.session_state.topic, THEMES[style_sel], style_sel)
        st.download_button("📥 СКАЧАТЬ", b, file_name="presentation.pptx")
    else:
        st.subheader("🧠 Тест (минимум 8/10)")
        quiz = st.session_state.data.get("quiz", [])[:10]
        u_ans = []
        for i, q in enumerate(quiz):
            u_ans.append(st.radio(f"{i+1}. {q['q']}", ["A", "B", "C"], format_func=lambda x: f"{x}: {q['o'][x]}", key=f"q_{st.session_state.quiz_key}_{i}"))
        
        if st.button("Проверить ответы"):
            score = sum(1 for i, a in enumerate(u_ans) if a == quiz[i]["a"])
            if score >= 8:
                st.success(f"Результат: {score}/10")
                b = make_pptx(st.session_state.data, st.session_state.topic, THEMES[style_sel], style_sel)
                st.download_button("📥 СКАЧАТЬ", b, file_name="presentation.pptx")
            else:
                st.error(f"Результат: {score}/10. Обновление вопросов...")
                # Исправленное обновление:
                new_q = ask_ai(st.session_state.topic, slide_num, lang_sel, only_quiz=True)
                if new_q and "quiz" in new_q:
                    st.session_state.data["quiz"] = new_q["quiz"]
                    st.session_state.quiz_key += 1
                    st.rerun()

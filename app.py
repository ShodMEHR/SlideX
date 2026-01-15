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

S_ID = st.secrets.get("S_CODE", "SX-369")  # секретный код владельца

# ================= AI =================
def ask_ai(topic, slides, lang, only_quiz=False):
    mode = "ONLY 10 quiz questions" if only_quiz else "full presentation"
    prompt = f"""
Create a {mode} about "{topic}" in {lang}.
Slides: {slides}

Rules:
- Each slide intro must be 130–160 words.
- Exactly 10 quiz questions.
- Response must be strictly valid JSON.

JSON structure:
{{
 "slides": [{{"title": "Slide Title", "intro": "Very long text...", "points": ["point1", "point2"]}}],
 "quiz": [{{"q": "Question text", "o": {{"A": "v1", "B": "v2", "C": "v3"}}, "a": "A"}}]
}}
"""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=90
        )
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except Exception as e:
        st.error(f"Ошибка ИИ: {e}")
        return None

# ================= PPTX + Анимация =================
def add_slide_transition(slide, style="fade"):
    slide_element = slide._element
    # удаляем старые transition если есть
    for child in slide_element.findall("{http://schemas.openxmlformats.org/presentationml/2006/main}transition"):
        slide_element.remove(child)
    transition = OxmlElement("p:transition")
    if style == "push":
        push = OxmlElement("p:push")
        push.set("dir", "l")
        transition.append(push)
    else:
        fade = OxmlElement("p:fade")
        transition.append(fade)
    slide_element.append(transition)

def make_pptx(data, topic, theme, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)

    for s in data["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])

        # Анимация перехода
        add_slide_transition(slide, "push" if style_name=="LUFFY STYLE" else "fade")

        # Фон
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(*theme["bg"])
        bg_shape.line.fill.background()

        # Заголовок
        t_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        p = t_box.text_frame.add_paragraph()
        p.text = str(s.get("title", "БЕЗ ЗАГОЛОВКА")).upper()
        p.font.size, p.font.bold = Pt(32), True
        p.font.color.rgb = RGBColor(*theme["acc"])

        # Контент
        c_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12), Inches(5.5))
        tf = c_box.text_frame
        tf.word_wrap = True
        pi = tf.add_paragraph()
        pi.text = textwrap.fill(str(s.get("intro","")), width=105)
        pi.font.size, pi.font.color.rgb = Pt(15), RGBColor(*theme["txt"])

        # Список с иконками
        icon = "⚓ " if style_name=="LUFFY STYLE" else "• "
        for pt in s.get("points", []):
            pp = tf.add_paragraph()
            pp.text = f"{icon}{pt}"
            pp.font.size, pp.font.color.rgb = Pt(14), RGBColor(*theme["acc"])

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
    topic_input = st.text_input("Тема презентации")
    slide_count = st.slider("Количество слайдов", 2, 12, 6)
    selected_style = st.selectbox("Стиль оформления", list(THEMES.keys()))
    selected_lang = st.selectbox("Язык", ["Russian","Tajik","English"])
    admin_code = st.text_input(".", type="password", help="Владелец")
    is_owner = (admin_code == S_ID)

    if st.button("🚀 Сгенерировать") and topic_input:
        with st.spinner("ИИ создает контент..."):
            st.session_state.data = None
            st.session_state.quiz_key += 1
            res = ask_ai(topic_input, slide_count, selected_lang)
            if res:
                st.session_state.data = res
                st.session_state.topic = topic_input
                st.rerun()

# ================= РЕЗУЛЬТАТ =================
if st.session_state.data:
    st.header(f"📝 Предпросмотр: {st.session_state.topic}")
    for i,s in enumerate(st.session_state.data["slides"]):
        with st.expander(f"Слайд {i+1}: {s.get('title')}"):
            st.write(s.get('intro'))

    st.divider()

    if is_owner:
        st.success("✅ Режим владельца включен")
        buf = make_pptx(st.session_state.data, st.session_state.topic, THEMES[selected_style], selected_style)
        st.download_button("📥 СКАЧАТЬ БЕЗ ТЕСТА", buf, file_name=f"{st.session_state.topic}.pptx")
    else:
        st.subheader("🧠 Проверка знаний (нужно 8/10)")
        quiz_list = st.session_state.data.get("quiz", [])[:10]
        user_answers = []

        for i, q in enumerate(quiz_list):
            ans = st.radio(
                f"{i+1}. {q['q']}",
                ["A","B","C"],
                format_func=lambda x: f"{x}: {q['o'][x]}",
                key=f"q_{st.session_state.quiz_key}_{i}"
            )
            user_answers.append(ans)

        if st.button("Проверить ответы"):
            score = sum(1 for i,a in enumerate(user_answers) if a==quiz_list[i]["a"])
            if score >= 8:
                st.success(f"Отлично! Результат: {score}/10")
                buf = make_pptx(st.session_state.data, st.session_state.topic, THEMES[selected_style], selected_style)
                st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", buf, file_name=f"{st.session_state.topic}.pptx")
            else:
                st.error(f"Результат: {score}/10. Нужно 8. Генерируем новый тест...")
                new_quiz = ask_ai(st.session_state.topic, slide_count, selected_lang, only_quiz=True)
                if new_quiz:
                    st.session_state.data["quiz"] = new_quiz["quiz"]
                    st.session_state.quiz_key += 1
                    st.rerun()

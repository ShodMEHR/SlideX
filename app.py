import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, textwrap, io
from datetime import datetime

# ================= CONFIG =================
try:
    AI_KEY = st.secrets["GROQ_API_KEY"]
    S_ID = st.secrets.get("S_CODE", "SX-369") 
except:
    AI_KEY = "your_key_here"
    S_ID = "SX-369"

MODEL_NAME = "llama-3.3-70b-versatile"

THEMES = {
    "NEON NIGHT": {"bg": (10,10,25), "acc": (0,255,150), "txt": (255,255,255)},
    "BUSINESS PRO": {"bg": (255,255,255), "acc": (0,80,180), "txt": (30,30,30)},
    "DEEP OCEAN": {"bg": (0,20,40), "acc": (0,200,255), "txt": (255,255,255)},
    "GIRLY STYLE": {"bg": (255,192,203), "acc": (255,105,180), "txt": (75,0,130)},
    "LUFFY STYLE": {"bg": (245,222,179), "acc": (255,69,0), "txt": (0,0,128)},
    "SUNSET STYLE": {"bg": (255,140,0), "acc": (255,255,0), "txt": (0,0,0)}
}

# ================= CORE FUNCTIONS =================
def ask_ai(topic, slides, lang, only_quiz=False):
    mode_text = "full presentation with quiz" if not only_quiz else "ONLY 10 new quiz questions"
    prompt = f"""
Act as a professional educator. Create a {mode_text} about "{topic}" strictly in {lang}.
Slides: {slides}.

STRICT RULES:
1. Each slide 'intro' field: EXACTLY 100-150 words. No less.
2. 'quiz' array: MUST contain EXACTLY 10 diverse questions.

JSON Format:
{{
  "slides": [{{"title": "T", "intro": "Long text...", "points": ["Fact1", "Fact2"]}}],
  "quiz": [
    {{"q": "Question", "o": {{"A":"v1","B":"v2","C":"v3"}}, "a":"A"}}
  ]
}}
"""
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            },
            timeout=90
        ).json()
        return json.loads(r["choices"][0]["message"]["content"])
    except Exception as e:
        st.error(f"Ошибка ИИ: {e}")
        return None

def make_pptx(data, topic, theme_data):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    bg, txt, acc = theme_data["bg"], theme_data["txt"], theme_data["acc"]
    for s in data["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0,0,prs.slide_width, prs.slide_height)
        sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(*bg); sh.line.fill.background()
        
        t_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        p = t_box.text_frame.add_paragraph()
        p.text = str(s.get("title","")).upper()
        p.font.size, p.font.bold, p.font.color.rgb = Pt(32), True, RGBColor(*acc)
        
        c_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.5))
        tf = c_box.text_frame
        tf.word_wrap = True
        pi = tf.add_paragraph()
        pi.text = textwrap.fill(str(s.get("intro","")), width=105)
        pi.font.size, pi.font.color.rgb = Pt(16), RGBColor(*txt)
        for pt in s.get("points",[]):
            pp = tf.add_paragraph()
            pp.text = f"• {pt}"; pp.font.size, pp.font.color.rgb = Pt(14), RGBColor(*acc)
    
    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ================= UI =================
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "quiz_key" not in st.session_state: st.session_state.quiz_key = 0
if "test_ok" not in st.session_state: st.session_state.test_ok = False

with st.sidebar:
    st.header("⚙️ Настройки")
    t_in = st.text_input("Тема", value=st.session_state.get("t_val",""))
    s_num = st.slider("Слайды", 2, 12, 6)
    style = st.selectbox("Стиль", list(THEMES.keys()))
    lang = st.selectbox("Язык", ["Russian","Tajik","English"])
    st.write("---")
    # Тот самый секретный вход под точкой
    a_code = st.text_input(".", type="password", help="Admin Access")
    is_owner = (a_code == S_ID)

if st.button("🚀 Сгенерировать"):
    if t_in:
        with st.spinner("Генерируем контент (80-160 слов на слайд) и тест..."):
            res = ask_ai(t_in, s_num, lang)
            if res:
                st.session_state.data = res
                st.session_state.t_val = t_in
                st.session_state.test_ok = False
                st.session_state.quiz_key += 1
                st.rerun()
    else:
        st.warning("Введите тему!")

if st.session_state.data:
    st.header("📝 Предпросмотр контента")
    for i, s in enumerate(st.session_state.data["slides"]):
        with st.expander(f"Слайд {i+1}: {s.get('title')}"):
            st.write(s.get("intro"))

    st.divider()

    # ЛОГИКА СКАЧИВАНИЯ
    if is_owner or st.session_state.test_ok:
        st.success("✅ Доступ открыт!")
        buf = make_pptx(st.session_state.data, st.session_state.t_val, THEMES[style])
        fname = f"{st.session_state.t_val}.pptx"
        st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", buf, file_name=fname)
    else:
        quiz = st.session_state.data.get("quiz", [])
        if quiz:
            st.subheader(f"🧠 Пройдите тест ({len(quiz)} вопросов)")
            u_ans = []
            for i, q in enumerate(quiz):
                st.write(f"**{i+1}. {q['q']}**")
                ans = st.radio(f"Выбор {i}", ["A","B","C"], 
                               format_func=lambda x: f"{x}: {q['o'][x]}", 
                               key=f"q_{st.session_state.quiz_key}_{i}")
                u_ans.append(ans)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Проверить ответы"):
                    score = sum(1 for i, a in enumerate(u_ans) if a == quiz[i]["a"])
                    pass_score = max(1, int(len(quiz) * 0.8))
                    if score >= pass_score:
                        st.session_state.test_ok = True
                        st.rerun()
                    else:
                        st.error(f"❌ Ваш балл: {score}/{len(quiz)}. Нужно минимум {pass_score}.")
            
            with col2:
                if st.button("🔄 Обновить тест"):
                    with st.spinner("Новые вопросы..."):
                        new_q = ask_ai(st.session_state.t_val, s_num, lang, only_quiz=True)
                        if new_q: 
                            st.session_state.data["quiz"] = new_q["quiz"]
                            st.session_state.quiz_key += 1
                            st.rerun()

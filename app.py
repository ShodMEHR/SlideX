import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io

# 1. ПОЛНЫЕ НАСТРОЙКИ СТИЛЕЙ
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
S_ID = "SX-369"

def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    prompt = (f"Create a deep presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"STRICT RULE: Each 'intro' field MUST be 100-150 words (min 3 paragraphs). "
              f"Also create a quiz with 10 questions. "
              f"Return JSON: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A','B','C']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"Professor. Write in {lang}. 130 words per slide."},
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
        txt_rgb = RGBColor(30,30,30)
        acc_rgb = RGBColor(*theme["acc"])
        l_m, w_m = Inches(1.0), Inches(11.3) # Дефолтные отступы
        
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
            # Специфическая верстка под стили
            if style_name == "LUFFY STYLE":
                l_m, w_m = Inches(5.5), Inches(7.3)
            elif style_name == "GIRLY STYLE":
                rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.2), Inches(10.3), Inches(5.8))
                rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(255,255,255); rect.fill.alpha = 0.8
                l_m, w_m = Inches(2.0), Inches(9.3)
            elif style_name in ["NEON NIGHT", "SUNSET STYLE", "SCHOOL STYLE"]:
                txt_rgb = RGBColor(255,255,255)
        except: pass
        
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9)).text_frame.paragraphs[0]
        p_t.text = str(s.get('title', '')).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(32), True, acc_rgb
        
        tf = slide.shapes.add_textbox(l_m, Inches(1.4), w_m, Inches(5.5)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(s.get('intro', ''))
        p.font.size, p.font.color.rgb = Pt(14), txt_rgb
        
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

# ИНТЕРФЕЙС
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0

with st.sidebar:
    t_input = st.text_input("Тема")
    s_count = st.slider("Слайды", 2, 12, 6)
    lang_choice = st.selectbox("Забон / Язык", ["Russian", "Tajik", "English"])
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    pass_code = st.text_input("Код доступа", type="password")
    gen = st.button("🚀 Сгенерировать")

if gen and t_input:
    with st.spinner("ИИ пишет ГИГАНТСКИЙ текст..."):
        res = ask_ai(t_input, s_count, lang_choice)
        if res: st.session_state.data = res; st.session_state.test_key += 1; st.rerun()

if st.session_state.data:
    # 1. ЧТЕНИЕ ТЕКСТА
    st.header("📝 Текст презентации")
    for i, s in enumerate(st.session_state.data['slides']):
        st.subheader(f"Слайд {i+1} ({len(s.get('intro','').split())} слов)")
        st.write(s.get('intro'))
        st.divider()

    # 2. ПРОВЕРКА КОДА ИЛИ ТЕСТ
    if pass_code == S_ID:
        st.success("🔓 Код SX-369 принят!")
        st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_name), "pres.pptx")
    else:
        st.header("✅ Тест (8/10)")
        quiz = st.session_state.data.get('quiz', [])[:10]
        user_ans = []
        for i, q in enumerate(quiz):
            user_ans.append(st.radio(f"{i+1}. {q['q']}", q['o'], key=f"q_{i}_{st.session_state.test_key}"))
            
        if st.button("Проверить и скачать"):
            score = sum([1 for i in range(len(quiz)) if user_ans[i] == quiz[i]['a']])
            if score >= 8:
                st.balloons()
                st.download_button("📥 СКАЧАТЬ", make_pptx(st.session_state.data, style_name), "pres.pptx")
            else:
                st.error(f"У вас {score}/10.")
                for i, q in enumerate(quiz):
                    st.write(f"Вопрос {i+1}: {'✅' if user_ans[i] == q['a'] else '❌'}")
                st.session_state.test_key += 1
                st.rerun()

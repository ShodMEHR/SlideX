import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io

# 1. СТИЛИ И ХАРАКТЕРИСТИКИ ВЕРСТКИ
THEMES = {
    "LUFFY STYLE": {"acc": (200, 30, 30), "icon": "⚓", "text_left": 5.5, "text_width": 7.3},
    "GIRLY STYLE": {"acc": (255, 105, 180), "icon": "🌸", "text_left": 2.0, "text_width": 9.3},
    "SCHOOL STYLE": {"acc": (200, 255, 200), "icon": "✏️", "text_left": 1.0, "text_width": 11.3},
    "MODERN GRADIENT": {"acc": (0, 102, 204), "icon": "➔", "text_left": 1.0, "text_width": 11.3},
    "MINIMALIST": {"acc": (100, 100, 100), "icon": "◈", "text_left": 1.5, "text_width": 10.3},
    "NEON NIGHT": {"acc": (0, 255, 150), "icon": "⚡", "text_left": 1.0, "text_width": 11.3},
    "BUSINESS PRO": {"acc": (0, 80, 180), "icon": "✔", "text_left": 1.0, "text_width": 11.3},
    "SUNSET STYLE": {"acc": (255, 230, 0), "icon": "☀️", "text_left": 1.0, "text_width": 11.3}
}

AI_KEY = st.secrets.get("GROQ_API_KEY", "")

def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    prompt = (f"Academic presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"STRICT RULE: Each 'intro' field MUST be 140-160 words. "
              f"Also create a quiz with 10 questions. "
              f"Return JSON: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A','B','C']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"Professor. Write in {lang}. Very long texts (150 words)."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}}, timeout=120)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

def make_pptx(data, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES.get(style_name, THEMES["MINIMALIST"])
    
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(30,30,30)
        
        # 1. Фон
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
            if style_name in ["NEON NIGHT", "SUNSET STYLE", "SCHOOL STYLE"]: txt_rgb = RGBColor(255,255,255)
        except: pass
        
        # 2. Спец-верстка для GIRLY (Рамка)
        if style_name == "GIRLY STYLE":
            rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.2), Inches(10.3), Inches(5.8))
            rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(255,255,255); rect.fill.alpha = 0.8
        
        # 3. Заголовок (Pt 40)
        title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0))
        p_t = title_box.text_frame.paragraphs[0]
        p_t.text = f"{theme['icon']} {str(s.get('title', '')).upper()}"
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(40), True, RGBColor(*theme["acc"])
        
        # 4. Текст (Pt 20) + Позиционирование
        left = Inches(theme["text_left"])
        width = Inches(theme["text_width"])
        tf_obj = slide.shapes.add_textbox(left, Inches(1.4), width, Inches(5.5))
        tf = tf_obj.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(s.get('intro', ''))
        p.font.size, p.font.color.rgb = Pt(20), txt_rgb
        
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    st.header("Настройки")
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Слайды", 2, 12, 6)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    user_code = st.text_input("Код доступа", type="password") 
    
    if st.button("🚀 Сгенерировать"):
        res = ask_ai(t_input, s_count, lang_choice)
        if res:
            st.session_state.data = res
            st.session_state.test_key += 1
            st.session_state.submitted = False
            st.rerun()

if st.session_state.data:
    st.header(f"📝 Текст: {t_input}")
    for i, s in enumerate(st.session_state.data['slides']):
        st.write(f"**Слайд {i+1}** ({len(s.get('intro','').split())} слов)")
        st.write(s.get('intro'))
        st.divider()

    # ПРОВЕРКА КОДА (БЕЗ ПАЛЕВА)
    if user_code == "SX-369":
        st.success("🔓 Режим Admin активен")
        # ИМЯ ФАЙЛА = ТЕМА
        st.download_button("📥 СКАЧАТЬ", make_pptx(st.session_state.data, style_name), f"{t_input}.pptx")
    else:
        st.header("✅ Контрольный тест")
        quiz = st.session_state.data.get('quiz', [])[:10]
        user_ans = []
        for i, q in enumerate(quiz):
            user_ans.append(st.selectbox(f"Вопрос {i+1}: {q['q']}", ["-- Выберите --"] + q['o'], key=f"q_{i}_{st.session_state.test_key}", disabled=st.session_state.submitted))

        if not st.session_state.submitted:
            if st.button("Проверить"):
                if "-- Выберите --" in user_ans: st.warning("Ответьте на всё!")
                else:
                    st.session_state.submitted = True
                    st.rerun()
        else:
            score = sum([1 for i in range(len(quiz)) if user_ans[i] == quiz[i]['a']])
            st.subheader(f"Результат: {score}/10")
            if score >= 8:
                st.balloons()
                # ИМЯ ФАЙЛА = ТЕМА
                st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", make_pptx(st.session_state.data, style_name), f"{t_input}.pptx")
            else:
                st.error("Вы не прошли тест.")
                if st.button("🔄 Сдать заново"):
                    st.session_state.test_key += 1
                    st.session_state.submitted = False
                    st.rerun()

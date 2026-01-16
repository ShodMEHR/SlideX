import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io, time

# 1. ПОРЯДОК СТИЛЕЙ (School первый, Luffy последний)
THEMES = {
    "SCHOOL STYLE": {"acc": (50, 150, 50), "icon": "✏️", "left": 1.0, "width": 11.3, "dark": True},
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
    prompt = (f"Create a deep presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"STRICT RULE: 'intro' MUST be 80-160 words per slide. "
              f"Also create 10 quiz questions. "
              f"Return JSON: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A-..','B-..','C-..']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"Professor. Write in {lang}. Exactly 130 words per slide."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}}, timeout=120)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

def make_pptx(data, style_name, font_size):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES.get(style_name)
    
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(255, 255, 255) if theme["dark"] else RGBColor(30, 30, 30)
        
        try: slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
        except: pass
        
        # ЗАГОЛОВОК (в файле Pt 40)
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0)).text_frame.paragraphs[0]
        p_t.text = f"{theme['icon']} {str(s.get('title', '')).upper()}"
        p_t.font.name = 'Times New Roman'
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(40), True, RGBColor(*theme["acc"])
        
        # ТЕКСТ (в файле Pt {font_size})
        tf_obj = slide.shapes.add_textbox(Inches(theme["left"]), Inches(1.5), Inches(theme["width"]), Inches(5.5))
        tf = tf_obj.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(s.get('intro', ''))
        p.font.name = 'Times New Roman'
        p.font.size, p.font.color.rgb = Pt(font_size), txt_rgb
        tf.line_spacing = 1.2 
        
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

# UI ИНТЕРФЕЙС
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    st.header("Настройки")
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Слайды (от 2 до 12)", 2, 12, 6)
    f_size_final = st.slider("Шрифт в файле (Pt)", 26, 40, 28)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_sel = st.selectbox("Стиль", list(THEMES.keys()))
    user_code = st.text_input("Код доступа", type="password") 
    
    if st.button("🚀 Сгенерировать"):
        with st.status("ИИ пишет текст...") as status:
            res = ask_ai(t_input, s_count, lang_choice)
            if res:
                st.session_state.data = res
                st.session_state.test_key += 1
                st.session_state.submitted = False
                status.update(label="Готово!", state="complete")
                st.rerun()

if st.session_state.data:
    # 1. КОМФОРТНЫЙ ПРОСМОТР (Шрифт обычный, чтобы можно было читать)
    st.header(f"Просмотр контента (Шрифт в файле будет {f_size_final} Pt)")
    for i, s in enumerate(st.session_state.data['slides']):
        st.subheader(f"{THEMES[style_sel]['icon']} Слайд {i+1}: {s.get('title')}")
        # Здесь шрифт обычный, чтобы не было "каши" в браузере
        st.write(s.get('intro'))
        st.divider()

    if user_code == "SX-369":
        st.success("🔓 Режим SX")
        st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_sel, f_size_final), f"{t_input}.pptx")
    else:
        # ТЕСТ
        quiz = st.session_state.data.get('quiz', [])[:10]
        user_ans = []
        for i, q in enumerate(quiz):
            user_ans.append(st.selectbox(f"Вопрос {i+1}: {q['q']}", ["-- Выберите --"] + q['o'], key=f"q_{i}_{st.session_state.test_key}", disabled=st.session_state.submitted))

        if not st.session_state.submitted:
            if st.button("Проверить ответы"):
                if "-- Выберите --" in user_ans: st.warning("Ответьте на всё!")
                else:
                    st.session_state.submitted = True
                    st.rerun()
        else:
            score = 0
            for i, q in enumerate(quiz):
                is_correct = user_ans[i][0] == q['a']
                if is_correct: score += 1
                if is_correct: st.success(f"Вопрос {i+1}: ✅")
                else: st.error(f"Вопрос {i+1}: ❌ (Правильно: {q['a']})")
            
            st.subheader(f"Результат: {score}/10")
            if score >= 8:
                st.balloons()
                # При скачивании применится выбранный шрифт f_size_final
                st.download_button("📥 СКАЧАТЬ ФАЙЛ", make_pptx(st.session_state.data, style_sel, f_size_final), f"{t_input}.pptx")
            else:
                if st.button("🔄 Сдать заново"):
                    st.session_state.test_key += 1
                    st.session_state.submitted = False
                    st.rerun()

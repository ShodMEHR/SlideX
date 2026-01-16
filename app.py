import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io

# 1. СТИЛИ
THEMES = {
    "LUFFY STYLE": {"acc": (200, 30, 30)},
    "GIRLY STYLE": {"acc": (255, 105, 180)},
    "SCHOOL STYLE": {"acc": (200, 255, 200)},
    "MODERN GRADIENT": {"acc": (0, 102, 204)},
    "MINIMALIST": {"acc": (100, 100, 100)},
    "NEON NIGHT": {"acc": (0, 255, 150)},
    "BUSINESS PRO": {"acc": (0, 80, 180)},
    "SUNSET STYLE": {"acc": (255, 230, 0)}
}

AI_KEY = st.secrets.get("GROQ_API_KEY", "")

def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    prompt = (f"Academic presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"STRICT RULE: Each 'intro' MUST be 120-160 words. "
              f"Also create a quiz with 10 questions. "
              f"Return JSON: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A','B','C']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": f"Professor. Write in {lang}. Long texts (130+ words)."},
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
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
            if style_name in ["NEON NIGHT", "SUNSET STYLE", "SCHOOL STYLE"]: txt_rgb = RGBColor(255,255,255)
        except: pass
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9)).text_frame.paragraphs[0]
        p_t.text = str(s.get('title', '')).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(32), True, RGBColor(*theme["acc"])
        tf = slide.shapes.add_textbox(Inches(1.0), Inches(1.4), Inches(11.3), Inches(5.5)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(s.get('intro', ''))
        p.font.size, p.font.color.rgb = Pt(14), txt_rgb
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0
if "submitted" not in st.session_state: st.session_state.submitted = False

with st.sidebar:
    st.header("Настройки")
    t_input = st.text_input("Тема")
    s_count = st.slider("Слайды", 2, 12, 6)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    # Скрытое поле для кода (без упоминания самого кода в тексте!)
    user_code = st.text_input("Код доступа", type="password", help="Введите ваш личный ключ")
    
    if st.button("🚀 Сгенерировать"):
        with st.spinner("Создаю контент..."):
            res = ask_ai(t_input, s_count, lang_choice)
            if res:
                st.session_state.data = res
                st.session_state.test_key += 1
                st.session_state.submitted = False
                st.rerun()

if st.session_state.data:
    # 1. ТЕКСТ (Всегда виден)
    st.header("📝 Просмотр слайдов")
    for i, s in enumerate(st.session_state.data['slides']):
        st.subheader(f"Слайд {i+1}: {s.get('title')} ({len(s.get('intro','').split())} слов)")
        st.write(s.get('intro'))
        st.divider()

    # 2. ЛОГИКА ДОСТУПА
    if user_code == "SX-369": # Код только здесь, в интерфейсе его нет
        st.success("🔓 Доступ разрешен")
        st.download_button("📥 СКАЧАТЬ ФАЙЛ", make_pptx(st.session_state.data, style_name), "pres.pptx")
    else:
        st.header("✅ Проверка знаний")
        quiz = st.session_state.data.get('quiz', [])[:10]
        user_ans = []
        
        # Вывод вопросов
        for i, q in enumerate(quiz):
            a = st.radio(f"{i+1}. {q['q']}", q['o'], key=f"q_{i}_{st.session_state.test_key}", disabled=st.session_state.submitted)
            user_ans.append(a)

        if not st.session_state.submitted:
            if st.button("Проверить ответы"):
                st.session_state.submitted = True
                st.rerun()
        else:
            # ЭКРАН РЕЗУЛЬТАТОВ
            score = sum([1 for i in range(len(quiz)) if user_ans[i] == quiz[i]['a']])
            st.subheader(f"Ваш результат: {score}/10")
            
            for i, q in enumerate(quiz):
                icon = "✅" if user_ans[i] == q['a'] else "❌"
                st.write(f"Вопрос {i+1}: {icon}")

            if score >= 8:
                st.balloons()
                st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", make_pptx(st.session_state.data, style_name), "pres.pptx")
            else:
                st.error("Вы не смогли пройти тест. Нужен балл 8/10.")
                if st.button("🔄 Сдать заново"):
                    st.session_state.test_key += 1
                    st.session_state.submitted = False
                    st.rerun()

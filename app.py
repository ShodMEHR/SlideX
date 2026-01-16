import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
import requests, json, io

# 1. СТИЛИ
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
    # Ультра-жесткий промпт для текста
    prompt = (f"Write a scientific presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"FOR EACH SLIDE: Write exactly 3 long paragraphs (minimum 130 words total per slide). "
              f"This is a strict academic requirement. "
              f"Also create 10 hard quiz questions. "
              f"Return ONLY JSON: {{'slides': [{{'title': '..', 'intro': '..'}}], 'quiz': [{{'q': '..', 'a': 'A', 'o': ['A', 'B', 'C']}}]}}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [
                {"role": "system", "content": "You are a senior professor. You never write less than 130 words per slide. Your texts are extremely detailed."},
                {"role": "user", "content": prompt}
            ], "response_format": {"type": "json_object"}, "temperature": 0.6}, timeout=120)
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except: return None

def make_pptx(data, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    for s in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(255,255,255) if style_name in ["NEON NIGHT", "SUNSET STYLE"] else RGBColor(30,30,30)
        try: slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
        except: pass
        p_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9)).text_frame.paragraphs[0]
        p_t.text = str(s.get('title', '')).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(30), True, RGBColor(*theme["acc"])
        tf = slide.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.3), Inches(5.5)).text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]; p.text = str(s.get('intro', ''))
        p.font.size, p.font.color.rgb = Pt(13), txt_rgb
    buf = io.BytesIO(); prs.save(buf); buf.seek(0)
    return buf

st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state: st.session_state.data = None
if "test_key" not in st.session_state: st.session_state.test_key = 0

with st.sidebar:
    t_input = st.text_input("Тема")
    s_count = st.slider("Слайды", 2, 12, 6)
    lang_choice = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    style_name = st.selectbox("Стиль", list(THEMES.keys()))
    pass_code = st.text_input("Код доступа", type="password")
    if st.button("🚀 Сгенерировать"):
        res = ask_ai(t_input, s_count, lang_choice)
        if res: st.session_state.data = res; st.session_state.test_key += 1; st.rerun()

if st.session_state.data:
    # Отображение контента
    st.header("📝 Тексты слайдов")
    for i, s in enumerate(st.session_state.data['slides']):
        words = len(s.get('intro','').split())
        st.subheader(f"Слайд {i+1}: {s.get('title')} ({words} слов)")
        st.write(s.get('intro'))
        st.divider()

    if pass_code == S_ID:
        st.success("🔓 Режим Admin")
        st.download_button("📥 СКАЧАТЬ", make_pptx(st.session_state.data, style_name), "pres.pptx")
    else:
        st.header("✅ Тест")
        user_answers = []
        quiz = st.session_state.data.get('quiz', [])[:10]
        for i, q in enumerate(quiz):
            ans = st.radio(f"{i+1}. {q['q']}", q['o'], key=f"q_{i}_{st.session_state.test_key}")
            user_answers.append(ans)
        
        if st.button("Проверить результат"):
            correct_count = 0
            results = []
            for i, q in enumerate(quiz):
                is_correct = (user_answers[i] == q['a'])
                if is_correct: correct_count += 1
                results.append((i+1, is_correct))
            
            if correct_count >= 8:
                st.balloons()
                st.download_button("📥 СКАЧАТЬ PPTX", make_pptx(st.session_state.data, style_name), "pres.pptx")
            else:
                st.error(f"Вы не прошли! Результат: {correct_count}/10")
                st.subheader("📊 Ваши ошибки:")
                for num, status in results:
                    icon = "✅ Правильно" if status else "❌ Ошибка!"
                    st.write(f"Вопрос {num}: {icon}")
                
                # Обновляем ключ теста после показа ошибок
                st.session_state.test_key += 1
                st.info("Тест обновлен. Тексты выше помогут найти ответы!")

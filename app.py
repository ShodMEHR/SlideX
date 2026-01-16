import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, io, random

# ================= 1. НАСТРОЙКИ СТИЛЕЙ =================
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

# Ключи и секретный код
AI_KEY = st.secrets.get("GROQ_API_KEY", "")
S_ID = "SX-369"

# ================= 2. ЛОГИКА ИИ =================
def ask_ai(topic, slides, lang):
    if not AI_KEY: return None
    # Запрос к ИИ: строго от 80 до 160 слов на вступление
    prompt = (f"Create a presentation about '{topic}' in {lang}. Slides: {slides}. "
              f"STRICT RULE: 'intro' field must be between 80 and 160 words. "
              f"Format: JSON {{'slides': [{{'title': '...', 'intro': '...', 'points': ['...', '...']}}], "
              f"'quiz': [{{'q': '...', 'a': 'A', 'o': ['A', 'B', 'C']}}]}}")
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }, timeout=120
        )
        return json.loads(r.json()["choices"][0]["message"]["content"])
    except:
        return None

# ================= 3. СОЗДАНИЕ ПРЕЗЕНТАЦИИ =================
def make_pptx(data, topic, style_name):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    theme = THEMES[style_name]
    
    for s in data.get("slides", []):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        txt_rgb = RGBColor(30, 30, 30)
        acc_rgb = RGBColor(*theme["acc"])
        l_m, w_m = Inches(1.0), Inches(11.3)

        # Наложение фона
        try:
            slide.shapes.add_picture(f"{style_name}.jpg", 0, 0, width=prs.slide_width, height=prs.slide_height)
            
            # Адаптация под конкретные картинки
            if style_name == "LUFFY STYLE":
                l_m, w_m = Inches(5.5), Inches(7.3)
            elif style_name == "GIRLY STYLE":
                rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.2), Inches(10.3), Inches(5.8))
                rect.fill.solid(); rect.fill.fore_color.rgb = RGBColor(255, 255, 255); rect.fill.alpha = 0.8
                l_m, w_m = Inches(2.0), Inches(9.3)
            elif style_name in ["SCHOOL STYLE", "NEON NIGHT", "SUNSET STYLE"]:
                txt_rgb = RGBColor(255, 255, 255)
        except:
            pass # Если файла нет, будет просто белый фон

        # Заголовок
        tb_t = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.3), Inches(0.9))
        p_t = tb_t.text_frame.paragraphs[0]
        p_t.text = str(s.get("title", "")).upper()
        p_t.font.size, p_t.font.bold, p_t.font.color.rgb = Pt(36), True, acc_rgb

        # Текст (80-160 слов)
        box = slide.shapes.add_textbox(l_m, Inches(1.4), w_m, Inches(5.5))
        tf = box.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = str(s.get("intro", ""))
        p.font.size, p.font.color.rgb = Pt(14), txt_rgb

        # Пункты
        for pt in s.get("points", []):
            pp = tf.add_paragraph()
            pp.text = f"{theme['icon']}{pt}"
            pp.font.size, pp.font.bold, pp.font.color.rgb = Pt(12), True, acc_rgb

    buf = io.BytesIO()
    prs.save(buf)
    buf.seek(0)
    return buf

# ================= 4. ИНТЕРФЕЙС STREAMLIT =================
st.set_page_config(page_title="SLIDEX PRO", layout="wide")
st.title("🎨 SLIDEX PRO")

if "data" not in st.session_state:
    st.session_state.data = None

# Боковая панель
with st.sidebar:
    st.header("Настройки")
    t_input = st.text_input("Тема презентации")
    s_count = st.slider("Количество слайдов", 2, 12, 6)
    style_name = st.selectbox("Стиль дизайна", list(THEMES.keys()))
    lang = st.selectbox("Язык", ["Russian", "Tajik", "English"])
    pass_code = st.text_input("Код доступа", type="password")
    
    if st.button("🚀 Сгенерировать") and t_input:
        with st.spinner("ИИ готовит презентацию... Это может занять до 2 минут."):
            res = ask_ai(t_input, s_count, lang)
            if res:
                st.session_state.data = res
                st.session_state.topic = t_input
            else:
                st.error("Ошибка! Проверьте API ключ в Secrets.")

# Основной экран
if st.session_state.data:
    st.success(f"Контент для темы '{st.session_state.topic}' готов!")
    
    # Показываем текст прямо на экране, чтобы ты видел работу ИИ
    with st.expander("👀 Посмотреть тексты слайдов"):
        for i, s in enumerate(st.session_state.data['slides']):
            st.write(f"**Слайд {i+1}:** {s['title']}")
            st.write(s['intro'])
            st.divider()

    # Проверка кода доступа или квиз
    if pass_code == S_ID:
        st.info("🔓 Режим разработчика. Код SX-369 принят.")
        buf = make_pptx(st.session_state.data, st.session_state.topic, style_name)
        st.download_button("📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ", buf, f"{st.session_state.topic}.pptx")
    else:
        st.warning("Для скачивания введите секретный код в меню слева или пройдите тест ниже.")
        # Тут можно добавить блок с квизом из st.session_state.data['quiz']

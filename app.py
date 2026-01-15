import streamlit as st
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
import requests, json, re, textwrap, io

# ================= CONFIG (SECURE) =================
# Данные берутся из настроек "Secrets" твоего приложения
try:
    AI_KEY = st.secrets["GROQ_API_KEY"]
    S_ID = st.secrets.get("S_CODE", "SX-369")
except:
    st.error("Ошибка: Настройте Secrets в Streamlit Cloud!")
    st.stop()

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
    mode = "Create a full presentation JSON" if not only_quiz else "Update ONLY the 10 quiz questions"
    
    # ТВОЙ НОВЫЙ ОБЪЕДИНЕННЫЙ ПРОМПТ (80-160 СЛОВ)
    prompt = f"""
    {mode} about "{topic}" in {lang}. 
    Slides: {slides}. 
    
    IMPORTANT RULE:
    Each slide in the "intro" field must contain at least 100-150 words of detailed text.
    No brief points. No cards. No grids. Just deep explanatory paragraphs.
    
    JSON Format:
    {{
      "slides": [{{"title": "", "intro": "DETAILED TEXT MIN 100 WORDS", "points": ["fact 1", "fact 2"]}}],
      "quiz": [{{"q": "", "o": {{"A": "", "B": "", "C": ""}}, "a": "A"}}]
    }}
    """
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_KEY}"},
            json={"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}},
            timeout=45
        ).json()
        return json.loads(r["choices"][0]["message"]["content"].strip())
    except:
        return None

def make_pptx(data, topic, theme_data):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    bg, txt, acc = theme_data["bg"], theme_data["txt"], theme_data["acc"]

    for s in data["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid(); bg_shape.fill.fore_color.rgb = RGBColor(*bg)
        bg_shape.line.fill.background()

        t_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        p = t_box.text_frame.add_paragraph()
        p.text = str(s.get("title", "")).upper()
        p.font.size, p.font.bold, p.font.color.rgb = Pt(34), True, RGBColor(*acc)

        c_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.5))
        tf = c_box.text_frame
        tf.word_wrap = True
        
        p_i = tf.add_paragraph()
        p_i.text = textwrap.fill(str(s.get("intro", "")), width=100)
        p_i.font.size, p_i.font.color.rgb = Pt(16), RGBColor(*txt)
        p_i.space_after = Pt(10)

        for pt in s.get("points", []):
            p_p = tf.add_paragraph()
            p_p.text = f"• {pt}"; p_p.font.size, p_p.font.color.rgb = Pt(14), RGBColor(*acc)

    buffer = io.BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer

# ================= UI =================
st.set_page_config(page_title="SLIDEX PRO", layout="wide", page_icon="🎨")
st.title("🎨 SLIDEX PRO")

# Sessions
if "data" not in st.session_state: st.session_state.data = None
if "step" not in st.session_state: st.session_state.step = "init"
if "test_status" not in st.session_state: st.session_state.test_status = None
if "quiz_key" not in st.session_state: st.session_state.quiz_key = 0

with st.sidebar:
    st.header("⚙️ Настройки")
    t_in = st.text_input("Тема", value=st.session_state.get("t_val", ""))
    s_num = st.slider("Слайды", 2, 12, 6) # Лимит 2-12 слайдов
    style = st.selectbox("Стиль", list(THEMES.keys()))
    lang = st.selectbox("Язык", ["Russian", "English", "Tajik"])
    
    st.write("---")
    # СКРЫТЫЙ ВХОД: точка в самом низу панели
    a_code = st.text_input(".", type="password", help="System focus")
    is_owner = (a_code == S_ID)

    if st.button("🚀 Сгенерировать"):
        if t_in:
            with st.spinner("ИИ готовит контент (100+ слов на слайд)..."):
                res = ask_ai(t_in, s_num, lang)
                if res:
                    st.session_state.data = res
                    st.session_state.step = "preview"
                    st.session_state.t_val = t_in
                    st.session_state.s_count = s_num
                    st.session_state.test_status = None
                    st.session_state.quiz_key += 1
        else:
            st.warning("Введите тему!")

# PREVIEW
if st.session_state.data and st.session_state.step == "preview":
    st.header("📝 Предпросмотр контента")
    if is_owner: st.success("Админ-доступ активирован.")
    
    for i, s in enumerate(st.session_state.data["slides"]):
        with st.expander(f"Слайд {i+1}: {s.get('title')}"):
            st.write(s.get('intro'))
            for p in s.get('points', []): st.write(f"- {p}")
    
    if st.button("Перейти к скачиванию ➔"):
        st.session_state.step = "quiz"
        st.rerun()

# QUIZ / DOWNLOAD
elif st.session_state.data and st.session_state.step == "quiz":
    st.header("📥 Скачивание файла")
    
    quiz_data = st.session_state.data.get("quiz", [])[:10]
    
    if is_owner:
        st.success("Чит-код SX-369 принят. Скачивание разрешено.")
        show_download = True
    else:
        st.info("Ответьте правильно на 8 из 10 вопросов для скачивания.")
        u_ans = []
        for i, q in enumerate(quiz_data):
            st.write(f"**{i+1}. {q['q']}**")
            ans = st.radio(f"Ответ {i}", ["A","B","C"], format_func=lambda x: f"{x}: {q['o'][x]}", 
                           key=f"q_{st.session_state.quiz_key}_{i}")
            u_ans.append(ans)
        
        if st.button("Проверить баллы"):
            score = sum(1 for i, a in enumerate(u_ans) if a == quiz_data[i]["a"])
            if score >= 8:
                st.session_state.test_status = "ok"
            else:
                st.error(f"Ваш балл: {score}/10. Нужно минимум 8.")
                st.session_state.test_status = "fail"
        
        show_download = (st.session_state.test_status == "ok")

    if show_download:
        pptx_buffer = make_pptx(st.session_state.data, st.session_state.t_val, THEMES[style])
        st.download_button(
            label="📥 СКАЧАТЬ ПРЕЗЕНТАЦИЮ (.PPTX)",
            data=pptx_buffer,
            file_name=f"{st.session_state.t_val}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
)    except:
        return None

def make_pptx(data, topic, theme_data):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    bg, txt, acc = theme_data["bg"], theme_data["txt"], theme_data["acc"]

    for s in data["slides"]:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg_shape.fill.solid(); bg_shape.fill.fore_color.rgb = RGBColor(*bg)
        bg_shape.line.fill.background()

        t_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
        p = t_box.text_frame.add_paragraph()
        p.text = str(s.get("title", "")).upper()
        p.font.size, p.font.bold, p.font.color.rgb = Pt(38), True, RGBColor(*acc)

        c_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.5), Inches(12.3), Inches(5.5))
        tf = c_box.text_frame
        tf.word_wrap = True
        
        p_i = tf.add_paragraph()
        p_i.text = textwrap.fill(str(s.get("intro", "")), width=115)
        p_i.font.size, p_i.font.color.rgb = Pt(17), RGBColor(*txt)
        p_i.space_after = Pt(12)

        for pt in s.get("points", []):
            p_p = tf.add_paragraph()
            p_p.text = f"• {pt}"; p_p.font.size, p_p.font.color.rgb = Pt(15), RGBColor(*acc)

    clean_name = re.sub(r'[\\/*?:"<>|]', "", topic)
    path = f"{clean_name[:25]}.pptx"
    prs.save(path)
    return path

# ================= UI =================
st.set_page_config(page_title="SLIDEX PRO", layout="wide", page_icon="🎨")
st.title("🎨 SLIDEX PRO")

# Sessions
if "data" not in st.session_state: st.session_state.data = None
if "step" not in st.session_state: st.session_state.step = "init"
if "test_status" not in st.session_state: st.session_state.test_status = None
if "quiz_key" not in st.session_state: st.session_state.quiz_key = 0

with st.sidebar:
    st.header("⚙️ Настройки")
    t_in = st.text_input("Тема", value=st.session_state.get("t_val", ""))
    s_num = st.slider("Слайды", 2, 12, 6)
    style = st.selectbox("Стиль", list(THEMES.keys()))
    lang = st.selectbox("Язык", ["Russian", "English", "Tajik"])
    a_code = st.text_input("Код доступа", type="password")

    if st.button("🚀 Сгенерировать"):
        if t_in:
            with st.spinner("ИИ готовит контент..."):
                res = ask_ai(t_in, s_num, lang)
                if res:
                    st.session_state.data = res
                    st.session_state.step = "preview"
                    st.session_state.t_val = t_in
                    st.session_state.s_count = s_num
                    st.session_state.test_status = None
                    st.session_state.quiz_key += 1
        else:
            st.warning("Введите тему!")

# PREVIEW
if st.session_state.data and st.session_state.step == "preview":
    st.header("📝 Предпросмотр")
    for i, s in enumerate(st.session_state.data["slides"]):
        with st.expander(f"Слайд {i+1}: {s.get('title')}"):
            st.write(s.get('intro'))
            for p in s.get('points', []): st.write(f"- {p}")
    
    if st.button("Перейти к тесту ➔"):
        st.session_state.step = "quiz"
        st.rerun()

# QUIZ
elif st.session_state.data and st.session_state.step == "quiz":
    st.header("🧠 Тест")
    is_owner = (a_code == S_ID)
    
    u_ans = []
    quiz_data = st.session_state.data.get("quiz", [])[:10]
    
    for i, q in enumerate(quiz_data):
        st.write(f"**{i+1}. {q['q']}**")
        ans = st.radio(f"Ответ {i}", ["A","B","C"], format_func=lambda x: f"{x}: {q['o'][x]}", 
                       key=f"q_{st.session_state.quiz_key}_{i}")
        u_ans.append(ans)

    if st.button("Проверить"):
        score = sum(1 for i, a in enumerate(u_ans) if a == quiz_data[i]["a"])
        if score >= 8 or is_owner:
            st.success(f"Доступ открыт! Балл: {score}/10")
            f_path = make_pptx(st.session_state.data, st.session_state.t_val, THEMES[style])
            with open(f_path, "rb") as f:
                st.download_button("📥 Скачать .pptx", f, file_name=f_path)
            st.session_state.test_status = "ok"
        else:
            st.error(f"Балл {score}/10. Нужно минимум 8.")
            st.session_state.test_status = "fail"

    if st.session_state.test_status == "fail":
        if st.button("Обновить тест и вернуться"):
            with st.spinner("Меняем вопросы..."):
                new = ask_ai(st.session_state.t_val, st.session_state.s_count, lang, only_quiz=True)
                if new: st.session_state.data["quiz"] = new["quiz"]
                st.session_state.quiz_key += 1
                st.session_state.step = "preview"
                st.session_state.test_status = None
                st.rerun()

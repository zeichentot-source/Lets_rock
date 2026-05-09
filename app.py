import streamlit as st
import json
import os
import pandas as pd
from datetime import datetime
import base64

DATA_FILE = 'bookings_web.json'

# --- ФУНКЦИИ ДАННЫХ ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return []

def save_data(entry):
    data = load_data()
    data.append(entry)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- КАЛЬКУЛЯТОР ---
def calculate_price(is_group, date_obj, start_h, end_h):
    total = 0
    day_of_week = date_obj.weekday()
    for hour in range(start_h, end_h):
        if not is_group:
            if 9 <= hour < 12: price = 200
            elif 12 <= hour < 18: price = 300 if day_of_week >= 5 else 250
            elif 18 <= hour < 24: price = 350 if day_of_week >= 4 else 300
            else: price = 300
        else:
            if 9 <= hour < 12: price = 350 if day_of_week >= 5 else 300
            elif 12 <= hour < 18: price = 450 if day_of_week >= 5 else 350
            elif 18 <= hour < 24:
                if day_of_week == 4: price = 450
                elif day_of_week >= 5: price = 500
                else: price = 400
            else: price = 400
        total += price
    return total

# --- ФОН И СТИЛИ ---
def set_background(image_file):
    with open(image_file, "rb") as f:
        img_data = f.read()
    b64_encoded = base64.b64encode(img_data).decode()
    style = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{b64_encoded}");
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    [data-testid="stForm"], .stTable, [data-testid="stDataFrame"] {{
        background-color: rgba(255, 255, 255, 0.4) !important;
        border-radius: 10px;
        padding: 20px;
    }}
    h1, h2, h3 {{
        color: #1a1a1a !important;
        font-weight: bold;
    }}
    label, p, .stMarkdown {{
        color: #000000 !important;
    }}
    </style>
    """
    st.markdown(style, unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ ---
st.set_page_config(page_title="Rock Studio", layout="wide")

if os.path.exists("texture.jpg"):
    set_background("texture.jpg")

st.title("Репетиционная база Let's rock")

col_main, col_image = st.columns([1, 1], gap="large")

with col_main:
    st.subheader("Записаться")
    with st.form("booking_form", clear_on_submit=True):
        u_type = st.radio("Формат:", ["Один человек", "Группа"], horizontal=True)
        name = st.text_input("Имя / Название группы", placeholder="Введите название")
        date = st.date_input("Дата репетиции", format="DD.MM.YYYY")
        
        c1, c2 = st.columns(2)
        start_t = c1.select_slider("Начало", options=list(range(9, 24)), value=12)
        end_t = c2.select_slider("Конец", options=list(range(10, 25)), value=14)
        
        submitted = st.form_submit_button("ЗАБРОНИРОВАТЬ", use_container_width=True)
        
        if submitted:
            if end_t <= start_t:
                st.error("❌ Время конца должно быть позже начала!")
            elif not name:
                st.error("❌ Введите название!")
            else:
                existing = load_data()
                date_str = date.strftime('%d.%m.%y') 
                is_busy = any(b['date'] == date_str and not (end_t <= b['start'] or start_t >= b['end']) for b in existing)
                
                if is_busy:
                    st.error("🚫 Это время уже занято!")
                else:
                    price = calculate_price(u_type == "Группа", date, start_t, end_t)
                    save_data({
                        "Дата": date_str, 
                        "Начало": f"{start_t}:00", 
                        "Конец": f"{end_t}:00", 
                        "Имя": name, 
                        "Сумма": f"{price}₽", 
                        "Тип": u_type, 
                        "start": start_t, 
                        "end": end_t, 
                        "date": date_str
                    })
                    st.success(f"Запись подтверждена. Стоимость: {price}₽")

with col_image:
    st.write("##") 
    if os.path.exists("rock.jpg"):
        st.image("rock.jpg", use_container_width=True)

st.divider()

# --- РАСПИСАНИЕ (С НОВЫМИ ЗАПИСЯМИ ВЕРХУ) ---
st.subheader("Актуальное расписание")
bookings = load_data()
if bookings:
    df = pd.DataFrame(bookings)
    df['sort_date'] = pd.to_datetime(df['date'], format='%d.%m.%y')
    
    # ИСПРАВЛЕНО: Сортировка по убыванию (ascending=False)
    # Теперь новые даты и более позднее время будут сверху
    df = df.sort_values(by=['sort_date', 'start'], ascending=False)
    
    st.dataframe(
        df[["Дата", "Начало", "Конец", "Имя", "Тип", "Сумма"]], 
        use_container_width=True, 
        hide_index=True
    )
else:
    st.info("Пока записей нет.")
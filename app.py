import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os

# --- НАСТРОЙКА ПОДКЛЮЧЕНИЯ ---
# Вставь сюда свою ссылку!
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1mF1K2g8BkuuZdVXFvylMuxTweG7e72cRaG-p0TAEkSc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- ФУНКЦИИ ДАННЫХ ---
def load_data():
    try:
        return conn.read(spreadsheet=SPREADSHEET_URL, usecols=[0,1,2,3,4,5])
    except:
        return pd.DataFrame(columns=["Дата", "Начало", "Конец", "Имя", "Тип", "Сумма"])

def save_data(new_row):
    # Мы будем использовать метод, который просто добавляет строку в конец
    try:
        existing_data = load_data()
        updated_df = pd.concat([existing_data, pd.DataFrame([new_row])], ignore_index=True)
        # Пробуем обновить через прямое обращение
        conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
    except Exception as e:
        st.error(f"Ошибка записи: {e}")

# --- КАЛЬКУЛЯТОР (Твои тарифы) ---
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
    if os.path.exists(image_file):
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
        [data-testid="stForm"], [data-testid="stDataFrame"] {{
            background-color: rgba(255, 255, 255, 0.4) !important;
            border-radius: 10px;
            padding: 20px;
        }}
        h1, h2, h3 {{ color: #1a1a1a !important; font-weight: bold; }}
        label, p {{ color: #000000 !important; }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Rock Studio", layout="wide")
set_background("texture.jpg")

st.title("Rock Studio: Система бронирования")

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
                date_str = date.strftime('%d.%m.%y')
                # Теперь калькулятор на месте!
                price = calculate_price(u_type == "Группа", date, start_t, end_t)
                
                new_entry = {
                    "Дата": date_str,
                    "Начало": f"{start_t}:00",
                    "Конец": f"{end_t}:00",
                    "Имя": name,
                    "Тип": u_type,
                    "Сумма": f"{price}₽"
                }
                save_data(new_entry)
                st.success(f"Запись подтверждена! Сумма: {price}₽")

with col_image:
    if os.path.exists("rock.jpg"):
        st.image("rock.jpg", use_container_width=True)

st.divider()

st.subheader("Актуальное расписание")
df = load_data()
if not df.empty:
    df['dt_obj'] = pd.to_datetime(df['Дата'], format='%d.%m.%y')
    df = df.sort_values(by='dt_obj', ascending=False).drop(columns=['dt_obj'])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("В таблице пока нет записей.")

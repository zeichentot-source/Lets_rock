import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os
import time

# --- 1. НАСТРОЙКА ПОДКЛЮЧЕНИЯ ---
# Библиотека автоматически возьмет данные из Secrets (раздел [connections.gsheets])
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. ФУНКЦИИ ДАННЫХ ---
def load_data():
    try:
        # ttl=0 гарантирует, что мы всегда видим свежие данные из таблицы
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["Дата", "Начало", "Конец", "Имя", "Тип", "Сумма"])

def save_data(new_row):
    try:
        existing_data = load_data()
        new_df = pd.DataFrame([new_row])
        updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        # Сохранение в Google Sheets через Service Account
        conn.update(data=updated_df)
    except Exception as e:
        st.error(f"Ошибка записи: {e}")

# --- 3. КАЛЬКУЛЯТОР ТАРИФОВ ---
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

# --- 4. ДИЗАЙН И СТИЛИЗАЦИЯ (CSS) ---
def set_background(image_file):
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
        style = f"""
        <style>
        /* Фон и общая прозрачность */
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Скрытие системных элементов Streamlit */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        button[title="View fullscreen"] {{ display: none !important; }}
        [data-testid="stElementToolbar"] {{ display: none !important; }}
        [data-testid="stStatusWidget"] {{ visibility: hidden; }}
        
        /* Стили форм и таблиц */
        [data-testid="stForm"], [data-testid="stDataFrame"], [data-testid="stTable"] {{
            background-color: rgba(255, 255, 255, 0.5) !important;
            border-radius: 10px;
            padding: 20px;
        }}

        /* Белые поля для мобильных устройств */
        input, div[data-baseweb="input"], .stTextInput>div>div>input {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }}
        
        button {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #ccc !important;
        }}

        /* Кастомные ползунки с ЧЕРЕПАМИ ☠️ */
        [data-testid="stWidgetLabel"] p {{
            margin-bottom: 25px !important;
            font-size: 18px !important;
        }}

        [data-testid="stTickBar"] {{
            height: 10px !important;
            border-radius: 5px !important;
            background-color: rgba(0, 0, 0, 0.2) !important;
        }}
        
        div[role="slider"] {{
            width: 35px !important;
            height: 35px !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            margin-top: -12px !important; 
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
        }}

        div[role="slider"]::after {{
            content: "☠️" !important;
            font-size: 32px !important;
            display: block !important;
        }}
        
        [data-testid="stSlider"] {{
            touch-action: none !important;
            padding-bottom: 20px !important;
        }}

        /* Шрифты */
        h1, h2, h3, label, p {{ 
            color: #1a1a1a !important; 
            font-weight: bold !important; 
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

# --- 5. ОСНОВНОЙ ИНТЕРФЕЙС ---
st.set_page_config(page_title="Rock Studio ☠️", layout="wide")
set_background("texture.jpg")

st.title("☠️Репетиционная база Let's rock☠️")

col_main, col_image = st.columns([1, 1], gap="large")

with col_main:
    st.subheader("Записаться на репетицию")
    with st.form("booking_form", clear_on_submit=True):
        u_type = st.radio("Формат:", ["Один человек", "Группа"], horizontal=True)
        name = st.text_input("Имя / Название группы", placeholder="Введите текст...")
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
                
                # Проверка занятости времени
                existing_df = load_data()
                is_busy = False
                if not existing_df.empty:
                    for _, row in existing_df.iterrows():
                        if row['Дата'] == date_str:
                            ex_start = int(row['Начало'].split(':')[0])
                            ex_end = int(row['Конец'].split(':')[0])
                            if not (end_t <= ex_start or start_t >= ex_end):
                                is_busy = True
                                break
                
                if is_busy:
                    st.error("🚫 Это время уже занято!")
                else:
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
                    # Пауза, чтобы пользователь увидел сообщение, затем обновление таблицы
                    time.sleep(2)
                    st.rerun()

with col_image:
    if os.path.exists("rock.jpg"):
        st.image("rock.jpg", use_container_width=True)

st.divider()

# --- 6. ТАБЛИЦА РАСПИСАНИЯ ---
st.subheader("Актуальное расписание")
df = load_data()

if df is not None and not df.empty:
    df = df.dropna(how='all')
    try:
        # Сортировка: свежие даты сверху
        df['dt_obj'] = pd.to_datetime(df['Дата'], format='%d.%m.%y')
        df = df.sort_values(by=['dt_obj', 'Начало'], ascending=[False, False]).drop(columns=['dt_obj'])
    except:
        pass
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Пока нет записей. Будь первым! 🤘")

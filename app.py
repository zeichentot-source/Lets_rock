import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import base64
import os

# --- НАСТРОЙКА ПОДКЛЮЧЕНИЯ ---
# Оставляем переменную для совместимости, но Service Account возьмет данные из Secrets
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1mF1K2g8BkuuZdVXFvylMuxTweG7e72cRaG-p0TAEkSc/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- ФУНКЦИИ ДАННЫХ ---
def load_data():
    try:
        # ttl=0 критически важен, чтобы сайт видел новые записи мгновенно
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["Дата", "Начало", "Конец", "Имя", "Тип", "Сумма"])

def save_data(new_row):
    try:
        existing_data = load_data()
        # Создаем DataFrame из новой строки и склеиваем со старыми данными
        new_df = pd.DataFrame([new_row])
        updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        
        # Обновляем таблицу. С Service Account ссылка в методе обычно не нужна, 
        # если она прописана в Secrets под ключом spreadsheet
        conn.update(data=updated_df)
    except Exception as e:
        st.error(f"Ошибка записи: {e}")

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
    if os.path.exists(image_file):
        with open(image_file, "rb") as f:
            img_data = f.read()
        b64_encoded = base64.b64encode(img_data).decode()
        style = f"""
        <style>
        /* 1. ОБЩИЙ ФОН ПРИЛОЖЕНИЯ */
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* 2. СКРЫТИЕ СИСТЕМНЫХ ЭЛЕМЕНТОВ (ЧИСТЫЙ ИНТЕРФЕЙС) */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        button[title="View fullscreen"] {{ display: none !important; }}
        [data-testid="stElementToolbar"] {{ display: none !important; }}
        [data-testid="stStatusWidget"] {{ visibility: hidden; }}
        
        /* 3. ДИЗАЙН ФОРМ И ТАБЛИЦ */
        [data-testid="stForm"], [data-testid="stDataFrame"], [data-testid="stTable"] {{
            background-color: rgba(255, 255, 255, 0.5) !important;
            border-radius: 10px;
            padding: 20px;
        }}

        /* 4. БЕЛЫЕ ПОЛЯ И КНОПКИ ДЛЯ МОБИЛОК (ANTI-DARK MODE) */
        input, div[data-baseweb="input"], .stTextInput>div>div>input {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }}
        
        button {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }}

        /* 5. КАСТОМНЫЕ ПОЛЗУНКИ С ЧЕРЕПАМИ ☠️ */
        
        /* Поднимаем заголовки "Начало"/"Конец", чтобы не мешали цифрам */
        [data-testid="stWidgetLabel"] p {{
            margin-bottom: 25px !important;
            font-size: 18px !important;
        }}

        /* Линия ползунка */
        [data-testid="stTickBar"] {{
            height: 10px !important;
            border-radius: 5px !important;
            background-color: rgba(0, 0, 0, 0.2) !important;
        }}
        
        /* Область захвата бегунка (делаем стандартный кружок невидимым) */
        div[role="slider"] {{
            width: 35px !important;
            height: 35px !important;
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            /* Центрируем череп по вертикали относительно линии */
            margin-top: -12px !important; 
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
        }}

        /* Рисуем череп ☠️ вместо кружка */
        div[role="slider"]::after {{
            content: "☠️" !important;
            font-size: 32px !important;
            display: block !important;
        }}
        
        /* Блокируем скролл страницы при движении черепа */
        [data-testid="stSlider"] {{
            touch-action: none !important;
            padding-bottom: 20px !important;
        }}

        /* 6. ТЕКСТ И ШРИФТЫ */
        h1, h2, h3, label, p {{ 
            color: #1a1a1a !important; 
            font-weight: bold !important; 
        }}
        </style>
        """
        st.markdown(style, unsafe_allow_html=True)

st.divider()

# --- РАСПИСАНИЕ ---
st.subheader("Актуальное расписание")
df = load_data()

if df is not None and not df.empty:
    # Очистка от пустых строк
    df = df.dropna(how='all')
    
    # Сортировка: новые сверху (по дате и по времени начала)
    try:
        df['dt_obj'] = pd.to_datetime(df['Дата'], format='%d.%m.%y')
        df = df.sort_values(by=['dt_obj', 'Начало'], ascending=[False, False]).drop(columns=['dt_obj'])
    except:
        pass
    
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("В таблице пока нет записей.")

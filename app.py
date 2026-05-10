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
        /* 1. Фон приложения */
        .stApp {{
            background-image: url("data:image/png;base64,{b64_encoded}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* 2. Скрытие системных элементов */
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        button[title="View fullscreen"] {{ display: none !important; }}
        [data-testid="stElementToolbar"] {{ display: none !important; }}
        [data-testid="stStatusWidget"] {{ visibility: hidden; }}
        
        /* 3. Формы и таблицы */
        [data-testid="stForm"], [data-testid="stDataFrame"], [data-testid="stTable"] {{
            background-color: rgba(255, 255, 255, 0.5) !important;
            border-radius: 10px;
            padding: 20px;
        }}

        /* 4. Белые поля ввода */
        input, div[data-baseweb="input"], .stTextInput>div>div>input {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }}
        
        button {{
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }}

        /* 5. ЧЕРЕПА ВМЕСТО КРУЖКОВ ☠️ */
        
        [data-testid="stWidgetLabel"] p {{
            margin-bottom: 25px !important;
        }}

        [data-testid="stTickBar"] {{
            height: 8px !important;
            background-color: #444 !important; /* Цвет линии сделаем потемнее */
        }}
        
        /* Стилизуем бегунок */
        div[role="slider"] {{
            background-color: transparent !important; /* Убираем стандарт

# --- ИНТЕРФЕЙС ---
st.set_page_config(page_title="Rock Studio", layout="wide")
set_background("texture.jpg")

st.title("☠️Репетиционная база Let's rock☠️")

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
                
                # Проверка занятости
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
                    
                    # ИСПОЛЬЗУЕМ TOAST (он появится в углу и не исчезнет при rerun)
                    st.toast(f'✅ Запись подтверждена! Сумма: {price}₽', icon='🤘')
                    
                    # Или используем небольшой фокус с задержкой, если хочешь именно большую зеленую плашку:
                    import time
                    st.success(f"Запись подтверждена! Сумма: {price}₽")
                    time.sleep(2) # Даем пользователю 2 секунды почитать, прежде чем сайт моргнет
                    st.rerun()

with col_image:
    if os.path.exists("rock.jpg"):
        st.image("rock.jpg", use_container_width=True)

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

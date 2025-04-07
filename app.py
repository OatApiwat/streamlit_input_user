import streamlit as st
import pymssql
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
from contextlib import contextmanager

# โหลด environment variables จาก .env
load_dotenv()

# การตั้งค่าการเชื่อมต่อฐานข้อมูล
SERVER = os.getenv("SERVER")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

# Connection Pooling
_connection = None

@contextmanager
def get_db_connection():
    global _connection
    if _connection is None:
        _connection = pymssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
    yield _connection

# ฟังก์ชันกำหนด shift จากเวลา
def get_shift(time):
    hour = time.hour
    if 9 <= hour < 10:
        return "A"
    elif 10 <= hour < 11:
        return "B"
    elif 11 <= hour < 13:
        return "C"
    elif 13 <= hour < 24 or 0 <= hour < 9:
        return "D"
    return "Unknown"

# ฟังก์ชันสร้างตารางถ้ายังไม่มี
@st.cache_resource
def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='user_data' AND xtype='U')
        CREATE TABLE user_data (
            no INT IDENTITY(1,1),
            time DATETIME,
            shift NVARCHAR(10),
            data_1 NVARCHAR(255) PRIMARY KEY,
            data_2 NVARCHAR(255),
            data_3 NVARCHAR(255),
            data_4 NVARCHAR(255),
            data_5 NVARCHAR(255)
        )
        """)
        cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_data_1') CREATE INDEX idx_data_1 ON user_data(data_1)")
        cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name='idx_time') CREATE INDEX idx_time ON user_data(time)")
        conn.commit()

# ฟังก์ชันเพิ่มหรืออัปเดตข้อมูลในฐานข้อมูลด้วย MERGE
def add_or_update_data(data_1, data_2, data_3, data_4, data_5):
    current_time = datetime.now()
    shift = get_shift(current_time)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
        MERGE user_data AS target
        USING (SELECT %s AS data_1) AS source
        ON (target.data_1 = source.data_1)
        WHEN MATCHED THEN
            UPDATE SET time = %s, shift = %s, data_2 = %s, data_3 = %s, data_4 = %s, data_5 = %s
        WHEN NOT MATCHED THEN
            INSERT (time, shift, data_1, data_2, data_3, data_4, data_5)
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (data_1, current_time, shift, data_2, data_3, data_4, data_5,
              current_time, shift, data_1, data_2, data_3, data_4, data_5))
        conn.commit()

# ฟังก์ชันดึงข้อมูลจากฐานข้อมูล โดยกรองตาม shift_option
def get_data(cache_buster, shift_option):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if shift_option == "All":
            cursor.execute("""
                SELECT TOP 10 no, time, shift, data_1, data_2, data_3, data_4, data_5
                FROM user_data
                ORDER BY time DESC
            """)
        else:
            cursor.execute("""
                SELECT TOP 10 no, time, shift, data_1, data_2, data_3, data_4, data_5
                FROM user_data
                WHERE shift = %s
                ORDER BY time DESC
            """, (shift_option,))
        rows = cursor.fetchall()
    return rows

def update_form():
    data_1 = st.session_state["data_1"]
    data_2 = st.session_state["data_2"]
    data_3 = st.session_state["data_3"]
    data_4 = st.session_state["data_4"]
    data_5 = st.session_state["data_5"]
    if data_1 and data_2 and data_3 and data_4 and data_5:
        add_or_update_data(data_1, data_2, data_3, data_4, data_5)
        st.session_state["form_submitted"] = True
        st.session_state["data_1"] = ""
        st.session_state["data_2"] = ""
        st.session_state["data_3"] = ""
        st.session_state["data_4"] = ""
        st.session_state["data_5"] = ""
        st.session_state["cache_buster"] += 1  # อัปเดต cache_buster เพื่อรีเฟรชข้อมูล
    else:
        st.session_state["form_submitted"] = False

def clear_form():
    st.session_state["data_1"] = ""
    st.session_state["data_2"] = ""
    st.session_state["data_3"] = ""
    st.session_state["data_4"] = ""
    st.session_state["data_5"] = ""
    st.session_state["form_submitted"] = False

# ฟังก์ชันหลักสำหรับรัน Streamlit UI
def main():
    st.set_page_config(page_title="Program MC1", layout="wide")

    # CSS
    st.markdown("""
    <style>
    .stTextInput > div > input {
        border-radius: 10px;
        padding: 10px;
        border: 2px solid #4CAF50;
        width: 100%;
        margin: 0;
        margin-top: 0px;
    }
    .stButton > button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 10px;
        padding: 10px 20px;
        border: none;
        font-size: 16px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }
    .stButton > button:hover {
        background-color: #e04343;
    }
    .title {
        text-align: center;
        font-size: 36px;
        color: #4CAF50;
        margin-bottom: 20px;
    }
    .subheader {
        font-size: 24px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0;
    }
    .table-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        height: 400px;
        overflow-y: auto;
        margin-top: 0;
    }
    .input-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: -50px;
        margin-top: -5px;
        padding: 0;
    }
    .input-label {
        font-size: 16px;
        color: #333;
        margin: 0;
    }
    .icon {
        font-size: 20px;
    }
    .dataframe td, .dataframe th {
        text-align: center !important;
    }
    .stSelectbox > div > select {
        border-radius: 10px;
        padding: 8px;
        border: 2px solid #4CAF50;
        width: 150px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">Program MC1</div>', unsafe_allow_html=True)
    init_db()

    # ตั้งค่า cache_buster และ form_submitted ถ้ายังไม่มี
    if "cache_buster" not in st.session_state:
        st.session_state["cache_buster"] = 0
    if "form_submitted" not in st.session_state:
        st.session_state["form_submitted"] = False

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="subheader"><span class="icon">📝</span>Input Data</div>', unsafe_allow_html=True)
        with st.form(key="data_form"):
            st.markdown('<div class="input-container"><span class="icon">1️⃣</span><span class="input-label">data_1</span></div>', unsafe_allow_html=True)
            st.text_input("Data 1", placeholder="Enter data_1", key="data_1", label_visibility="hidden")
            st.markdown('<div class="input-container"><span class="icon">2️⃣</span><span class="input-label">data_2</span></div>', unsafe_allow_html=True)
            st.text_input("Data 2", placeholder="Enter data_2", key="data_2", label_visibility="hidden")
            st.markdown('<div class="input-container"><span class="icon">3️⃣</span><span class="input-label">data_3</span></div>', unsafe_allow_html=True)
            st.text_input("Data 3", placeholder="Enter Submit data_3", key="data_3", label_visibility="hidden")
            st.markdown('<div class="input-container"><span class="icon">4️⃣</span><span class="input-label">data_4</span></div>', unsafe_allow_html=True)
            st.text_input("Data 4", placeholder="Enter data_4", key="data_4", label_visibility="hidden")
            st.markdown('<div class="input-container"><span class="icon">5️⃣</span><span class="input-label">data_5</span></div>', unsafe_allow_html=True)
            st.text_input("Data 5", placeholder="Enter data_5", key="data_5", label_visibility="hidden")

            button_col1, button_col2 = st.columns(2)
            with button_col1:
                submit_button = st.form_submit_button(label="Submit  📤", on_click=update_form)
            with button_col2:
                clear_button = st.form_submit_button(label="Clear Data  🗑️", on_click=clear_form)

        if submit_button:
            if st.session_state["form_submitted"]:
                st.success("Data processed successfully! ✅")
            else:
                st.error("Please fill in all fields. ⚠️")
        if clear_button:
            st.info("Input fields cleared! 🧹")

    with col2:
        st.markdown('<div class="subheader"><span class="icon">📊</span>Latest Data</div>', unsafe_allow_html=True)
        shift_option = st.selectbox("Select Shift", ["All", "A", "B", "C", "D"], index=0, key="shift_select")
        data = get_data(st.session_state["cache_buster"], shift_option)
        if data:
            df = pd.DataFrame(data, columns=["no", "time", "shift", "data_1", "data_2", "data_3", "data_4", "data_5"])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("No data available yet. 📉")

if __name__ == "__main__":
    main()

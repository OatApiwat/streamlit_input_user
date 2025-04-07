import streamlit as st
import pymssql
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

# โหลด environment variables จาก .env
load_dotenv()

# การตั้งค่าการเชื่อมต่อฐานข้อมูล
SERVER = os.getenv("SERVER")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

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

# ฟังก์ชันเชื่อมต่อกับ SQL Server และสร้างตารางถ้ายังไม่มี
@st.cache_resource
def init_db():
    conn = pymssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
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
    conn.commit()
    conn.close()

# ฟังก์ชันเพิ่มหรืออัปเดตข้อมูลในฐานข้อมูล
def add_or_update_data(data_1, data_2, data_3, data_4, data_5):
    current_time = datetime.now()
    shift = get_shift(current_time)
    conn = pymssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM user_data WHERE data_1 = %s", (data_1,))
    exists = cursor.fetchone()[0]
    
    if exists:
        cursor.execute("""
        UPDATE user_data 
        SET time = %s, shift = %s, data_2 = %s, data_3 = %s, data_4 = %s, data_5 = %s
        WHERE data_1 = %s
        """, (current_time, shift, data_2, data_3, data_4, data_5, data_1))
    else:
        cursor.execute("""
        INSERT INTO user_data (time, shift, data_1, data_2, data_3, data_4, data_5)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (current_time, shift, data_1, data_2, data_3, data_4, data_5))
    
    conn.commit()
    conn.close()

# ฟังก์ชันดึงข้อมูลจากฐานข้อมูล
@st.cache_data(ttl=10)
def get_data():
    conn = pymssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT TOP 10 no, time, shift, data_1, data_2, data_3, data_4, data_5
        FROM user_data
        ORDER BY time DESC
    """)
    rows = cursor.fetchall()
    conn.close()
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
    else:
        st.session_state["form_submitted"] = False
    
def clear_form():
    st.session_state.status = False
    st.session_state["data_1"] = ""
    st.session_state["data_2"] = ""
    st.session_state["data_3"] = ""
    st.session_state["data_4"] = ""
    st.session_state["data_5"] = ""
    
    
# ฟังก์ชันหลักสำหรับรัน Streamlit UI
def main():
    st.set_page_config(page_title="Program MC1", layout="wide")
    # CSS
    @st.cache_resource
    def get_css():
        return """
        <style>
        .stTextInput > div > input {
            border-radius: 10px;
            padding: 10px;
            border: 2px solid #4CAF50;
            width: 100%;
            margin: 0;
            margin-top: 0px;  /* ลดระยะห่างด้านบนของ input */
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
        </style>"""
    st.markdown(f"<style>{get_css()}</style>", unsafe_allow_html=True)
    st.markdown('<div class="title">Program MC1</div>', unsafe_allow_html=True)
    init_db()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="subheader"><span class="icon">📝</span>Input Data</div>', unsafe_allow_html=True)
        with st.form(key="data_form"):
            # แสดง input fields ใน containersVED
            st.markdown('<div class="input-container"><span class="icon">1️⃣</span><span class="input-label">data_1</span></div>', unsafe_allow_html=True)
            data_10 = st.text_input("Data 1", placeholder="Enter data_1", key="data_1", label_visibility="hidden")
            st.markdown('<div class="input-container"><span class="icon">2️⃣</span><span class="input-label">data_2</span></div>', unsafe_allow_html=True)
            data_20 = st.text_input("Data 2", placeholder="Enter data_2", key="data_2", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">3️⃣</span><span class="input-label">data_3</span></div>', unsafe_allow_html=True)
            data_30 = st.text_input("Data 3", placeholder="Enter data_3", key="data_3", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">4️⃣</span><span class="input-label">data_4</span></div>', unsafe_allow_html=True)
            data_40 = st.text_input("Data 4", placeholder="Enter data_4", key="data_4", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">5️⃣</span><span class="input-label">data_5</span></div>', unsafe_allow_html=True)
            data_50 = st.text_input("Data 5", placeholder="Enter data_5", key="data_5", label_visibility="hidden")
            
            # สร้าง columns สำหรับปุ่ม Submit และ Clear
            button_col1, button_col2 = st.columns(2)
            with button_col1:
                submit_button = st.form_submit_button(label="Submit  📤", on_click=update_form)
            with button_col2:
                clear_button = st.form_submit_button(label="Clear Data  🗑️", on_click=clear_form)

        # เมื่อกดปุ่ม Submit
        if submit_button:
            # if data_10 and data_20 and data_30 and data_40 and data_50:
            if st.session_state["form_submitted"]:
                st.success("Data processed successfully! ✅")
            else:
                st.error("Please fill in all fields. ⚠️")

        # เมื่อกดปุ่ม Clear
        if clear_button:
            st.info("Input fields cleared! 🧹")

    with col2:
        st.markdown('<div class="subheader"><span class="icon">📊</span>Latest Data</div>', unsafe_allow_html=True)
        data = get_data()
        if data:
            df = pd.DataFrame(data, columns=["no", "time", "shift", "data_1", "data_2", "data_3", "data_4", "data_5"])
            shift_option = st.selectbox("Select Shift", ["All", "A", "B", "C", "D"], index=0)
            if shift_option != "All":
                df = df[df["shift"] == shift_option]
            st.dataframe(df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("No data available yet. 📉")

if __name__ == "__main__":
    main()

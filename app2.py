import streamlit as st
import pymssql
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

# Load environment variables from .env
load_dotenv()

# Database connection settings
SERVER = os.getenv("SERVER")
USER = os.getenv("USER")
PASSWORD = os.getenv("PASSWORD")
DATABASE = os.getenv("DATABASE")

# Determine shift based on time
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

# Initialize database and create table if it doesn't exist
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

# Add or update data in the database
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

# Fetch data from the database
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

# Update form submission
def update_form():
    data_1 = st.session_state["data_1"]
    data_2 = st.session_state["data_2"]
    data_3 = st.session_state["data_3"]
    data_4 = st.session_state["data_4"]
    data_5 = st.session_state["data_5"]
    if data_1 and data_2 and data_3 and data_4 and data_5:
        add_or_update_data(data_1, data_2, data_3, data_4, data_5)
        clear_form()

# Clear form inputs
def clear_form():
    st.session_state["data_1"] = ""
    st.session_state["data_2"] = ""
    st.session_state["data_3"] = ""
    st.session_state["data_4"] = ""
    st.session_state["data_5"] = ""

# Main Streamlit UI
def main():
    st.set_page_config(page_title="Program MC1", layout="wide")

    # Custom CSS for enhanced styling
    st.markdown("""
        <style>
        /* General layout */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            font-family: 'Arial', sans-serif;
        }
        
        /* Title */
        .title {
            text-align: center;
            font-size: 40px;
            font-weight: bold;
            color: #ffffff;
            background: linear-gradient(90deg, #4CAF50, #2196F3);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
            padding: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
        }

        /* Subheader */
        .subheader {
            font-size: 26px;
            font-weight: 600;
            color: #2c3e50;
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }

        /* Input fields */
        .stTextInput > div > input {
            border-radius: 12px;
            padding: 12px;
            border: 2px solid #4CAF50;
            background-color: #ffffff;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            transition: border-color 0.3s ease;
            width: 100%;
            margin-top: 5px;
        }
        .stTextInput > div > input:focus {
            border-color: #2196F3;
            outline: none;
            box-shadow: 0 0 8px rgba(33, 150, 243, 0.3);
        }

        /* Buttons */
        .stButton > button {
            background: linear-gradient(90deg, #4CAF50, #66BB6A);
            color: white;
            border-radius: 12px;
            padding: 12px 25px;
            border: none;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #45a049, #5cb85c);
            transform: translateY(-2px);
            box-shadow: 0 5px 10px rgba(0, 0, 0, 0.15);
        }
        .stButton > button:nth-child(2) {
            background: linear-gradient(90deg, #FF4B4B, #F06292);
        }
        .stButton > button:nth-child(2):hover {
            background: linear-gradient(90deg, #e04343, #ec407a);
        }

        /* Input container */
        .input-container {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        .input-label {
            font-size: 16px;
            color: #34495e;
            font-weight: 500;
        }
        .icon {
            font-size: 22px;
        }

        /* Table container */
        .table-container {
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 15px;
            background-color: #ffffff;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
            height: 450px;
            overflow-y: auto;
        }
        .dataframe td, .dataframe th {
            text-align: center !important;
            font-size: 14px;
            padding: 10px !important;
        }
        .dataframe th {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            border-radius: 12px;
            border: 2px solid #4CAF50;
            background-color: #ffffff;
            padding: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
            transition: border-color 0.3s ease;
        }
        .stSelectbox > div > div:hover {
            border-color: #2196F3;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">Program MC1</div>', unsafe_allow_html=True)
    init_db()

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown('<div class="subheader"><span class="icon">📝</span>Input Data</div>', unsafe_allow_html=True)
        with st.form(key="data_form"):
            st.markdown('<div class="input-container"><span class="icon">1️⃣</span><span class="input-label">Data 1</span></div>', unsafe_allow_html=True)
            data_1 = st.text_input("", placeholder="Enter Data 1", key="data_1", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">2️⃣</span><span class="input-label">Data 2</span></div>', unsafe_allow_html=True)
            data_2 = st.text_input("", placeholder="Enter Data 2", key="data_2", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">3️⃣</span><span class="input-label">Data 3</span></div>', unsafe_allow_html=True)
            data_3 = st.text_input("", placeholder="Enter Data 3", key="data_3", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">4️⃣</span><span class="input-label">Data 4</span></div>', unsafe_allow_html=True)
            data_4 = st.text_input("", placeholder="Enter Data 4", key="data_4", label_visibility="hidden")
            
            st.markdown('<div class="input-container"><span class="icon">5️⃣</span><span class="input-label">Data 5</span></div>', unsafe_allow_html=True)
            data_5 = st.text_input("", placeholder="Enter Data 5", key="data_5", label_visibility="hidden")
            
            button_col1, button_col2 = st.columns(2)
            with button_col1:
                submit_button = st.form_submit_button(label="Submit  📤", on_click=update_form)
            with button_col2:
                clear_button = st.form_submit_button(label="Clear  🗑️", on_click=clear_form)

        if submit_button:
            if data_1 and data_2 and data_3 and data_4 and data_5:
                st.success("Data processed successfully! ✅", icon="✅")
            else:
                st.error("Please fill in all fields! ⚠️", icon="⚠️")

        if clear_button:
            st.info("Input fields cleared! 🧹", icon="🧹")

    with col2:
        st.markdown('<div class="subheader"><span class="icon">📊</span>Latest Data</div>', unsafe_allow_html=True)
        data = get_data()
        if data:
            df = pd.DataFrame(data, columns=["No", "Time", "Shift", "Data 1", "Data 2", "Data 3", "Data 4", "Data 5"])
            shift_option = st.selectbox("Filter by Shift", ["All", "A", "B", "C", "D"], index=0)
            if shift_option != "All":
                df = df[df["Shift"] == shift_option]
            # st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=400)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("No data available yet! 📉", icon="📉")

if __name__ == "__main__":
    main()
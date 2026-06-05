import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ตั้งค่าหน้าเว็บ Dashboard
st.set_page_config(page_title="Dental Booking Dashboard - พัน.สร.22 บชร.2", layout="wide")

# ==========================================
# 🔐 ระบบตรวจสอบสิทธิ์เข้าใช้งาน (Login System)
# ==========================================
def check_password():
    """คืนค่า True ถ้าผู้ใช้กรอกรหัสผ่านถูกต้อง"""
    if "login_successful" not in st.session_state:
        st.session_state["login_successful"] = False

    # ถ้าเคยล็อกอินผ่านแล้ว ไม่ต้องแสดงหน้าล็อกอินอีก
    if st.session_state["login_successful"]:
        return True

    # 🛠️ แก้ไขตรงนี้: ปรับตามมาตรฐาน Streamlit เวอร์ชันล่าสุดเรียบร้อยครับ
    st.markdown("<h2 style='text-align: center;'>🔒 ระบบฐานข้อมูลทันตกรรม พัน.สร.22 บชร.2</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>กรุณากรอกชื่อผู้ใช้งานและรหัสผ่านเพื่อเข้าสู่ระบบ</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("ชื่อผู้ใช้งาน (Username)")
            password = st.text_input("รหัสผ่าน (Password)", type="password")
            submit_button = st.form_submit_button("เข้าสู่ระบบ")
            
            if submit_button:
                if username == "Med22" and password == "78520":
                    st.session_state["login_successful"] = True
                    st.rerun() 
                else:
                    st.error("❌ ชื่อผู้ใช้งานหรือรหัสผ่านไม่ถูกต้อง!")
    return False

# ตรวจสอบการล็อกอินก่อนเริ่มทำงาน
if check_password():
    
    if st.sidebar.button("🚪 ออกจากระบบ"):
        st.session_state["login_successful"] = False
        st.rerun()

    # ==========================================
    # 📊 ส่วนเนื้อหาหลักของ Dashboard
    # ==========================================
    st.title("📊 ระบบวิเคราะห์ข้อมูลการจองคิวทันตกรรม พัน.สร.22 บชร.2")
    st.markdown("---")

    # ดึงข้อมูลจาก Google Sheets
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1YEpHTYpkRINABCKue6cBBD0hsCQ_yWS9ttUOtApIaYA/export?format=csv&gid=0"

    @st.cache_data(ttl=600)
    def load_data():
        df = pd.read_csv(SHEET_URL)
        df['วันเวลาที่ต้องการเข้ารับบริการ'] = pd.to_datetime(df['วันเวลาที่ต้องการเข้ารับบริการ'], errors='coerce')
        df['Month-Year'] = df['วันเวลาที่ต้องการเข้ารับบริการ'].dt.strftime('%Y-%m')
        df['Hour'] = df['วันเวลาที่ต้องการเข้ารับบริการ'].dt.hour
        
        cols_to_check = [
            'ประเภทบุคลากร/ทหารประจำการ', 'ประเภทบุคลากร/ทหารกองประจำการ (พลทหาร)',
            'ประเภทบุคลากร/ข้าราชการบำนาญ', 'ประเภทบุคลากร/ครอบครัวทหาร',
            'สิทธิการรักษา/สิทธิ์สวัสดิการรักษาพยาบาลข้าราชการ ', 'สิทธิการรักษา/สิทธิ์ประกันสังคม / สิทธิ์บัตรทอง ',
            'สิทธิการรักษา/สิทธิ์เฉพาะหน่วยงาน ', 'ประเภทหัตถการที่ต้องการจอง/ตรวจสุขภาพช่องปาก / ปรึกษา',
            'ประเภทหัตถการที่ต้องการจอง/ขูดหินปูน', 'ประเภทหัตถการที่ต้องการจอง/ถอนอย่างง่าย'
        ]
        for col in cols_to_check:
            if col in df.columns:
                df[col] = df[col].fillna('').apply(lambda x: True if '✓' in str(x) else False)
        return df

    try:
        df_raw = load_data()
        
        st.sidebar.header("🔍 ตัวกรองข้อมูล (Filters)")
        available_months = sorted(df_raw['Month-Year'].dropna().unique())
        selected_month = st.sidebar.selectbox("เลือกเดือนที่ต้องการดูข้อมูล", ["ทั้งหมด"] + available_months)
        
        if selected_month != "ทั้งหมด":
            df = df_raw[df_raw['Month-Year'] == selected_month]
        else:
            df = df_raw.copy()

        total_bookings = len(df)
        st.columns(1)[0].metric("จำนวนการจองคิวทั้งหมดในรอบที่เลือก", f"{total_bookings} ราย")
        
        st.markdown("### 📈 ข้อมูลสถิติเพื่อการตัดสินใจทางทันตกรรม")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("🎖️ ข้อมูลยศของผู้จอง")
            if 'ยศ' in df.columns and not df['ยศ'].dropna().empty:
                rank_counts = df['ยศ'].value_counts().reset_index()
                fig_rank = px.bar(rank_counts, x='ยศ', y='count', labels={'count':'จำนวน (ราย)'}, text_auto=True, color='ยศ')
                st.plotly_chart(fig_rank, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลยศ")
            
        with col2:
            st.subheader("🏢 ข้อมูลสังกัด")
            if 'สังกัด' in df.columns and not df['สังกัด'].dropna().empty:
                dept_counts = df['สังกัด'].value_counts().reset_index()
                fig_dept = px.pie(dept_counts, names='สังกัด', values='count', hole=0.3)
                st.plotly_chart(fig_dept, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลสังกัด")
            
        with col3:
            st.subheader("👤 ประเภทบุคลากร")
            personnel_types = {
                'ทหารประจำการ': df['ประเภทบุคลากร/ทหารประจำการ'].sum() if 'ประเภทบุคลากร/ทหารประจำการ' in df.columns else 0,
                'พลทหาร': df['ประเภทบุคลากร/ทหารกองประจำการ (พลทหาร)'].sum() if 'ประเภทบุคลากร/ทหารกองประจำการ (พลทหาร)' in df.columns else 0,
                'ข้าราชการบำนาญ': df['ประเภทบุคลากร/ข้าราชการบำนาญ'].sum() if 'ประเภทบุคลากร/ข้าราชการบำนาญ' in df.columns else 0,
                'ครอบครัวทหาร': df['ประเภทบุคลากร/ครอบครัวทหาร'].sum() if 'ประเภทบุคลากร/ครอบครัวทหาร' in df.columns else 0
            }
            df_pers = pd.DataFrame(list(personnel_types.items()), columns=['ประเภท', 'จำนวน'])
            fig_pers = px.bar(df_pers, x='ประเภท', y='จำนวน', text_auto=True, color='ประเภท')
            st.plotly_chart(fig_pers, use_container_width=True)

        st.markdown("---")

        col4, col5, col6 = st.columns(3)
        with col4:
            st.subheader("💳 สิทธิ์การรักษา")
            benefits = {
                'สวัสดิการข้าราชการ': df['สิทธิการรักษา/สิทธิ์สวัสดิการรักษาพยาบาลข้าราชการ '].sum() if 'สิทธิการรักษา/สิทธิ์สวัสดิการรักษาพยาบาลข้าราชการ ' in df.columns else 0,
                'ประกันสังคม/บัตรทอง': df['สิทธิการรักษา/สิทธิ์ประกันสังคม / สิทธิ์บัตรทอง '].sum() if 'สิทธิการรักษา/สิทธิ์ประกันสังคม / สิทธิ์บัตรทอง ' in df.columns else 0,
                'สิทธิ์เฉพาะหน่วยงาน': df['สิทธิการรักษา/สิทธิ์เฉพาะหน่วยงาน '].sum() if 'สิทธิการรักษา/สิทธิ์เฉพาะหน่วยงาน ' in df.columns else 0
            }
            df_ben = pd.DataFrame(list(benefits.items()), columns=['สิทธิ์', 'จำนวน'])
            fig_ben = px.pie(df_ben, names='สิทธิ์', values='จำนวน', hole=0.4)
            st.plotly_chart(fig_ben, use_container_width=True)
            
        with col5:
            st.subheader("🩺 ประวัติโรคประจำตัว (Top 5)")
            if 'ประวัติโรคประจำตัว' in df.columns and not df['ประวัติโรคประจำตัว'].dropna().empty:
                disease_counts = df['ประวัติโรคประจำตัว'].value_counts().reset_index().head(5)
                fig_disease = px.bar(disease_counts, y='ประวัติโรคประจำตัว', x='count', orientation='h', text_auto=True, labels={'count':'จำนวน'})
                st.plotly_chart(fig_disease, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลโรคประจำตัว")
            
        with col6:
            st.subheader("🦷 ประเภทหัตถการที่จอง")
            procedures = {
                'ตรวจช่องปาก/ปรึกษา': df['ประเภทหัตถการที่ต้องการจอง/ตรวจสุขภาพช่องปาก / ปรึกษา'].sum() if 'ประเภทหัตถการที่ต้องการจอง/ตรวจสุขภาพช่องปาก / ปรึกษา' in df.columns else 0,
                'ขูดหินปูน': df['ประเภทหัตถการที่ต้องการจอง/ขูดหินปูน'].sum() if 'ประเภทหัตถการที่ต้องการจอง/ขูดหินปูน' in df.columns else 0,
                'ถอนฟันอย่างง่าย': df['ประเภทหัตถการที่ต้องการจอง/ถอนอย่างง่าย'].sum() if 'ประเภทหัตถการที่ต้องการจอง/ถอนอย่างง่าย' in df.columns else 0
            }
            df_proc = pd.DataFrame(list(procedures.items()), columns=['หัตถการ', 'จำนวน'])
            fig_proc = px.bar(df_proc, x='หัตถการ', y='จำนวน', text_auto=True, color='หัตถการ')
            st.plotly_chart(fig_proc, use_container_width=True)

        st.markdown("---")
        
        st.markdown("### 💡 ส่วนวิเคราะห์เพิ่มเติมเพื่อการบริหารงานทันตกรรม")
        col7, col8 = st.columns(2)
        with col7:
            st.subheader("⏰ ช่วงเวลาที่มีการจองหนาแน่น (Peak Hours)")
            if 'Hour' in df.columns and not df['Hour'].dropna().empty:
                hour_counts = df['Hour'].dropna().value_counts().reset_index().sort_values(by='Hour')
                hour_counts['Hour'] = hour_counts['Hour'].astype(int).apply(lambda x: f"{x}:00 น.")
                fig_hour = px.line(hour_counts, x='Hour', y='count', markers=True, labels={'count':'จำนวนเคส', 'Hour':'เวลา'})
                st.plotly_chart(fig_hour, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลเวลาเข้ารับบริการที่ถูกต้อง")
            
        with col8:
            st.subheader("⚠️ การเฝ้าระวัง: อัตราการแพ้ยาของคนไข้")
            if 'ประวัติการแพ้ยา' in df.columns:
                allergy_counts = df['ประวัติการแพ้ยา'].fillna('ไม่ระบุ').value_counts().reset_index()
                fig_allergy = px.bar(allergy_counts, x='count', y='ประวัติการแพ้ยา', orientation='h', color='ประวัติการแพ้ยา', text_auto=True)
                st.plotly_chart(fig_allergy, use_container_width=True)
            else:
                st.info("ไม่มีข้อมูลประวัติการแพ้ยา")

        st.markdown("---")
        st.subheader("📋 ตารางข้อมูลผู้จองคิวตามตัวกรอง")
        show_cols = [c for c in ['วันเวลาที่ต้องการเข้ารับบริการ', 'ยศ', 'ชื่อ - นามสกุล', 'สังกัด', 'อาการสำคัญ (สาเหตุที่มา)'] if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อหรือประมวลผลข้อมูล: {e}")
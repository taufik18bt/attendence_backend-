import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ⚠️ YAHAN APNA ASLI RENDER URL PASTE KAREIN
# (Agar URL 'postgres://' se shuru hota hai, to code apne aap use theek kar lega)
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm"

# --- URL Fix for SQLAlchemy (Zaroori Hai) ---
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# --- Database Connection Function (Naya Tareeka) ---
def get_db_engine():
    return create_engine(DB_URL)

# --- Page Setup ---
st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🚀 Attendance System Admin")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Live Logs", "➕ Add & View Employees", "📍 View Locations"])

# ==========================================
# TAB 1: LIVE LOGS
# ==========================================
with tab1:
    st.subheader("🕒 Aaj ki Attendance")
    
    if st.button("Refresh Data 🔄", key="refresh_main"):
        st.rerun()

    try:
        engine = get_db_engine()
        query = """
            SELECT 
                u.full_name AS "Name", 
                u.mobile_number AS "Mobile", 
                a.punch_type AS "Type", 
                TO_CHAR(a.punch_time, 'DD-Mon HH24:MI:SS') AS "Time", 
                a.gps_lat, 
                a.gps_long 
            FROM attendance_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.punch_time DESC;
        """
        # Ab hum connection object use kar rahe hain jo Pandas ko pasand hai
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)

        if df.empty:
            st.info("Abhi koi attendance data nahi hai.")
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Database Error: {e}")

# ==========================================
# TAB 2: ADD & VIEW EMPLOYEES
# ==========================================
with tab2:
    st.header("👥 Employee Management")
    
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_users = pd.read_sql(text("SELECT id, full_name, mobile_number, created_at FROM users ORDER BY id ASC;"), conn)
        
        total_emp = len(df_users)
        st.metric(label="Total Employees Added", value=total_emp)
        
        with st.expander("📜 View All Employees List", expanded=True):
            st.dataframe(df_users, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading users: {e}")

    st.markdown("---") 

    st.subheader("👤 Add New Employee")
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
        with col2:
            mobile = st.text_input("Mobile Number")
        location_id = st.number_input("Location ID", min_value=1, value=1)
        
        submitted = st.form_submit_button("✅ Save Employee")
        
        if submitted:
            if name and mobile:
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        # Check duplicate
                        result = conn.execute(text("SELECT id FROM users WHERE mobile_number = :m"), {"m": mobile}).fetchone()
                        
                        if result:
                            st.error("❌ Ye Mobile Number pehle se registered hai!")
                        else:
                            conn.execute(
                                text("INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id) VALUES (:n, :m, 'PENDING', :l)"),
                                {"n": name, "m": mobile, "l": location_id}
                            )
                            conn.commit()
                            st.success(f"User '{name}' add ho gaye! 🎉")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Naam aur Mobile Number bharna zaroori hai.")

# ==========================================
# TAB 3: LOCATIONS
# ==========================================
with tab3:
    st.subheader("📍 Office Locations")
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_loc = pd.read_sql(text("SELECT * FROM locations;"), conn)
        
        st.dataframe(df_loc, use_container_width=True)
        if not df_loc.empty:
            st.map(df_loc.rename(columns={"latitude": "lat", "longitude": "lon"}))
            
    except Exception as e:
        st.error(f"Error: {e}")
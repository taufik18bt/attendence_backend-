import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ⚠️ YAHAN APNA ASLI RENDER URL PASTE KAREIN
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm"

# --- URL Fix ---
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

def get_db_engine():
    return create_engine(DB_URL)

st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🚀 Attendance System Admin")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Live Logs", "➕ Add & View Employees", "🏢 Manage Locations"])

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
            SELECT u.full_name, u.mobile_number, a.punch_type, 
            TO_CHAR(a.punch_time, 'DD-Mon HH24:MI:SS') as time, 
            a.gps_lat, a.gps_long 
            FROM attendance_logs a JOIN users u ON a.user_id = u.id 
            ORDER BY a.punch_time DESC;
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        if df.empty:
            st.info("No data yet.")
        else:
            st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

# ==========================================
# TAB 2: EMPLOYEES
# ==========================================
with tab2:
    st.header("👥 Employee Management")
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_users = pd.read_sql(text("SELECT * FROM users ORDER BY id ASC"), conn)
        
        st.metric("Total Employees", len(df_users))
        with st.expander("View List", expanded=False):
            st.dataframe(df_users)
            
    except Exception as e:
        st.error(str(e))

    st.markdown("---")
    st.subheader("👤 Add New Employee")
    
    with st.form("add_user"):
        col1, col2 = st.columns(2)
        with col1: name = st.text_input("Name")
        with col2: mobile = st.text_input("Mobile")
        
        # Yahan user ko batayenge ki available locations kya hain
        loc_id = st.number_input("Location ID (Existing: 1=Head Office)", min_value=1, value=1)
        
        if st.form_submit_button("Save Employee"):
            if name and mobile:
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        # Check location exists
                        loc_check = conn.execute(text("SELECT id FROM locations WHERE id=:i"), {"i": loc_id}).fetchone()
                        if not loc_check:
                            st.error(f"❌ Location ID {loc_id} nahi mili! Pehle Tab 3 mein jakar Location banayein.")
                        else:
                            conn.execute(
                                text("INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id) VALUES (:n, :m, 'PENDING', :l)"),
                                {"n": name, "m": mobile, "l": loc_id}
                            )
                            conn.commit()
                            st.success("User Added! 🎉")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# TAB 3: LOCATIONS (NEW FEATURE ADDED) 🏢
# ==========================================
with tab3:
    st.header("📍 Manage Offices")
    
    # 1. List Locations
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_loc = pd.read_sql(text("SELECT * FROM locations ORDER BY id ASC"), conn)
        st.dataframe(df_loc, use_container_width=True)
    except:
        pass

    st.markdown("---")
    
    # 2. Add Location Form
    st.subheader("➕ Add New Office Location")
    with st.form("add_loc"):
        c1, c2 = st.columns(2)
        with c1: loc_name = st.text_input("Office Name (e.g. Branch 2)")
        with c2: radius = st.number_input("Radius (Meters)", value=200)
        
        c3, c4 = st.columns(2)
        with c3: lat = st.number_input("Latitude", format="%.6f", value=28.6139)
        with c4: lon = st.number_input("Longitude", format="%.6f", value=77.2090)
        
        if st.form_submit_button("Create Location"):
            try:
                engine = get_db_engine()
                with engine.connect() as conn:
                    conn.execute(
                        text("INSERT INTO locations (name, latitude, longitude, radius_meters) VALUES (:n, :la, :lo, :r)"),
                        {"n": loc_name, "la": lat, "lo": lon, "r": radius}
                    )
                    conn.commit()
                    st.success("New Location Created! ✅")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
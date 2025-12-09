import streamlit as st
import psycopg2
import pandas as pd

# ⚠️ YAHAN APNA ASLI RENDER URL PASTE KAREIN
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm"

# --- Database Connection Function ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

# --- Page Setup ---
st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🚀 Attendance System Admin")

# --- 🔥 TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Live Logs", "➕ Add & View Employees", "📍 View Locations"])

# ==========================================
# TAB 1: LIVE LOGS (Attendance Dekhein)
# ==========================================
with tab1:
    st.subheader("🕒 Aaj ki Attendance")
    
    if st.button("Refresh Data 🔄", key="refresh_main"):
        st.rerun()

    try:
        conn = get_db_connection()
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
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            st.info("Abhi koi attendance data nahi hai.")
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Database Error: {e}")

# ==========================================
# TAB 2: ADD & VIEW EMPLOYEES (Yahan sudhaar kiya hai)
# ==========================================
with tab2:
    st.header("👥 Employee Management")
    
    # --- PART A: LIST DEKHEIN (Kitne log hain) ---
    try:
        conn = get_db_connection()
        # Users ka data layenge
        df_users = pd.read_sql("SELECT id, full_name, mobile_number, created_at FROM users ORDER BY id ASC;", conn)
        conn.close()
        
        # Count dikhayein
        total_emp = len(df_users)
        st.metric(label="Total Employees Added", value=total_emp)
        
        # Table dikhayein
        with st.expander("📜 View All Employees List (Yahan Click Karein)", expanded=True):
            st.dataframe(df_users, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading users: {e}")

    st.markdown("---") 

    # --- PART B: NAYA USER ADD KAREIN ---
    st.subheader("👤 Add New Employee")
    
    with st.form("add_user_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name (Naam)")
        with col2:
            mobile = st.text_input("Mobile Number (Login ID)")
        
        location_id = st.number_input("Location ID (Default: 1)", min_value=1, value=1)
        
        submitted = st.form_submit_button("✅ Save Employee")
        
        if submitted:
            if name and mobile:
                try:
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Check duplicate
                    cur.execute("SELECT id FROM users WHERE mobile_number = %s", (mobile,))
                    if cur.fetchone():
                        st.error("❌ Ye Mobile Number pehle se registered hai!")
                    else:
                        cur.execute("""
                            INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id)
                            VALUES (%s, %s, 'PENDING', %s)
                        """, (name, mobile, location_id))
                        conn.commit()
                        st.success(f"User '{name}' add ho gaye! List update karne ke liye Refresh karein.")
                        st.rerun() # Page auto-refresh karega
                        
                    conn.close()
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
        conn = get_db_connection()
        df_loc = pd.read_sql("SELECT * FROM locations;", conn)
        st.dataframe(df_loc)
        
        if not df_loc.empty:
            st.map(df_loc.rename(columns={"latitude": "lat", "longitude": "lon"}))
            
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
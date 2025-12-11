import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ⚠️ YAHAN APNA ASLI RENDER EXTERNAL URL DALEIN
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm"

# URL Fix
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

def get_db_engine():
    return create_engine(DB_URL)

st.set_page_config(page_title="Admin Panel", layout="wide")
st.title("🚀 Attendance System Admin")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📋 Live Logs", "➕ Add & View Employees", "🏢 Manage Locations"])

# ==========================================
# TAB 1: LIVE LOGS (INDIA TIME) 🇮🇳
# ==========================================
with tab1:
    st.subheader("🕒 Aaj ki Attendance (India Time)")
    if st.button("Refresh Data 🔄", key="refresh_main"):
        st.rerun()

    try:
        engine = get_db_engine()
        query = """
            SELECT 
                u.full_name AS "Name", 
                u.mobile_number AS "Mobile", 
                a.punch_type AS "Type", 
                TO_CHAR(a.punch_time + INTERVAL '5 hours 30 minutes', 'DD-Mon HH12:MI:SS AM') AS "Time (IST)", 
                a.gps_lat, 
                a.gps_long 
            FROM attendance_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.punch_time DESC;
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        
        if df.empty:
            st.info("Abhi koi attendance data nahi hai.")
        else:
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Database Error: {e}")

# ==========================================
# TAB 2: EMPLOYEES
# ==========================================
with tab2:
    st.header("👥 Employee Management")
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_users = pd.read_sql(text("SELECT id, full_name, mobile_number, role, assigned_location_id FROM users ORDER BY id ASC"), conn)
        
        st.metric("Total Employees", len(df_users))
        with st.expander("View Employee List", expanded=False):
            st.dataframe(df_users, use_container_width=True)
            
    except Exception as e:
        st.error(str(e))

    st.markdown("---")
    st.subheader("👤 Add New Employee")
    
    with st.form("add_user"):
        col1, col2 = st.columns(2)
        with col1: name = st.text_input("Full Name")
        with col2: mobile = st.text_input("Mobile Number")
        
        loc_id = st.number_input("Location ID (Default: 1)", min_value=1, value=1)
        
        if st.form_submit_button("Save Employee"):
            if name and mobile:
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        check = conn.execute(text("SELECT id FROM users WHERE mobile_number=:m"), {"m":mobile}).fetchone()
                        if check:
                            st.error("❌ Number pehle se registered hai!")
                        else:
                            conn.execute(
                                text("INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id, role) VALUES (:n, :m, 'PENDING', :l, 'employee')"),
                                {"n": name, "m": mobile, "l": loc_id}
                            )
                            conn.commit()
                            st.success("User Added! 🎉")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# ==========================================
# TAB 3: LOCATIONS (FULL CONTROL) 🏢
# ==========================================
with tab3:
    st.header("📍 Manage Offices")
    
    # 1. LIVE LIST DIKHAO
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            df_loc = pd.read_sql(text("SELECT * FROM locations ORDER BY id ASC"), conn)
        
        st.info("Current Locations List:")
        st.dataframe(df_loc, use_container_width=True)
        
        # Location IDs ki list (Dropdown ke liye)
        loc_options = df_loc['id'].tolist() if not df_loc.empty else []
        
    except Exception as e:
        st.error(f"Error loading locations: {e}")
        loc_options = []

    st.markdown("---")
    
    # --- 3 SECTIONS: ADD | EDIT | DELETE ---
    action = st.radio("Kya karna chahte hain?", ["➕ Add New Location", "✏️ Edit Location", "🗑️ Delete Location"], horizontal=True)

    # ----------- SECTION 1: ADD -----------
    if action == "➕ Add New Location":
        st.subheader("➕ Add New Office")
        with st.form("add_loc"):
            loc_name = st.text_input("Office Name")
            c1, c2, c3 = st.columns(3)
            with c1: lat = st.number_input("Latitude", format="%.6f", value=28.6139)
            with c2: lon = st.number_input("Longitude", format="%.6f", value=77.2090)
            with c3: rad = st.number_input("Radius (m)", value=200)
            
            if st.form_submit_button("Create Location"):
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        conn.execute(
                            text("INSERT INTO locations (name, latitude, longitude, radius_meters) VALUES (:n, :la, :lo, :r)"),
                            {"n": loc_name, "la": lat, "lo": lon, "r": rad}
                        )
                        conn.commit()
                    st.success("Location Added! ✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # ----------- SECTION 2: EDIT -----------
    elif action == "✏️ Edit Location":
        st.subheader("✏️ Update Office Details")
        if not loc_options:
            st.warning("Koi Location nahi hai edit karne ke liye.")
        else:
            # Dropdown se ID select karo
            selected_id = st.selectbox("Select Location ID to Edit", loc_options)
            
            # Us ID ka data nikalo
            selected_row = df_loc[df_loc['id'] == selected_id].iloc[0]
            
            with st.form("edit_loc"):
                new_name = st.text_input("Office Name", value=selected_row['name'])
                c1, c2, c3 = st.columns(3)
                with c1: new_lat = st.number_input("Latitude", format="%.6f", value=float(selected_row['latitude']))
                with c2: new_lon = st.number_input("Longitude", format="%.6f", value=float(selected_row['longitude']))
                with c3: new_rad = st.number_input("Radius (m)", value=int(selected_row['radius_meters']))
                
                if st.form_submit_button("Update Location"):
                    try:
                        engine = get_db_engine()
                        with engine.connect() as conn:
                            conn.execute(
                                text("UPDATE locations SET name=:n, latitude=:la, longitude=:lo, radius_meters=:r WHERE id=:id"),
                                {"n": new_name, "la": new_lat, "lo": new_lon, "r": new_rad, "id": int(selected_id)}
                            )
                            conn.commit()
                        st.success("Location Updated! 🔄")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ----------- SECTION 3: DELETE -----------
    elif action == "🗑️ Delete Location":
        st.subheader("🗑️ Delete Office")
        st.warning("⚠️ Dhyan rahe: Agar is Office mein Employees assigned hain, to ye delete nahi hoga.")
        
        if not loc_options:
            st.warning("Delete karne ke liye kuch nahi hai.")
        else:
            del_id = st.selectbox("Select Location ID to Delete", loc_options)
            
            if st.button("❌ Permanently Delete"):
                try:
                    engine = get_db_engine()
                    with engine.connect() as conn:
                        # Pehle check karo koi employee to nahi hai
                        emp_count = conn.execute(text("SELECT COUNT(*) FROM users WHERE assigned_location_id=:id"), {"id": int(del_id)}).scalar()
                        
                        if emp_count > 0:
                            st.error(f"❌ Delete Failed! Is office mein abhi {emp_count} employees hain. Pehle unhe shift karein.")
                        else:
                            conn.execute(text("DELETE FROM locations WHERE id=:id"), {"id": int(del_id)})
                            conn.commit()
                            st.success(f"Location ID {del_id} Deleted! 🗑️")
                            st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
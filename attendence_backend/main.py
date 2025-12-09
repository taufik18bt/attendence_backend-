
import csv
import io
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import os




app = FastAPI()



# --- ISSE PASTE KAREIN (CORS PERMISSION) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Sabko allow karo (Mobile app + HTML file)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------------------------------

# --- DATABASE SETTINGS ---



# Direct URL paste karein (Jo copy kiya tha). Prefer using env var in production:
DB_URL = os.getenv("DATABASE_URL")


# Database Connection Function — use the DSN string `DB_URL`.
def get_db_connection():
    try:
        return psycopg2.connect(DB_URL)
    except Exception as e:
        print("Database Connection Error:", e)
        return None

# --- API ENDPOINTS ---

# 1. Test API: Ye check karega ki server chal raha hai ya nahi
@app.get("/")
def home():
    return {"message": "Attendance System Backend is Running!"}

# 2. Test Database: Ye check karega ki database connect hua ya nahi
@app.get("/check-db")
def check_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"status": "Success", "message": "Database Connected Successfully!"}
    else:
        raise HTTPException(status_code=500, detail="Database Connection Failed")

# --- for punch  ---

import math
from datetime import datetime

# Data Model for Punch
class PunchSchema(BaseModel):
    user_id: int
    punch_type: str  # "IN" or "OUT"
    latitude: float
    longitude: float
    device_id: str
   
   

# 1. Haversine Formula (Do points ke beech doori napne ke liye)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# 2. Punch API


@app.post("/api/punch")
def submit_punch(data: PunchSchema):
    
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # A. User ki assigned location nikalo
        cursor.execute("""
            SELECT l.latitude, l.longitude, l.radius_meters 
            FROM users u 
            JOIN locations l ON u.assigned_location_id = l.id 
            WHERE u.id = %s
        """, (data.user_id,))
        
        assigned_loc = cursor.fetchone()
        
        if not assigned_loc:
            raise HTTPException(status_code=404, detail="User or Location not found")

        # --- FIX IS HERE (Decimal ko Float banana) ---
        office_lat = float(assigned_loc['latitude'])   # <--- Ye naya hai
        office_long = float(assigned_loc['longitude']) # <--- Ye naya hai
        office_radius = int(assigned_loc['radius_meters'])

        # B. Distance Calculate karo (Ab ye chalega!)
        dist = calculate_distance(
            data.latitude, data.longitude,
            office_lat, office_long
        )
        
        print(f"User Distance: {dist} meters") 

        # C. Check karo: Kya user radius ke andar hai?
        if dist > office_radius:
            raise HTTPException(status_code=400, detail=f"You are too far! Distance: {int(dist)}m")

        # D. Agar pass hai, to attendance save karo
        cursor.execute("""
            INSERT INTO attendance_logs (user_id, punch_type, gps_lat, gps_long, is_synced)
            VALUES (%s, %s, %s, %s, TRUE)
        """, (data.user_id, data.punch_type, data.latitude, data.longitude))
        
        conn.commit()
        return {"status": "Success", "message": f"Punch {data.punch_type} Accepted!"}

    except Exception as e:
        conn.rollback()
        print("Error:", e) # Terminal me error print karega
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass



# --- for login ---
class LoginSchema(BaseModel):
    mobile_number: str

@app.post("/api/login")
def login_user(data: LoginSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if mobile number exists
        cursor.execute("""
            SELECT id, full_name 
            FROM users 
            WHERE mobile_number = %s
        """, (data.mobile_number,))

        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found! Register first.")

        return {
            "status": "Success", 
            "message": "Login Successful", 
            "user": user
        }

    except Exception as e:
        print("Login Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

        # --- ADD EMPLOYEE API (Admin Panel ke liye) ---

class NewUserSchema(BaseModel):
    full_name: str
    mobile_number: str
    device_id: str = "ADMIN_ADDED"
    assigned_location_id: int = 1  # Default Location 1 (Head Office)

@app.post("/api/add-user")
def add_new_user(user: NewUserSchema):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check karo number pehle se to nahi hai?
        cursor.execute("SELECT id FROM users WHERE mobile_number = %s", (user.mobile_number,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Mobile Number already exists!")

        # Naya User Insert karo
        cursor.execute("""
            INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
        """, (user.full_name, user.mobile_number, user.device_id, user.assigned_location_id))
        
        new_row = cursor.fetchone()
        new_id = new_row['id'] if isinstance(new_row, dict) else new_row[0]
        conn.commit()
        
        return {"status": "Success", "message": "User Added Successfully", "user_id": new_id}

    except Exception as e:
        conn.rollback()
        print("Add User Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

        # --- EXPORT TO CSV API ---

@app.get("/api/export")
def export_attendance_csv():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    
    try:
        cursor = conn.cursor() # Dictionary cursor nahi chahiye, normal cursor chahiye
        
        # Data nikalo
        query = """
            SELECT 
                u.full_name, 
                u.mobile_number, 
                a.punch_type, 
                a.punch_time, 
                a.gps_lat, 
                a.gps_long 
            FROM attendance_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.punch_time DESC;
        """
        cursor.execute(query)
        logs = cursor.fetchall()
        
        # 1. Memory mein CSV file banao
        stream = io.StringIO()
        csv_writer = csv.writer(stream)
        
        # 2. Headings likho
        csv_writer.writerow(["Employee Name", "Mobile Number", "Punch Type", "Time", "Latitude", "Longitude"])
        
        # 3. Data Rows likho
        for log in logs:
            # Note: Normal cursor tuples return karta hai (index 0, 1, 2...)
            csv_writer.writerow([
                log[0], # full_name
                log[1], # mobile
                log[2], # punch_type
                str(log[3]), # punch_time
                log[4], # lat
                log[5]  # long
            ])
            
        # 4. File ko download ke liye ready karo
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=attendance_report.csv"
        
        return response

    except Exception as e:
        print("Export Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass


        # --- ADMIN REPORT API ---

@app.get("/api/reports")
def get_attendance_report():
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB Connection Failed")
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Attendance + User details join karke nikalo
        query = """
            SELECT 
                u.full_name, 
                u.mobile_number, 
                a.punch_type, 
                a.punch_time, 
                a.gps_lat, 
                a.gps_long 
            FROM attendance_logs a
            JOIN users u ON a.user_id = u.id
            ORDER BY a.punch_time DESC;
        """
        cursor.execute(query)
        logs = cursor.fetchall()
        
        return {"status": "Success", "data": logs}

    except Exception as e:
        print("Report Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
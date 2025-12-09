from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from math import radians, cos, sin, asin, sqrt

app = FastAPI()

# --- DATABASE CONNECTION ---
# ⚠️ Yahan apna ASLI Render URL dalein
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print("Database Connection Error:", e)
        return None

# --- DISTANCE FORMULA ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return (R * c) * 1000

# --- DATA MODELS ---
class LoginRequest(BaseModel):
    mobile_number: str
    device_id: str = "Unknown"

class PunchRequest(BaseModel):
    mobile_number: str
    latitude: float
    longitude: float
    punch_type: str 

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "System Live hai! 🚀"}

# ✅ YE HAI WO MISSING LOGIN ENDPOINT
@app.post("/api/login")
def login(request: LoginRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Error")
    
    cursor = conn.cursor()
    try:
        # Check if user exists
        # Hum space hata kar (strip) check karenge taaki galti na ho
        clean_mobile = request.mobile_number.strip()
        
        cursor.execute("SELECT * FROM users WHERE mobile_number = %s", (clean_mobile,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found! Admin se baat karein.")
            
        return {
            "status": "Success",
            "message": "Login Approved",
            "user": user
        }
    except Exception as e:
        print("Login Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ❌ Purana (Ise hata dein):
# @app.post("/punch")

# ✅ Naya (Ye likhein):
@app.post("/api/punch")
def mark_attendance(request: PunchRequest):
    # ... baki code same rahega ...
def mark_attendance(request: PunchRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Error")
    
    cursor = conn.cursor()
    try:
        clean_mobile = request.mobile_number.strip()
        
        cursor.execute("SELECT id, full_name, assigned_location_id FROM users WHERE mobile_number = %s", (clean_mobile,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Get Office Location
        cursor.execute("SELECT latitude, longitude, radius_meters FROM locations WHERE id = %s", (user['assigned_location_id'],))
        office = cursor.fetchone()
        
        if not office:
            # Agar office nahi mila, to Head Office (ID 1) default maan lete hain
            cursor.execute("SELECT latitude, longitude, radius_meters FROM locations WHERE id = 1")
            office = cursor.fetchone()

        # Distance Check
        dist = calculate_distance(
            request.latitude, request.longitude, 
            float(office['latitude']), float(office['longitude'])
        )
        
        if dist > office['radius_meters']:
            raise HTTPException(status_code=400, detail=f"Too Far! You are {int(dist)}m away from office.")

        # Save Punch
        cursor.execute("""
            INSERT INTO attendance_logs (user_id, punch_type, gps_lat, gps_long)
            VALUES (%s, %s, %s, %s)
        """, (user['id'], request.punch_type, request.latitude, request.longitude))
        
        conn.commit()
        return {"status": "Success", "message": "Punch Accepted!", "distance": int(dist)}

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
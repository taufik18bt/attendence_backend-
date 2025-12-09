from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from math import radians, cos, sin, asin, sqrt

app = FastAPI()

# ⚠️ Yahan DATABASE URL hona chahiye (postgres:// wala), Server URL nahi!
DB_URL = os.getenv("DATABASE_URL", "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print("DB Error:", e)
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    return (R * c) * 1000

class LoginRequest(BaseModel):
    mobile_number: str
    device_id: str = "Unknown"

class PunchRequest(BaseModel):
    user_id: int          
    latitude: float
    longitude: float
    punch_type: str
    device_id: str | None = None 

@app.get("/")
def home():
    return {"message": "System Live hai! 🚀"}

# ✅ LOGIN FIX
@app.post("/api/login")
def login(request: LoginRequest):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database Error")
    cursor = conn.cursor()
    try:
        clean_mobile = request.mobile_number.strip()
        cursor.execute("SELECT * FROM users WHERE mobile_number = %s", (clean_mobile,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found! Pehle Admin se add karein.")
            
        return {"status": "Success", "message": "Login Approved", "user": user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ✅ PUNCH FIX
@app.post("/api/punch")
def mark_attendance(request: PunchRequest):
    conn = get_db_connection()
    if not conn: raise HTTPException(status_code=500, detail="Database Error")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (request.user_id,))
        user = cursor.fetchone()
        if not user: raise HTTPException(status_code=404, detail="User not found")
        
        # Location Logic
        loc_id = user.get('assigned_location_id')
        if loc_id:
            cursor.execute("SELECT latitude, longitude, radius_meters FROM locations WHERE id = %s", (loc_id,))
            office = cursor.fetchone()
        else:
            cursor.execute("SELECT latitude, longitude, radius_meters FROM locations WHERE id = 1")
            office = cursor.fetchone()

        if not office: raise HTTPException(status_code=400, detail="Office Location missing")

        dist = calculate_distance(request.latitude, request.longitude, float(office['latitude']), float(office['longitude']))
        
        if dist > office['radius_meters']:
            raise HTTPException(status_code=400, detail=f"Too Far! You are {int(dist)}m away.")

        cursor.execute("""
            INSERT INTO attendance_logs (user_id, punch_type, gps_lat, gps_long)
            VALUES (%s, %s, %s, %s)
        """, (request.user_id, request.punch_type, request.latitude, request.longitude))
        conn.commit()
        return {"status": "Success", "message": "Punch Accepted!", "distance": int(dist)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from math import radians, cos, sin, asin, sqrt

app = FastAPI()

# --- DATABASE CONNECTION ---
# ⚠️ Yahan apna ASLI Render External URL dalein
DB_URL = os.getenv("postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm")

def get_db_connection():
    try:
        conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print("Database Connection Error:", e)
        return None

# --- 🌍 MATHS FORMULA (Do points ke beech doori napne ke liye) ---
def calculate_distance(lat1, lon1, lat2, lon2):
    # Earth ka radius (kilometers mein)
    R = 6371 
    
    # Degree ko Radians mein badalna
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a))
    
    # Distance in Meters
    distance_meters = (R * c) * 1000
    return distance_meters

# --- DATA MODELS ---
class PunchRequest(BaseModel):
    mobile_number: str
    latitude: float
    longitude: float
    punch_type: str # 'IN' or 'OUT'

# --- API ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "Attendance System is Running with Geofencing! 🔒"}

@app.get("/check-db")
def check_db():
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"status": "Success", "message": "Database Connected Successfully!"}
    return {"status": "Failed", "message": "Database Connection Failed"}

@app.post("/punch")
def mark_attendance(request: PunchRequest):
    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database Error")
    
    cursor = conn.cursor()
    
    try:
        # 1. User ko dhoondo
        cursor.execute("SELECT id, full_name, assigned_location_id FROM users WHERE mobile_number = %s", (request.mobile_number,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found! Pehle Admin se register karwayein.")
            
        user_id = user['id']
        location_id = user['assigned_location_id']
        
        # 2. Office ki Location nikalo
        cursor.execute("SELECT latitude, longitude, radius_meters FROM locations WHERE id = %s", (location_id,))
        office = cursor.fetchone()
        
        if not office:
            raise HTTPException(status_code=400, detail="Office Location set nahi hai.")

        # 3. 📏 DISTANCE CHECK (Sabse Zaroori Logic)
        dist = calculate_distance(
            request.latitude, request.longitude, 
            float(office['latitude']), float(office['longitude'])
        )
        
        print(f"User Distance: {dist} meters") # Logs mein dikhega
        
        # Agar user range se bahar hai (e.g. > 200 meters)
        if dist > office['radius_meters']:
            raise HTTPException(status_code=400, detail=f"Failed! Aap Office se {int(dist)}m door hain. Pass jayen!")

        # 4. Agar range mein hai, to Punch Save karo
        cursor.execute("""
            INSERT INTO attendance_logs (user_id, punch_type, gps_lat, gps_long)
            VALUES (%s, %s, %s, %s)
        """, (user_id, request.punch_type, request.latitude, request.longitude))
        
        conn.commit()
        return {
            "status": "Success", 
            "message": f"Punch {request.punch_type} Successful!", 
            "distance_meters": int(dist),
            "name": user['full_name']
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
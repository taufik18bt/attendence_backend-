import psycopg2
import os

# --- ⚠️ YAHAN APNA RENDER KA EXTERNAL URL PASTE KARNA HAI ---
# Example: "postgres://user:pass@host.render.com/db"
# "Internal URL" mat dalna, "External URL" dalna!
DB_URL = "YAHAN_RENDER_KA_EXTERNAL_URL_PASTE_KAREIN" 

def create_tables():
    try:
        # Database connect karo
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        print("Database Connected! Creating Tables...")

        # 1. Locations Table (Office coordinates ke liye)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                latitude DECIMAL(9,6),
                longitude DECIMAL(9,6),
                radius_meters INT DEFAULT 100
            );
        """)

        # 2. Users Table (Employees ke liye)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100),
                mobile_number VARCHAR(15) UNIQUE NOT NULL,
                device_id VARCHAR(100),
                assigned_location_id INT REFERENCES locations(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Attendance Logs Table (Punch IN/OUT ke liye)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_logs (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                punch_type VARCHAR(10) CHECK (punch_type IN ('IN', 'OUT')),
                punch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gps_lat DECIMAL(9,6),
                gps_long DECIMAL(9,6),
                is_synced BOOLEAN DEFAULT FALSE
            );
        """)

        # --- SPECIAL: Ek Default Office Location Daal dete hain ---
        # Taaki jab aap pehla user add karein to error na aaye
        cursor.execute("""
            INSERT INTO locations (name, latitude, longitude, radius_meters)
            SELECT 'Head Office', 28.6139, 77.2090, 200
            WHERE NOT EXISTS (SELECT 1 FROM locations);
        """)
        
        conn.commit()
        print("Success! Sabhi Tables (Users, Locations, Logs) ban gayi hain via Python.")
        print("Ek default 'Head Office' location bhi add kar di gayi hai.")

    except Exception as e:
        print("Error aaya:", e)
    finally:
        if conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_tables()
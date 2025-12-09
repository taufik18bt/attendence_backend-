import psycopg2

# --- ⚠️ YAHAN APNA RENDER EXTERNAL URL PASTE KAREIN ---
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm" 

def reset_database():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        print("Purani tables delete kar raha hoon...")
        
        # 1. Drop Tables (Purana kachra saaf karein)
        cursor.execute("DROP TABLE IF EXISTS attendance_logs CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS users CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS locations CASCADE;")
        
        print("Nayi Tables bana raha hoon...")

        # 2. Create Locations
        cursor.execute("""
            CREATE TABLE locations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                latitude DECIMAL(9,6),
                longitude DECIMAL(9,6),
                radius_meters INT DEFAULT 100
            );
        """)

        # 3. Create Users (Ab 'device_id' ke saath!)
        cursor.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100),
                mobile_number VARCHAR(15) UNIQUE NOT NULL,
                device_id VARCHAR(100),
                assigned_location_id INT REFERENCES locations(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. Create Logs
        cursor.execute("""
            CREATE TABLE attendance_logs (
                id SERIAL PRIMARY KEY,
                user_id INT REFERENCES users(id),
                punch_type VARCHAR(10) CHECK (punch_type IN ('IN', 'OUT')),
                punch_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                gps_lat DECIMAL(9,6),
                gps_long DECIMAL(9,6),
                is_synced BOOLEAN DEFAULT FALSE
            );
        """)

        # 5. Default Location Add karein
        cursor.execute("""
            INSERT INTO locations (name, latitude, longitude, radius_meters)
            VALUES ('Head Office', 28.6139, 77.2090, 200);
        """)

        conn.commit()
        print("\n✅ Success! Database poora naya ban gaya hai.")
        print("Ab aap 'add_user.py' chala sakte hain.")

    except Exception as e:
        print("❌ Error:", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_database()
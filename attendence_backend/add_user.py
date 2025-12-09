import psycopg2

# --- ⚠️ YAHAN APNA RENDER KA EXTERNAL URL PASTE KAREIN ---
DB_URL = "postgresql://admin:ZvzYYMivJ38wnBdJaKsANwRQe5KHALAW@dpg-d4rhpn49c44c7390ikgg-a.singapore-postgres.render.com/attendence_db_96rm" 

def add_test_user():
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        
        # 1. Check karein ki Location hai ya nahi
        cursor.execute("SELECT id FROM locations LIMIT 1;")
        loc = cursor.fetchone()
        
        if not loc:
            print("Pehle Location banani padegi...")
            cursor.execute("INSERT INTO locations (name, latitude, longitude, radius_meters) VALUES ('Head Office', 28.6139, 77.2090, 200) RETURNING id;")
            loc_id = cursor.fetchone()[0]
        else:
            loc_id = loc[0]

        # 2. User Add karein
        # 👇 Yahan apna Mobile Number dalein jo App me use karte hain
        my_mobile = "1234567890"  
        my_name = "Test Admin"
        
        cursor.execute("""
            INSERT INTO users (full_name, mobile_number, device_id, assigned_location_id)
            VALUES (%s, %s, 'TEST_DEVICE_ID', %s)
            RETURNING id;
        """, (my_name, my_mobile, loc_id))
        
        new_user_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"\n✅ Success! User ban gaya.")
        print(f"Name: {my_name}")
        print(f"Mobile: {my_mobile}")
        print(f"User ID: {new_user_id}")
        print("---------------------------------------")
        print("Ab App mein jao aur 'Login' ya 'Punch' try karo!")

    except psycopg2.IntegrityError:
        print("⚠️ Ye Mobile Number pehle se registered hai.")
    except Exception as e:
        print("❌ Error:", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_test_user()
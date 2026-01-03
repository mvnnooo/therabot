import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def test_pythonanywhere_connection():
    config = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'port': int(os.getenv('DB_PORT', 3306))
    }
    
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # اختبار استعلام بسيط
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        print(f"✅ Connection successful! Result: {result}")
        
        # عرض معلومات قاعدة البيانات
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📊 Tables in database: {len(tables)}")
        
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        connection.close()
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ Connection failed: {err}")
        return False

if __name__ == "__main__":
    test_pythonanywhere_connection()
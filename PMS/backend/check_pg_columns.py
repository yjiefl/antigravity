
import asyncio
import os
import sys
import psycopg2

# Connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "plan_management"
DB_USER = "pms"
DB_PASS = "pms_secret_2026"

def check_columns():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='tasks';
        """)
        
        columns = cursor.fetchall()
        print("Tasks table columns:")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    check_columns()

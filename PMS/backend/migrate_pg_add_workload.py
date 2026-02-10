
import psycopg2
import sys

# Connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "plan_management"
DB_USER = "pms"
DB_PASS = "pms_secret_2026"

def migrate():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to PostgreSQL database.")
        
        # Add workload_b
        try:
            print("Adding 'workload_b' column to 'tasks' table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN workload_b DOUBLE PRECISION DEFAULT 0.0;")
            print("Column added successfully.")
        except psycopg2.errors.DuplicateColumn:
            print("Column 'workload_b' already exists.")
        except Exception as e:
            print(f"Error adding workload_b: {e}")

        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

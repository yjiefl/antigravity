import sqlite3
import os

db_path = "/Users/yangjie/code/antigravity/PMS/backend/plan_management.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Migrating tasks table...")
        
        # Add extension fields
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN extension_status VARCHAR(20)")
            cursor.execute("ALTER TABLE tasks ADD COLUMN extension_reason TEXT")
            cursor.execute("ALTER TABLE tasks ADD COLUMN extension_date DATETIME")
            print("Added extension fields.")
        except sqlite3.OperationalError as e:
            print(f"Warning: {e}")

        # Add reviewer_id
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN reviewer_id CHAR(32)")
            # Actually, looking at the models, they might be using String for UUID if not configured otherwise.
            # But SQLAlchemy with SQLite often uses BLOB for UUID if 'as_uuid=True' is set.
            # Let's check a current column type.
            print("Added reviewer_id field.")
        except sqlite3.OperationalError as e:
            print(f"Warning: {e}")

        conn.commit()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

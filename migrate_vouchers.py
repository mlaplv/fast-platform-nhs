import sqlite3
import os

db_path = "fast_platform.db" # Check if this is the correct DB

def migrate():
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE vouchers ADD COLUMN category TEXT DEFAULT 'DISCOUNT'")
        print("Added column 'category' to 'vouchers'")
    except sqlite3.OperationalError as e:
        print(f"Column 'category' error: {e}")

    try:
        cursor.execute("ALTER TABLE vouchers ADD COLUMN is_default BOOLEAN DEFAULT 0")
        print("Added column 'is_default' to 'vouchers'")
    except sqlite3.OperationalError as e:
        print(f"Column 'is_default' error: {e}")

    try:
        cursor.execute("ALTER TABLE vouchers ADD COLUMN priority INTEGER DEFAULT 0")
        print("Added column 'priority' to 'vouchers'")
    except sqlite3.OperationalError as e:
        print(f"Column 'priority' error: {e}")

    conn.commit()
    conn.close()
    print("Migration finished.")

if __name__ == "__main__":
    migrate()

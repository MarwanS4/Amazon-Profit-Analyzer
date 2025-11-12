import sqlite3

DB_FILE = "users.db"  # adjust if your database filename differs
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()

# Check if column already exists
c.execute("PRAGMA table_info(users)")
columns = [col[1] for col in c.fetchall()]

if "theme" not in columns:
    c.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
    print("✅ Added 'theme' column to users table.")
else:
    print("✔ 'theme' column already exists.")

conn.commit()
conn.close()

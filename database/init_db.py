import sqlite3

connection = sqlite3.connect("emailmind.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id INTEGER,
    sender TEXT,
    subject TEXT,
    intent TEXT,
    confidence INTEGER,
    action_taken TEXT,
    reason TEXT,
    status TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

connection.commit()
connection.close()

print("Database created successfully.")
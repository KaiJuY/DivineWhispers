import sqlite3

conn = sqlite3.connect('divine_whispers.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()

print("All tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Check if specific tables exist
tables_to_check = ['chat_sessions', 'chat_messages', 'fortune_jobs', 'chat_tasks', 'jobs']
print("\nChecking specific tables:")
for table_name in tables_to_check:
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    exists = cursor.fetchone()
    if exists:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"  [OK] {table_name}: {count} rows")
    else:
        print(f"  [NOT FOUND] {table_name}")

conn.close()

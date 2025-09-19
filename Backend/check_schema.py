import sqlite3
import os

# Check Backend ChromaDB schema
backend_db = "chroma_db/chroma.sqlite3"
root_db = "../chroma_db/chroma.sqlite3"

print("=== Backend ChromaDB Schema ===")
if os.path.exists(backend_db):
    conn = sqlite3.connect(backend_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(collections)")
    print("Collections table columns:")
    for row in cursor.fetchall():
        print(f"  {row}")
    conn.close()
else:
    print("Backend DB not found")

print("\n=== Root ChromaDB Schema ===")
if os.path.exists(root_db):
    conn = sqlite3.connect(root_db)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(collections)")
    print("Collections table columns:")
    for row in cursor.fetchall():
        print(f"  {row}")
    conn.close()
else:
    print("Root DB not found")
#!/usr/bin/env python3
"""
Add payment_method column to transactions table
"""

import sqlite3
import os
import sys

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'divine_whispers.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    sys.exit(1)

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if column already exists
    cursor.execute("PRAGMA table_info(transactions)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]

    if 'payment_method' in column_names:
        print("payment_method column already exists!")
        conn.close()
        sys.exit(0)

    # Add payment_method column
    print("Adding payment_method column to transactions table...")
    cursor.execute("""
        ALTER TABLE transactions
        ADD COLUMN payment_method VARCHAR(100) NULL
    """)

    # Commit the changes
    conn.commit()
    print("Successfully added payment_method column!")

    # Verify the column was added
    cursor.execute("PRAGMA table_info(transactions)")
    columns = cursor.fetchall()

    print("\nUpdated transactions table schema:")
    print("=" * 50)
    for col in columns:
        print(f"{col[1]} | {col[2]} | {'NOT NULL' if col[3] else 'NULL'} | {'PK' if col[5] else ''}")

    conn.close()

except Exception as e:
    print(f"Error adding column: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
    sys.exit(1)

print("\nMigration completed successfully!")
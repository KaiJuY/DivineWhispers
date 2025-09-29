#!/usr/bin/env python3
"""
Check transactions table schema to verify payment_method column exists
"""

import sqlite3
import sys
import os

# Get the database path
db_path = os.path.join(os.path.dirname(__file__), 'divine_whispers.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    sys.exit(1)

try:
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get schema for transactions table
    cursor.execute("PRAGMA table_info(transactions)")
    columns = cursor.fetchall()

    print("Transactions table schema:")
    print("=" * 50)
    for col in columns:
        print(f"{col[1]} | {col[2]} | {'NOT NULL' if col[3] else 'NULL'} | {'PK' if col[5] else ''}")

    # Check if payment_method column exists
    has_payment_method = any(col[1] == 'payment_method' for col in columns)
    print(f"\nPayment method column exists: {has_payment_method}")

    # Show recent transactions to see current data
    cursor.execute("SELECT txn_id, reference_id, description, status FROM transactions ORDER BY created_at DESC LIMIT 5")
    recent = cursor.fetchall()

    print("\nRecent transactions:")
    print("=" * 50)
    for tx in recent:
        print(f"ID: {tx[0]} | Ref: {tx[1]} | Desc: {tx[2]} | Status: {tx[3]}")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
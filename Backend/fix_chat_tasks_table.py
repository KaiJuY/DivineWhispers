#!/usr/bin/env python3
"""
Fix missing updated_at column in chat_tasks table
"""

import sqlite3
from datetime import datetime

def fix_chat_tasks_table():
    """Add missing updated_at column to chat_tasks table"""
    db_path = "divine_whispers.db"

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if updated_at column exists
        cursor.execute("PRAGMA table_info(chat_tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'updated_at' in columns:
            print("updated_at column already exists in chat_tasks table")
            return

        print("Adding updated_at column to chat_tasks table...")

        # Add updated_at column with current timestamp as default
        current_time = datetime.now().isoformat()
        cursor.execute('ALTER TABLE chat_tasks ADD COLUMN updated_at DATETIME')

        # Update existing rows to have current timestamp
        cursor.execute('UPDATE chat_tasks SET updated_at = ? WHERE updated_at IS NULL', (current_time,))

        # Commit changes
        conn.commit()

        # Verify the column was added
        cursor.execute("PRAGMA table_info(chat_tasks)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'updated_at' in columns:
            print("✓ Successfully added updated_at column to chat_tasks table")

            # Show table structure
            print("\nUpdated chat_tasks table structure:")
            cursor.execute("PRAGMA table_info(chat_tasks)")
            for row in cursor.fetchall():
                print(f"  {row[1]} {row[2]} {'NOT NULL' if row[3] else 'NULL'} {'PRIMARY KEY' if row[5] else ''}")
        else:
            print("✗ Failed to add updated_at column")

    except Exception as e:
        print(f"Error fixing chat_tasks table: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_chat_tasks_table()
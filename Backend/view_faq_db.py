#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple FAQ Database Viewer
"""

import sqlite3
import sys
import io
import os
from datetime import datetime

# Fix Unicode output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def view_database(db_path="pending_faq.db"):
    """View FAQ database contents."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== FAQ Database Viewer ===\n")
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM pending_faqs")
        total = cursor.fetchone()[0]
        print(f"📊 Total FAQ entries: {total}")
        
        # Get status counts
        cursor.execute("SELECT status, COUNT(*) FROM pending_faqs GROUP BY status")
        status_counts = cursor.fetchall()
        print("\n📈 Status breakdown:")
        for status, count in status_counts:
            print(f"   {status}: {count}")
        
        # Get category counts
        cursor.execute("SELECT category, COUNT(*) FROM pending_faqs GROUP BY category")
        category_counts = cursor.fetchall()
        print("\n🏷️  Category breakdown:")
        for category, count in category_counts:
            print(f"   {category}: {count}")
        
        # Show recent entries
        cursor.execute("""
            SELECT session_id, question, category, status, created_at 
            FROM pending_faqs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent = cursor.fetchall()
        
        print("\n📋 Recent FAQ entries:")
        print("-" * 80)
        for i, (session_id, question, category, status, created_at) in enumerate(recent, 1):
            # Truncate long questions
            display_question = question[:60] + "..." if len(question) > 60 else question
            print(f"{i:2d}. [{status:8}] {category:8} | {display_question}")
            print(f"    Session: {session_id} | Created: {created_at}")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

def view_specific_faq(session_id, db_path="pending_faq.db"):
    """View a specific FAQ by session ID with complete information."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pending_faqs WHERE session_id LIKE ?
        """, (f"%{session_id}%",))
        
        result = cursor.fetchone()
        if result:
            columns = [desc[0] for desc in cursor.description]
            print(f"\n=== FAQ Complete Details: {session_id[:8]}... ===")
            print("=" * 80)
            
            for col, val in zip(columns, result):
                if col == 'question':
                    print(f"\n📋 QUESTION:")
                    print("-" * 40)
                    print(f"{val}")
                    print()
                elif col == 'answer':
                    print(f"💬 ANSWER:")
                    print("-" * 40)
                    print(f"{val}")
                    print()
                elif col in ['approval_context']:
                    if val:
                        print(f"🔍 {col.upper()}:")
                        print("-" * 40)
                        print(f"{val}")
                        print()
                    else:
                        print(f"🔍 {col.upper()}: None\n")
                else:
                    icon = {
                        'id': '🆔', 'category': '🏷️', 'language': '🌐', 
                        'session_id': '🔑', 'created_at': '📅', 'status': '📊',
                        'approved_by': '👤', 'approved_at': '✅'
                    }.get(col, '📝')
                    print(f"{icon} {col.upper()}: {val}")
            
            print("=" * 80)
        else:
            print(f"No FAQ found with session ID containing: {session_id}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # View specific FAQ
        session_id = sys.argv[1]
        view_specific_faq(session_id)
    else:
        # View database overview
        view_database()
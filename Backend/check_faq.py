import sqlite3

conn = sqlite3.connect('divine_whispers.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM faqs')
count = cursor.fetchone()[0]
print(f'Total FAQs: {count}')

cursor.execute('SELECT id, question, category, is_published FROM faqs LIMIT 10')
print('\nSample FAQs:')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, Question: {row[1][:50]}..., Category: {row[2]}, Published: {row[3]}')

conn.close()

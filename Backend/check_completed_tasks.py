import sqlite3

conn = sqlite3.connect('divine_whispers.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM chat_tasks WHERE status = "completed"')
count = cursor.fetchone()[0]
print(f'Completed tasks: {count}')

cursor.execute('SELECT task_id, question, deity_id, response_text FROM chat_tasks WHERE status = "completed" LIMIT 5')
print('\nSample completed tasks:')
for row in cursor.fetchall():
    response_preview = row[3][:100] if row[3] else 'None'
    print(f'Task ID: {row[0]}')
    print(f'  Question: {row[1][:80]}...')
    print(f'  Deity: {row[2]}')
    print(f'  Response: {response_preview}...')
    print()

conn.close()

import sqlite3

conn = sqlite3.connect('divine_whispers.db')
cursor = conn.cursor()

# Check unique users in chat_tasks
cursor.execute('SELECT COUNT(DISTINCT user_id) FROM chat_tasks')
unique_users = cursor.fetchone()[0]
print(f'Unique users with chat tasks: {unique_users}')

# Check total chat_tasks
cursor.execute('SELECT COUNT(*) FROM chat_tasks')
total_tasks = cursor.fetchone()[0]
print(f'Total chat tasks: {total_tasks}')

# Check how many tasks per user
cursor.execute('''
    SELECT user_id, COUNT(*) as task_count
    FROM chat_tasks
    GROUP BY user_id
    ORDER BY task_count DESC
''')
print('\nTasks per user:')
for row in cursor.fetchall():
    print(f'  User {row[0]}: {row[1]} tasks')

# Check chat_sessions table
cursor.execute('SELECT COUNT(*) FROM chat_sessions')
sessions_count = cursor.fetchone()[0]
print(f'\nRows in chat_sessions table: {sessions_count}')

if sessions_count > 0:
    cursor.execute('SELECT * FROM chat_sessions LIMIT 5')
    print('Sample sessions:')
    for row in cursor.fetchall():
        print(f'  {row}')

conn.close()

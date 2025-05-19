import sqlite3
import os
from datetime import datetime

DB_PATH = "data/project_memory.sqlite"

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            status TEXT DEFAULT 'planned',
            timestamp TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS code_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_message(role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)', 
              (role, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_messages(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

def add_task(description):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO tasks (description, timestamp) VALUES (?, ?)', 
              (description, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_tasks(status=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if status:
        c.execute('SELECT id, description, status FROM tasks WHERE status = ?', (status,))
    else:
        c.execute('SELECT id, description, status FROM tasks')
    rows = c.fetchall()
    conn.close()
    return rows

def update_task(task_id, new_status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', (new_status, task_id))
    conn.commit()
    conn.close()

def save_code(label, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO code_snippets (label, content, timestamp) VALUES (?, ?, ?)', 
              (label, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

def get_code_by_label(label):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT content FROM code_snippets WHERE label = ? ORDER BY id DESC LIMIT 1', (label,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

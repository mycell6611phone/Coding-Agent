import sqlite3
import os
from datetime import datetime
import json
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
# Setup API and database paths
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"
DB_PATH = "data/project_memory.sqlite"
DB_NAME = DB_PATH  # alias for consistency

# Ensure the data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Main message log
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    # Tasks
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            status TEXT DEFAULT 'planned',
            timestamp TEXT
        )
    ''')

    # Code snippets
    c.execute('''
        CREATE TABLE IF NOT EXISTS code_snippets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT,
            content TEXT,
            timestamp TEXT
        )
    ''')

    # Embedding-based memory
    c.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            content TEXT,
            embedding TEXT,
            timestamp TEXT
        )
    ''')

    conn.commit()
    conn.close()

# --- Standard Message Save ---
def save_message(role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (role, content, timestamp) VALUES (?, ?, ?)', 
              (role, content, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# --- New: Save message with embedding ---
def save_message_with_embedding(role, content):
    embedding = client.embeddings.create(
        model=EMBED_MODEL,
        input=content
    ).data[0].embedding

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO embeddings (role, content, embedding, timestamp) VALUES (?, ?, ?, ?)",
        (role, content, json.dumps(embedding), datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

# --- Load most recent messages (basic history) ---
def get_messages(limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows[::-1]

# --- Load relevant memory using cosine similarity ---
def cosine_similarity(vec1, vec2):
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def get_relevant_messages(new_input, top_k=5):
    new_embedding = client.embeddings.create(
        model=EMBED_MODEL,
        input=new_input
    ).data[0].embedding

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role, content, embedding FROM embeddings")
    rows = c.fetchall()
    conn.close()

    scored = []
    for role, content, emb_json in rows:
        try:
            emb = json.loads(emb_json)
            similarity = cosine_similarity(new_embedding, emb)
            scored.append((similarity, role, content))
        except:
            continue

    top_matches = sorted(scored, reverse=True)[:top_k]
    return [(role, content) for _, role, content in top_matches]

# --- Tasks ---
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

# --- Code snippets ---
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

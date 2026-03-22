import sqlite3
import json
from datetime import datetime, timedelta

DB_FILE = "agent_memory.db"

def get_connection():
    """Get a database connection"""
    return sqlite3.connect(DB_FILE)

def initialize_db():
    """Create tables if they don't exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Conversation history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_name TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Search cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT,
            location TEXT,
            results TEXT,
            cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print("Database initialized")

def save_message(session_id, agent_name, role, content):
    """Save a single message to conversation history"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (session_id, agent_name, role, content)
        VALUES (?, ?, ?, ?)
    """, (session_id, agent_name, role, content))
    conn.commit()
    conn.close()

def load_conversation(session_id, agent_name):
    """Load full conversation history for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content FROM conversations
        WHERE session_id = ? AND agent_name = ?
        ORDER BY timestamp ASC
    """, (session_id, agent_name))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def get_cached_search(keywords, location, ttl_hours=24):
    """Get cached search results if still fresh"""
    conn = get_connection()
    cursor = conn.cursor()
    expiry = datetime.now() - timedelta(hours=ttl_hours)
    cursor.execute("""
        SELECT results FROM search_cache
        WHERE keywords = ? AND location = ?
        AND cached_at > ?
        ORDER BY cached_at DESC
        LIMIT 1
    """, (keywords, location, expiry))
    row = cursor.fetchone()
    conn.close()
    if row:
        print(f"Cache hit for {keywords} in {location}")
        return json.loads(row[0])
    print(f"Cache miss for {keywords} in {location}")
    return None

def save_search_cache(keywords, location, results):
    """Cache search results - one row per keyword/location"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Delete existing entry first
    cursor.execute("""
        DELETE FROM search_cache
        WHERE keywords = ? AND location = ?
    """, (keywords, location))
    
    # Insert fresh results
    cursor.execute("""
        INSERT INTO search_cache (keywords, location, results)
        VALUES (?, ?, ?)
    """, (keywords, location, json.dumps(results)))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_db()
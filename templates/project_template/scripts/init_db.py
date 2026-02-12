import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.database import DatabaseTool

def init_database():
    db = DatabaseTool()
    
    db.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS documentation (
            id SERIAL PRIMARY KEY,
            title TEXT,
            url TEXT UNIQUE,
            content TEXT,
            embedding vector(1536),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    db.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id SERIAL PRIMARY KEY,
            namespace TEXT,
            key TEXT,
            value JSONB,
            embedding vector(1536),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(namespace, key)
        )
    """)
    
    db.close()
    print("Database initialized successfully")

if __name__ == '__main__':
    init_database()
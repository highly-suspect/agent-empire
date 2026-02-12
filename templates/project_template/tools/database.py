import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

class DatabaseTool:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.getenv('DATABASE_URL')
        self.conn = None
    
    def connect(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.connection_string)
        return self.conn
    
    def execute(self, query, params=None):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute(query, params or ())
            conn.commit()
            rowcount = cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cur.close()
        return rowcount
    
    def query(self, query, params=None):
        conn = self.connect()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute(query, params or ())
            results = cur.fetchall()
        finally:
            cur.close()
        return results
    
    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None
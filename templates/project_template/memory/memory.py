import json
import os
from datetime import datetime

class Memory:
    def __init__(self, namespace='default', config=None):
        self.namespace = namespace
        self.config = config or {}
        
        base_path = self.config.get('file_path', 'knowledge/memory')
        self.storage_path = f"{base_path}/{namespace}"
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_value(self, key, value):
        """Store any value by key"""
        path = f'{self.storage_path}/{key}.json'
        with open(path, 'w') as f:
            json.dump({
                'value': value,
                'timestamp': datetime.now().isoformat()
            }, f)
    
    def load_value(self, key):
        """Retrieve any value by key"""
        path = f'{self.storage_path}/{key}.json'
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return None
    
    def list_keys(self):
        """List all stored keys in this namespace"""
        return [f.replace('.json', '') for f in os.listdir(self.storage_path)]
    
    async def retrieve_context(self, session_id, query):
        """Async interface for controller - loads conversation context"""
        return self.load_value(f"{session_id}_context")
    
    async def store_conversation(self, session_id, query, response):
        """Async interface for controller - stores conversation history"""
        self.save_value(f"{session_id}_conversation", {
            'query': query,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
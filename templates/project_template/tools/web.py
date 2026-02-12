import requests

class WebTool:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
    
    def get(self, url, timeout=10):
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    
    def close(self):
        self.session.close()
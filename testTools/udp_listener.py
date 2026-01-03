import socket

port = 9000
print(f"UDP listener started on port {port}")
print("Waiting for UDP packets...")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', port))

packet_count = 0
try:
    while True:
        data, addr = sock.recvfrom(1024)
        packet_count += 1
        print(f"[{packet_count}] Received UDP packet from {addr[0]}:{addr[1]} ({len(data)} bytes)")
except KeyboardInterrupt:
    print(f"\nTotal packets received: {packet_count}")
    sock.close()

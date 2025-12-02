# Comando y Control (C2) en Python

Este proyecto demuestra la arquitectura y el funcionamiento básico de un servidor de **Comando y Control (C2)** y un agente malicioso (implante) utilizando **Python** y el framework **Flask**. Se implementa un canal de comunicación seguro y cifrado para la gestión de tareas remotas.

---

## ¿Qué es un Servidor C2?

Un servidor de **Comando y Control (C2)** es el centro de mando de una operación de ataque o test de penetración. Su función principal es **gestionar de forma remota** las máquinas comprometidas (agentes o implantes) dentro de una red objetivo.

* **Comando:** El servidor C2 envía **instrucciones** (tareas) al agente (ej. "ejecuta este comando", "descarga este archivo").
* **Control:** El agente ejecuta la tarea y devuelve el **resultado** al servidor C2, permitiendo al operador mantener el control sobre la máquina.

Los sistemas C2 son una pieza clave en la fase final de un ataque, esencial para la **persistencia** y la **exfiltración de datos**.

---

## Componentes del Proyecto

El proyecto se compone de dos elementos principales que interactúan entre sí:

| Componente | Archivo | Descripción |
| :--- | :--- | :--- |
| **Servidor C2 (Command & Control)** | `c2.py` | Aplicación **Flask** que gestiona la comunicación, almacena las tareas pendientes y recibe los resultados de los agentes. |
| **Agente (Implante)** | `agent.py` | Script que se ejecuta en la máquina objetivo. Se comunica periódicamente con el C2 para recibir tareas y enviar los *outputs*. |

---

## Funcionamiento de la Comunicación C2

La comunicación entre el Agente y el Servidor se basa en un mecanismo de **"beaconing" (baliza)** y se mantiene **cifrada** para evadir la detección y garantizar la privacidad del canal.

### 1. Cifrado de las Comunicaciones

Para proteger los datos transmitidos (tareas y resultados), se utiliza la biblioteca `cryptography` de Python, específicamente el módulo **Fernet**, que implementa el cifrado simétrico **AES-128 en modo CBC**.

* **Clave Secreta (`SECRET_KEY`):** Se utiliza una única clave preestablecida (o generada y compartida) que tanto el servidor (`c2.py`) como el agente (`agent.py`) utilizan para cifrar y descifrar la información. El agente usa una clave fija, y el servidor genera una al inicio.
* **Función `encrypt_data/decrypt_data`:** Ambos archivos incluyen estas funciones para encapsular el cifrado y el descifrado de los *payloads* (cargas útiles) en formato JSON.

### 2. El Ciclo de Beaconing (Agente -> C2)

El agente es el que inicia la comunicación, un patrón conocido como **"pull C2"**.

1.  **Conexión Inicial y Beaconing (`/api/status`)**
    * El agente (`agent.py`) se despierta y envía una solicitud **POST** al *endpoint* `/api/status` del servidor C2.
    * El cuerpo de la solicitud es un **JSON cifrado** que contiene el **ID único del agente**.
2.  **Verificación y Envío de Tarea (C2 -> Agente)**
    * El servidor C2 (`c2.py`) descifra la información. Si el ID es nuevo, crea una entrada en el diccionario `tasks`.
    * El servidor comprueba si hay **tareas pendientes** (`tasks[agent_id]`) en su cola.
    * Si hay tareas, **extrae UNA** (utilizando `pop(0)`) y la incluye en la respuesta.
    * La respuesta completa (con o sin tarea) se **cifra** y se devuelve al agente.

### 3. Envío de Resultados (Agente -> C2)

1.  **Ejecución de Tarea**
    * El agente descifra la respuesta del C2. Si hay una tarea, la ejecuta (actualmente, solo ejecuta comandos de *shell* con `subprocess.check_output`).
2.  **Reporte de Resultados (`/api/upload`)**
    * El agente envía una solicitud **POST** al *endpoint* `/api/upload`.
    * El cuerpo es un **JSON cifrado** que contiene el **ID del agente** y el **output** (resultado de la ejecución del comando).
    * El servidor C2 descifra el resultado y lo imprime en consola.

### 4. Envío de Tarea al Agente (Operador -> C2)

El operador (usuario) utiliza el *endpoint* `/api/push` para **enviar una tarea** a la cola de un agente específico.

* El operador envía una solicitud **POST** con el `id` del agente y la `task` (diccionario) al C2.
* El C2 simplemente añade la tarea a la lista `tasks[agent_id]`, donde el agente la recogerá en su siguiente *beacon*.

---

##  Estructura del Código

### `c2.py` (Servidor)

* **`/api/status` (POST):** Recibe el *beacon* y devuelve una tarea pendiente (si existe).
* **`/api/upload` (POST):** Recibe y muestra el resultado de una tarea ejecutada por el agente.
* **`/api/push` (POST):** Permite al operador añadir una nueva tarea a la cola de un agente.
* **`/admin/agents` (GET):** Muestra una lista de los agentes conectados y sus tareas pendientes.
* **Almacenamiento:** Utiliza un diccionario global `tasks` para mantener las colas de tareas por ID de agente.

### `agent.py` (Agente)

* **ID Único:** Utiliza `uuid.uuid4()` para generar un `AGENT_ID` único en cada ejecución.
* **Loop Infinito (`while True`):** Ejecuta el ciclo de *beaconing* de forma continua.
* **Jitter:** Utiliza `time.sleep(random.randint(5, 10))` para introducir un tiempo de espera aleatorio (jitter) entre *beacons*, dificultando la detección por patrones fijos.
* **Ejecución de Comandos:** Utiliza `subprocess.check_output` con `shell=True` para ejecutar la tarea recibida.

---

##  Próximos Pasos (Cybersecurity/Ofensiva)

Este proyecto es una base excelente. En un entorno real, se podría ampliar con:

1.  **Tipos de Tareas Avanzadas:** Implementar lógica para tareas `download` (descarga), `upload` (subida de archivos), o `sleep` (cambiar el intervalo de *beaconing*).
2.  **Persistencia:** Mecanismos para asegurar que el agente se reinicie después de un *reboot*.
3.  **Comunicación Evasiva:** Usar protocolos HTTP/S que imiten tráfico legítimo (ej. peticiones a Google o redes sociales) o implementar *Domain Fronting*.
4.  **Base de Datos:** Reemplazar el diccionario `tasks` por una base de datos (SQLite, PostgreSQL) para persistencia entre reinicios del servidor C2.

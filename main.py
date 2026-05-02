"""
Codigo carro con brazo implementado en raspberry pi pico w

Autor:
Sergio Esteban Riveros Mendoza 20191005117
Julian David Gamboa Baquero 20201005187

"""

import network
import socket
import json
import time
from machine import Pin, PWM
import _thread
import ntptime
from uctypes import BF_POS, BF_LEN, UINT32, BFUINT32, struct

#----------------------------------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN RTC
#----------------------------------------------------------------------------------------------------------------------------------------------
# Offset horario Colombia (UTC -5 horas)
TIMEZONE_OFFSET = -5 * 3600

# Dirección base del RTC
RTC_BASE = 0x4005c000

# Campos del registro SETUP_0
SETUP_0_FIELDS = {
    "YEAR": 12 << BF_POS | 12 << BF_LEN | BFUINT32,
    "MONTH": 8 << BF_POS | 4 << BF_LEN | BFUINT32,
    "DAY": 0 << BF_POS | 5 << BF_LEN | BFUINT32
}

# Campos del registro SETUP_1
SETUP_1_FIELDS = {
    "DOTW": 24 << BF_POS | 3 << BF_LEN | BFUINT32,
    "HOUR": 16 << BF_POS | 5 << BF_LEN | BFUINT32,
    "MIN": 8 << BF_POS | 6 << BF_LEN | BFUINT32,
    "SEC": 0 << BF_POS | 6 << BF_LEN | BFUINT32
}

# Campos del registro CTRL
CTRL_FIELDS = {
    "FORCE_NOTLEAP_YEAR": 8 << BF_POS | 1 << BF_LEN | BFUINT32,
    "LOAD": 4 << BF_POS | 1 << BF_LEN | BFUINT32,
    "RTC_ACTIVE": 1 << BF_POS | 1 << BF_LEN | BFUINT32,
    "RTC_ENABLE": 0 << BF_POS | 1 << BF_LEN | BFUINT32
}

# Campos del registro RTC_1
RTC_1_FIELDS = {
    "YEAR": 12 << BF_POS | 12 << BF_LEN | BFUINT32,
    "MONTH": 8 << BF_POS | 4 << BF_LEN | BFUINT32,
    "DAY": 0 << BF_POS | 5 << BF_LEN | BFUINT32
}

# Campos del registro RTC_0
RTC_0_FIELDS = {
    "DOTW": 24 << BF_POS | 3 << BF_LEN | BFUINT32,
    "HOUR": 16 << BF_POS | 5 << BF_LEN | BFUINT32,
    "MIN": 8 << BF_POS | 6 << BF_LEN | BFUINT32,
    "SEC": 0 << BF_POS | 6 << BF_LEN | BFUINT32
}

# Definición de registros del RTC
RTC_REGS = {
    "SETUP_0_REG": 0x04 | UINT32,
    "SETUP_0": (0x04, SETUP_0_FIELDS),
    "SETUP_1_REG": 0x08 | UINT32,
    "SETUP_1": (0x08, SETUP_1_FIELDS),
    "CTRL_REG": 0x0c | UINT32,
    "CTRL": (0x0c, CTRL_FIELDS),
    "RTC_1_REG": 0x18 | UINT32,
    "RTC_1": (0x18, RTC_1_FIELDS),
    "RTC_0_REG": 0x1c | UINT32,
    "RTC_0": (0x1c, RTC_0_FIELDS)
}

# Instanciar la estructura del RTC
RTC_DEVICE = struct(RTC_BASE, RTC_REGS)
rtc = RTC_DEVICE

def configurar_rtc(year, month, day, dotw, hour, minute, second):
    """Configura el RTC del hardware"""
    rtc.CTRL.RTC_ENABLE = 0
    
    rtc.SETUP_0.YEAR = year
    rtc.SETUP_0.MONTH = month
    rtc.SETUP_0.DAY = day
    
    rtc.SETUP_1.DOTW = dotw
    rtc.SETUP_1.HOUR = hour
    rtc.SETUP_1.MIN = minute
    rtc.SETUP_1.SEC = second
    
    rtc.CTRL.LOAD = 1
    rtc.CTRL.RTC_ENABLE = 1

def leer_rtc():
    """Lee la fecha y hora actual del RTC"""
    sec = rtc.RTC_0.SEC
    min = rtc.RTC_0.MIN
    hour = rtc.RTC_0.HOUR
    dotw = rtc.RTC_0.DOTW
    day = rtc.RTC_1.DAY
    month = rtc.RTC_1.MONTH
    year = rtc.RTC_1.YEAR
    
    return (year, month, day, hour, min, sec, dotw)

def sincronizar_ntp():
    """Sincroniza el RTC con un servidor NTP"""
    try:
        print("🕐 Sincronizando tiempo con NTP...")
        ntptime.host = "pool.ntp.org"
        ntptime.settime()
        
        # Obtener tiempo local con offset de zona horaria
        t = time.localtime(time.time() + TIMEZONE_OFFSET)
        
        # Configurar el RTC del hardware
        configurar_rtc(t[0], t[1], t[2], t[6], t[3], t[4], t[5])
        
        print(f"✓ Tiempo sincronizado: {t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}")
        return True
    except Exception as e:
        print(f"❌ Error al sincronizar NTP: {e}")
        return False

def datetime_to_timestamp(dt_str):
    """Convierte string ISO 8601 a timestamp Unix
    Formato esperado: '2025-10-24T14:35:00Z' o '2025-10-24T14:35:00'
    La hora se interpreta como HORA LOCAL DE COLOMBIA (no UTC)
    """
    try:
        # Remover la 'Z' si existe (la ignoramos, tratamos todo como hora local)
        dt_str = dt_str.rstrip('Z')
        
        # Parsear fecha y hora
        date_part, time_part = dt_str.split('T')
        year, month, day = map(int, date_part.split('-'))
        hour, minute, second = map(int, time_part.split(':'))
        
        # Crear tupla de tiempo interpretando como hora local
        time_tuple = (year, month, day, hour, minute, second, 0, 0)
        
        # Convertir a timestamp (mktime interpreta como hora local)
        timestamp = time.mktime(time_tuple)
        
        return timestamp
    except Exception as e:
        print(f"❌ Error parseando fecha '{dt_str}': {e}")
        return None

#----------------------------------------------------------------------------------------------------------------------------------------------
# SISTEMA DE TAREAS PROGRAMADAS
#----------------------------------------------------------------------------------------------------------------------------------------------
scheduled_tasks = []
tasks_lock = _thread.allocate_lock()

def schedule_task(seq_name, time_str):
    """Programa una tarea para ejecutarse en una fecha/hora específica"""
    timestamp = datetime_to_timestamp(time_str)
    
    if timestamp is None:
        print(f"❌ Formato de fecha inválido: {time_str}")
        return False
    
    # Verificar que la fecha sea futura
    current_time = time.time()
    if timestamp <= current_time:
        print(f"⚠️  La fecha {time_str} ya pasó")
        return False
    
    with tasks_lock:
        # Verificar si ya existe una tarea con ese nombre
        for task in scheduled_tasks:
            if task["name"] == seq_name:
                print(f"⚠️  Ya existe una tarea programada para '{seq_name}'")
                return False
        
        scheduled_tasks.append({
            "name": seq_name,
            "timestamp": timestamp,
            "time_str": time_str
        })
        
        # Ordenar por timestamp
        scheduled_tasks.sort(key=lambda x: x["timestamp"])
    
    # Mostrar hora programada
    local_time = time.localtime(timestamp)
    print(f"📅 Secuencia '{seq_name}' programada para:")
    print(f"   {local_time[0]}-{local_time[1]:02d}-{local_time[2]:02d} {local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d} (hora Colombia)")
    return True

def cancel_scheduled_task(seq_name):
    """Cancela una tarea programada"""
    with tasks_lock:
        for i, task in enumerate(scheduled_tasks):
            if task["name"] == seq_name:
                scheduled_tasks.pop(i)
                print(f"🗑️  Tarea programada '{seq_name}' cancelada")
                return True
    print(f"⚠️  No se encontró tarea programada para '{seq_name}'")
    return False

def check_scheduled_tasks():
    """Verifica y ejecuta tareas programadas que ya deben ejecutarse"""
    current_time = time.time()
    tasks_to_execute = []
    
    with tasks_lock:
        # Buscar tareas que deben ejecutarse
        while scheduled_tasks and scheduled_tasks[0]["timestamp"] <= current_time:
            task = scheduled_tasks.pop(0)
            tasks_to_execute.append(task)
    
    # Ejecutar las tareas
    for task in tasks_to_execute:
        print(f"\n⏰ ¡Es hora de ejecutar '{task['name']}'!")
        execute_sequence(task["name"])

#----------------------------------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN DE SERVOS
#----------------------------------------------------------------------------------------------------------------------------------------------
FREQ = 50

SERVO_BASE = PWM(Pin(8))
SERVO_LEFT = PWM(Pin(9))
SERVO_RIGHT = PWM(Pin(10))

SERVO_BASE.freq(FREQ)
SERVO_LEFT.freq(FREQ)
SERVO_RIGHT.freq(FREQ)

def set_servo_angle(servo, angle):
    min_us = 500
    max_us = 2500
    us = min_us + (max_us - min_us) * angle / 180
    duty = int((us / 20000) * 65535)
    servo.duty_u16(duty)

#----------------------------------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN DE MOTORES DC
#----------------------------------------------------------------------------------------------------------------------------------------------
MOTOR_LEFT_PWM = Pin(4, Pin.OUT)
MOTOR_LEFT_DIR1 = Pin(2, Pin.OUT)
MOTOR_LEFT_DIR2 = Pin(3, Pin.OUT)

MOTOR_RIGHT_PWM = Pin(7, Pin.OUT)
MOTOR_RIGHT_DIR1 = Pin(5, Pin.OUT)
MOTOR_RIGHT_DIR2 = Pin(6, Pin.OUT)

left_motor_pwm = PWM(MOTOR_LEFT_PWM)
right_motor_pwm = PWM(MOTOR_RIGHT_PWM)
left_motor_pwm.freq(1000)
right_motor_pwm.freq(1000)

motor_lock = _thread.allocate_lock()
motor_timer_active = False

def set_motor(speed, forward, motor):
    """Configurar motor individual"""
    pwm_value = int((abs(speed) / 100) * 65535)
    
    if motor == 'left':
        left_motor_pwm.duty_u16(pwm_value)
        if forward:
            MOTOR_LEFT_DIR1.on()
            MOTOR_LEFT_DIR2.off()
        else:
            MOTOR_LEFT_DIR1.off()
            MOTOR_LEFT_DIR2.on()
    else:
        right_motor_pwm.duty_u16(pwm_value)
        if forward:
            MOTOR_RIGHT_DIR1.on()
            MOTOR_RIGHT_DIR2.off()
        else:
            MOTOR_RIGHT_DIR1.off()
            MOTOR_RIGHT_DIR2.on()

def control_motors(v, w):
    """Control de motores basado en velocidad lineal (v) y angular (w)"""
    with motor_lock:
        left_speed = v - w
        right_speed = v + w
        
        left_speed = max(-100, min(100, left_speed))
        right_speed = max(-100, min(100, right_speed))
        
        set_motor(abs(left_speed), left_speed >= 0, 'left')
        set_motor(abs(right_speed), right_speed >= 0, 'right')

def stop_motors():
    """Detener todos los motores"""
    with motor_lock:
        set_motor(0, True, 'left')
        set_motor(0, True, 'right')

#----------------------------------------------------------------------------------------------------------------------------------------------
# SISTEMA DE SECUENCIAS
#----------------------------------------------------------------------------------------------------------------------------------------------
sequences = {}
sequence_lock = _thread.allocate_lock()
sequence_executing = False

def apply_servo_transforms(alfa0, alfa1, alfa2):
    """Aplica las transformaciones a los ángulos de servos"""
    if alfa1 > 135:
        auxalfa1 = 25
    elif alfa1 < 10:
        auxalfa1 = 150
    else:
        auxalfa1 = (-alfa1 + 160)
    
    if alfa2 >= 0:
        auxalfa2 = 175
    elif alfa2 <= -90:
        auxalfa2 = 90
    else:
        auxalfa2 = (1.21 + 129.29)
    
    if alfa0 < -90:
        auxalfa0 = 0
    elif alfa0 > 90:
        auxalfa0 = 180
    else:
        auxalfa0 = alfa0 + 90
    
    return auxalfa0, auxalfa1, auxalfa2

def execute_state(state):
    """Ejecuta un estado individual (servos + motores)"""
    v = state.get("v", 0)
    w = state.get("w", 0)
    alfa0 = state.get("alfa0", 0)
    alfa1 = state.get("alfa1", 0)
    alfa2 = state.get("alfa2", 0)
    duration = state.get("duration", 0)
    
    auxalfa0, auxalfa1, auxalfa2 = apply_servo_transforms(alfa0, alfa1, alfa2)
    set_servo_angle(SERVO_BASE, auxalfa0)
    set_servo_angle(SERVO_RIGHT, auxalfa1)
    set_servo_angle(SERVO_LEFT, auxalfa2)
    vaux=v*10
    waux=w*10*(-1)
    
    if duration > 0:
        control_motors(vaux, waux)
        time.sleep(duration)
        stop_motors()
    else:
        if v == 0 and w == 0:
            stop_motors()
        else:
            control_motors(v, w)

def execute_sequence_thread(seq_name):
    """Thread que ejecuta una secuencia completa"""
    global sequence_executing
    
    with sequence_lock:
        if seq_name not in sequences:
            print(f"❌ Secuencia '{seq_name}' no existe")
            return
        
        if sequence_executing:
            print(f"⚠️  Ya hay una secuencia en ejecución")
            return
        
        sequence_executing = True
        states = sequences[seq_name].copy()
    
    print(f"\n{'='*50}")
    print(f"🎬 EJECUTANDO SECUENCIA: '{seq_name}'")
    print(f"   Total de estados: {len(states)}")
    print(f"{'='*50}\n")
    
    try:
        for i, state in enumerate(states, 1):
            print(f"[Estado {i}/{len(states)}]")
            execute_state(state)
            time.sleep(0.1)
        
        print(f"\n{'='*50}")
        print(f"✅ SECUENCIA COMPLETADA: '{seq_name}'")
        print(f"{'='*50}\n")
    
    except Exception as e:
        print(f"❌ Error ejecutando secuencia: {e}")
        stop_motors()
    
    finally:
        sequence_executing = False

def execute_sequence(seq_name):
    """Inicia la ejecución de una secuencia en un thread separado"""
    _thread.start_new_thread(execute_sequence_thread, (seq_name,))

#----------------------------------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN DE RED
#----------------------------------------------------------------------------------------------------------------------------------------------
WIFI_SSID = "Ejemplo"
WIFI_PASSWORD = "12345678"
BROKER_HOST = "192.168.1.101"
BROKER_PORT = 5051

TOPICS_TO_SUBSCRIBE = [
    "UDFJC/emb1/+/RPi/sequence",
    "UDFJC/emb1/robot1/RPi/sequence",
    "UDFJC/emb1/robot1/RPi/state"
]

led = Pin("LED", Pin.OUT)

def connect_wifi():
    """Conecta a la red WiFi"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        print("Ya conectado a WiFi")
        print("IP:", wlan.ifconfig()[0])
        return wlan
    
    print(f"Conectando a WiFi: {WIFI_SSID}...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    
    max_wait = 20
    while max_wait > 0:
        if wlan.isconnected():
            break
        max_wait -= 1
        print("Esperando conexión...")
        led.toggle()
        time.sleep(0.5)
    
    if wlan.isconnected():
        print("¡Conectado a WiFi!")
        status = wlan.ifconfig()
        print(f"IP: {status[0]}")
        led.on()
        return wlan
    else:
        print("Error: No se pudo conectar a WiFi")
        led.off()
        return None

class PubSubClient:
    """Cliente TCP para el broker Pub/Sub"""
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
        self.buffer = b""
        
    def connect(self):
        """Conecta al broker"""
        try:
            print(f"Conectando al broker {self.host}:{self.port}...")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0)
            self.sock.connect((self.host, self.port))
            self.sock.setblocking(False)
            self.connected = True
            print("¡Conectado al broker!")
            led.on()
            return True
        except Exception as e:
            print(f"Error al conectar: {e}")
            self.connected = False
            led.off()
            return False
    
    def disconnect(self):
        """Desconecta del broker"""
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.sock = None
        self.connected = False
        print("Desconectado del broker")
        led.off()
    
    def send_json(self, obj):
        """Envía un objeto JSON al broker"""
        if not self.connected:
            return False
        try:
            payload = json.dumps(obj) + "\n"
            self.sock.send(payload.encode("utf-8"))
            return True
        except Exception as e:
            print(f"Error al enviar: {e}")
            self.connected = False
            return False
    
    def subscribe(self, topic):
        """Se suscribe a un tópico"""
        packet = {"action": "SUB", "topic": topic}
        success = self.send_json(packet)
        if success:
            time.sleep(0.5)
        return success
    
    def publish(self, topic, data):
        """Publica datos en un tópico"""
        packet = {"action": "PUB", "topic": topic, "data": data}
        return self.send_json(packet)
    
    def check_messages(self):
        """Verifica si hay mensajes nuevos (non-blocking)"""
        if not self.connected:
            return []
        
        messages = []
        try:
            while True:
                data = self.sock.recv(1024)
                if not data:
                    self.connected = False
                    break
                
                self.buffer += data
                
                while b"\n" in self.buffer:
                    line, self.buffer = self.buffer.split(b"\n", 1)
                    if not line:
                        continue
                    
                    try:
                        text = line.decode("utf-8").strip()
                        obj = json.loads(text)
                        messages.append(obj)
                    except Exception as e:
                        print(f"Error parseando JSON: {e}")
                        
        except OSError as e:
            if e.args[0] not in (11, 115):
                self.connected = False
        except Exception as e:
            print(f"Error inesperado: {e}")
            self.connected = False
        
        return messages

#----------------------------------------------------------------------------------------------------------------------------------------------
# CALLBACKS PARA MENSAJES
#----------------------------------------------------------------------------------------------------------------------------------------------

def on_message_received(msg):
    """Callback cuando se recibe un mensaje"""
    topic = msg.get("topic", "")
    data = msg.get("data")
    status = msg.get("status")
    
    if status:
        led.toggle()
        return
    
    if "sequence" in topic and data:
        action = data.get("action")
        
        if action == "create":
            seq_data = data.get("sequence", {})
            seq_name = seq_data.get("name", "unnamed")
            states = seq_data.get("states", [])
            
            with sequence_lock:
                sequences[seq_name] = states
            
            print(f"✅ Secuencia '{seq_name}' creada con {len(states)} estados")
        
        elif action == "delete":
            seq_name = data.get("name", "")
            with sequence_lock:
                if seq_name in sequences:
                    del sequences[seq_name]
                    print(f"🗑️  Secuencia '{seq_name}' eliminada")
            
            cancel_scheduled_task(seq_name)
        
        elif action == "add_state":
            seq_name = data.get("name", "")
            new_state = data.get("state", {})
            
            with sequence_lock:
                if seq_name in sequences:
                    sequences[seq_name].append(new_state)
                    print(f"➕ Estado agregado a secuencia '{seq_name}'")
        
        elif action == "execute_now":
            seq_name = data.get("name", "")
            print(f"▶️  Solicitada ejecución inmediata de '{seq_name}'")
            execute_sequence(seq_name)
        
        elif action == "schedule":
            seq_name = data.get("name", "")
            schedule_time = data.get("time", "")
            
            print(f"📅 Solicitada programación de '{seq_name}' para {schedule_time}")
            
            with sequence_lock:
                if seq_name not in sequences:
                    print(f"❌ No se puede programar: secuencia '{seq_name}' no existe")
                    return
            
            schedule_task(seq_name, schedule_time)
        
        elif action == "cancel_schedule":
            seq_name = data.get("name", "")
            cancel_scheduled_task(seq_name)
        
        elif action == "list_scheduled":
            with tasks_lock:
                if scheduled_tasks:
                    print(f"\n📋 Tareas programadas ({len(scheduled_tasks)}):")
                    for task in scheduled_tasks:
                        print(f"   • {task['name']} → {task['time_str']}")
                else:
                    print("📋 No hay tareas programadas")
    
    elif "state" in topic and data:
        if sequence_executing:
            print("⚠️  Comando de estado ignorado: hay una secuencia en ejecución")
            return
        execute_state(data)

#----------------------------------------------------------------------------------------------------------------------------------------------
# MAIN LOOP
#----------------------------------------------------------------------------------------------------------------------------------------------

def main():
    print("\n" + "="*50)
    print("Cliente Pub/Sub - Raspberry Pi Pico W")
    print("Control de Servos y Motores DC")
    print("CON PROGRAMACIÓN DE SECUENCIAS")
    print("="*50 + "\n")
    
    stop_motors()
    
    wlan = connect_wifi()
    if not wlan:
        print("❌ No se pudo conectar a WiFi. Reiniciando en 5s...")
        time.sleep(5)
        import machine
        machine.reset()
    
    sincronizar_ntp()
    
    rtc_time = leer_rtc()
    print(f"🕐 Hora actual: {rtc_time[0]}-{rtc_time[1]:02d}-{rtc_time[2]:02d} {rtc_time[3]:02d}:{rtc_time[4]:02d}:{rtc_time[5]:02d}")
    
    client = PubSubClient(BROKER_HOST, BROKER_PORT)
    
    while not client.connect():
        print("Reintentando en 5 segundos...")
        time.sleep(5)
    
    print("\nSuscribiéndose a tópicos...")
    for topic in TOPICS_TO_SUBSCRIBE:
        print(f"  → Suscribiendo a: {topic}")
        client.subscribe(topic)
        time.sleep(0.1)
    
    print("\n✓ Cliente listo y esperando mensajes...\n")
    print("Comandos disponibles:")
    print("  - create: Crear secuencia")
    print("  - execute_now: Ejecutar secuencia inmediatamente")
    print("  - schedule: Programar secuencia para fecha/hora específica")
    print("  - cancel_schedule: Cancelar una tarea programada")
    print("  - list_scheduled: Listar tareas programadas")
    print("  - add_state: Agregar estado a secuencia")
    print("  - delete: Eliminar secuencia")
    print("\n")
    
    last_ping = time.time()
    last_ntp_sync = time.time()
    ping_interval = 30
    ntp_sync_interval = 3600
    
    try:
        while True:
            if not wlan.isconnected():
                print("❌ WiFi desconectado. Reconectando...")
                stop_motors()
                wlan = connect_wifi()
                if wlan:
                    sincronizar_ntp()
                    client.connect()
                    for topic in TOPICS_TO_SUBSCRIBE:
                        client.subscribe(topic)
                        time.sleep(0.1)
                continue
            
            if not client.connected:
                print("❌ Broker desconectado. Reconectando...")
                stop_motors()
                time.sleep(5)
                if client.connect():
                    for topic in TOPICS_TO_SUBSCRIBE:
                        client.subscribe(topic)
                        time.sleep(0.1)
                continue
            
            check_scheduled_tasks()
            
            messages = client.check_messages()
            for msg in messages:
                on_message_received(msg)
            
            now = time.time()
            if now - last_ping > ping_interval:
                with tasks_lock:
                    scheduled_info = [{"name": t["name"], "time": t["time_str"]} for t in scheduled_tasks]
                
                client.publish("UDFJC/emb1/robot1/Pico/heartbeat", {
                    "timestamp": now,
                    "status": "alive",
                    "sequences": list(sequences.keys()),
                    "executing": sequence_executing,
                    "scheduled": scheduled_info,
                    "rtc_time": "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*leer_rtc())
                })
                last_ping = now
            
            if now - last_ntp_sync > ntp_sync_interval:
                print("🔄 Re-sincronizando con NTP...")
                if sincronizar_ntp():
                    last_ntp_sync = now
            
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
    finally:
        stop_motors()
        client.disconnect()
        print("Programa terminado")


if __name__ == "__main__":
    main()
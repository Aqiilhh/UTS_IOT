import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime

# === Konfigurasi MQTT (samakan dengan Wokwi/ESP32) ===
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

TOPIK_SUHU = "iot/sensor/suhu"
TOPIK_KELEMBAPAN = "iot/sensor/kelembapan"
TOPIK_KECERAHAN = "iot/sensor/kecerahan"

# === Konfigurasi Database ===
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",        # isi jika pakai password
    database="db_sensor"
)

cursor = db.cursor()

# Buffer data sementara
current_data = {"suhu": None, "kelembapan": None, "kecerahan": None}

# === Fungsi Insert Data ===
def insert_to_db(s, k, c):
    sql = """
        INSERT INTO data_sensor (suhu, humidity, lux)
        VALUES (%s, %s, %s)
    """
    val = (s, k, c)
    cursor.execute(sql, val)
    db.commit()
    print(f"✅ Tersimpan ke DB → Suhu:{s}  Kelembapan:{k}  Kecerahan:{c}")

# === Callback MQTT ===
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("🔗 MQTT Connected!")
        client.subscribe(TOPIK_SUHU)
        client.subscribe(TOPIK_KELEMBAPAN)
        client.subscribe(TOPIK_KECERAHAN)
        print("📡 Subscribed semua topik sensor.")
    else:
        print(f"❌ MQTT Connection Failed, code: {rc}")

def on_message(client, userdata, msg):
    global current_data
    val = float(msg.payload.decode())
    
    if msg.topic == TOPIK_SUHU:
        current_data["suhu"] = val
    elif msg.topic == TOPIK_KELEMBAPAN:
        current_data["kelembapan"] = val
    elif msg.topic == TOPIK_KECERAHAN:
        current_data["kecerahan"] = val

    print(f"📥 Data diterima → {current_data}")

    # Jika semua data sudah lengkap → simpan DB
    if None not in current_data.values():
        insert_to_db(current_data["suhu"], current_data["kelembapan"], current_data["kecerahan"])
        current_data = {"suhu": None, "kelembapan": None, "kecerahan": None} # Reset buffer

# === Program Utama ===
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "Listener_DB_Store")
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Menghubungkan ke broker MQTT...")
client.connect(MQTT_BROKER, MQTT_PORT, 60)

print("🚀 Listener aktif. Tekan CTRL+C untuk berhenti.\n")
client.loop_forever()

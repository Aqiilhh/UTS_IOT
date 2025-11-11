from flask import Flask, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from decimal import Decimal
import datetime # <-- DITAMBAHKAN untuk handle timestamp

# --- Konfigurasi ---
app = Flask(__name__)
CORS(app)  # Mengizinkan akses Cross-Origin

# Ganti dengan detail koneksi database MySQL Anda
DB_CONFIG = {
    'user': 'root',
    'password': '',  # Sesuaikan password Anda (mungkin 'root' atau kosong di Laragon)
    'host': '127.0.0.1',
    'database': 'db_sensor'
}

# --- Fungsi Helper untuk Database ---
def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# --- Helper untuk mengubah Decimal ke float (untuk JSON) ---
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# --- Rute API Utama ---
@app.route('/api/sensor-stats')
def get_sensor_stats():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Tidak bisa terhubung ke database"}), 500

    cursor = conn.cursor(dictionary=True) # dictionary=True agar hasil query jadi dict
    
    try:
        # 1. Query untuk suhumax, suhumin, suhurata
        cursor.execute("SELECT MAX(suhu) as suhumax, MIN(suhu) as suhumin, AVG(suhu) as suhurata FROM data_sensor")
        stats = cursor.fetchone()

        # 2. Query untuk nilai_suhu_max_humid_max
        cursor.execute("""
            SELECT id AS id, suhu AS suhun, humidity AS humid, lux AS kecerahan, timestamp
            FROM data_sensor
            ORDER BY timestamp DESC
        """)
        nilai_max = cursor.fetchall()



        # 3. Query untuk month_year_max
        cursor.execute("""
            SELECT DISTINCT DATE_FORMAT(timestamp, '%c-%Y') as month_year
            FROM data_sensor
            WHERE suhu = (SELECT MAX(suhu) FROM data_sensor)
            OR humidity = (SELECT MAX(humidity) FROM data_sensor)
        """)
        month_year_max = cursor.fetchall()


        print("DEBUG: nilai_max =", nilai_max)


        # 4. Susun JSON output
        output_json = {
            # Handle jika DB kosong dan stats['suhurata'] adalah None
            "suhumax": stats["suhumax"],
            "suhumin": stats["suhumin"],
            "suhurata": round(stats["suhurata"], 2) if stats["suhurata"] is not None else 0,
            "nilai_suhu_max_humid_max": nilai_max,
            "month_year_max": month_year_max
        }
        
        # Perlu konversi manual timestamp ke string jika belum
        for item in output_json["nilai_suhu_max_humid_max"]:
            # Cek jika tipenya adalah objek datetime
            if isinstance(item["timestamp"], datetime.datetime):
                item["timestamp"] = item["timestamp"].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(output_json)

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- Rute untuk Parsing (Frontend) ---
@app.route('/')
def index():
    # Menampilkan halaman HTML untuk parsing
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
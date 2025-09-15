# app.py
from flask import Flask, jsonify, request
from conexion import get_connection
from mysql.connector import Error

app = Flask(__name__)

@app.route("/")
def home():
    return "Flask + MySQL OK. Visita /test_db"

@app.route("/test_db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"ok": True, "msg": "Conexión a MySQL exitosa"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Ruta para crear tabla usuarios (id_usuario, nombre, mail)
@app.route("/init_db/usuarios", methods=["POST"])
def init_usuarios():
    sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INT AUTO_INCREMENT PRIMARY KEY,
        nombre     VARCHAR(100) NOT NULL,
        mail       VARCHAR(150) NOT NULL UNIQUE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        conn.close()
        return jsonify({"ok": True, "msg": "Tabla 'usuarios' lista"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Insertar usuario (POST JSON: {"nombre":"...", "mail":"..."})
@app.route("/usuarios", methods=["POST"])
def add_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    mail = data.get("mail")
    if not nombre or not mail:
        return jsonify({"ok": False, "error": "nombre y mail requeridos"}), 400

    sql = "INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, (nombre, mail))
        cur.close()
        conn.close()
        return jsonify({"ok": True, "msg": "Usuario creado"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# Listar usuarios
@app.route("/usuarios", methods=["GET"])
def list_usuarios():
    sql = "SELECT id_usuario, nombre, mail FROM usuarios ORDER BY id_usuario DESC"
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"ok": True, "data": rows})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
# app.py (agrega debajo de tus otras rutas)
from flask import Flask, jsonify, request
from conexion import get_connection  # <- o from conexion.conexion import get_connection
from mysql.connector import Error

app = Flask(__name__)

# 1) Crear tabla usuarios
@app.route("/init_db/usuarios", methods=["POST"])
def init_usuarios():
    sql = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INT AUTO_INCREMENT PRIMARY KEY,
        nombre     VARCHAR(100) NOT NULL,
        mail       VARCHAR(150) NOT NULL UNIQUE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        cur.close(); conn.close()
        return {"ok": True, "msg": "Tabla 'usuarios' lista"}
    except Error as e:
        return {"ok": False, "error": str(e)}, 500

# 2) Insertar usuario
@app.route("/usuarios", methods=["POST"])
def add_usuario():
    data = request.get_json(force=True)
    nombre = data.get("nombre")
    mail   = data.get("mail")
    if not nombre or not mail:
        return {"ok": False, "error": "nombre y mail requeridos"}, 400
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)", (nombre, mail))
        cur.close(); conn.close()
        return {"ok": True, "msg": "Usuario creado"}
    except Error as e:
        return {"ok": False, "error": str(e)}, 500

# 3) Listar usuarios
@app.route("/usuarios", methods=["GET"])
def list_usuarios():
    try:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_usuario, nombre, mail FROM usuarios ORDER BY id_usuario DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return {"ok": True, "data": rows}
    except Error as e:
        return {"ok": False, "error": str(e)}, 500

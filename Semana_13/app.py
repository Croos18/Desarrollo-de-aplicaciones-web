# app.py
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from mysql.connector import Error
from conexion import get_connection  # asegúrate de apuntar a la BD correcta

app = Flask(__name__)
app.secret_key = "cambia-esta-clave"

# ------------------ HOME ------------------
@app.route("/")
def home():
    # Página de inicio: redirige al listado web
    return redirect(url_for("listar_productos"))

# ------------------ SALUD / DB ------------------
@app.route("/test_db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close(); conn.close()
        return jsonify({"ok": True, "msg": "Conexión a MySQL exitosa"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ------------------ INIT DB (usuarios, productos) ------------------
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
        conn = get_connection(); cur = conn.cursor()
        cur.execute(sql); conn.commit()
        cur.close(); conn.close()
        return jsonify({"ok": True, "msg": "Tabla 'usuarios' lista"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/init_db/productos", methods=["POST"])
def init_productos():
    sql = """
    CREATE TABLE IF NOT EXISTS productos (
      id_producto INT AUTO_INCREMENT PRIMARY KEY,
      nombre      VARCHAR(120) NOT NULL,
      precio      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
      stock       INT NOT NULL DEFAULT 0,
      created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute(sql); conn.commit()
        cur.close(); conn.close()
        return jsonify({"ok": True, "msg": "Tabla 'productos' lista"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ------------------ API USUARIOS (lo tuyo) ------------------
@app.route("/usuarios", methods=["POST"])
def add_usuario():
    data = request.get_json(force=True) or {}
    nombre = data.get("nombre"); mail = data.get("mail")
    if not nombre or not mail:
        return jsonify({"ok": False, "error": "nombre y mail requeridos"}), 400
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (nombre, mail) VALUES (%s, %s)", (nombre, mail))
        conn.commit(); new_id = cur.lastrowid
        cur.close(); conn.close()
        return jsonify({"ok": True, "msg": "Usuario creado", "id_usuario": new_id}), 201
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/usuarios", methods=["GET"])
def list_usuarios():
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_usuario, nombre, mail FROM usuarios ORDER BY id_usuario DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
        return jsonify({"ok": True, "data": rows})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# ------------------ WEB CRUD PRODUCTOS ------------------
# LISTAR
@app.get("/productos")
def listar_productos():
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_producto, nombre, precio, stock, created_at FROM productos ORDER BY id_producto DESC")
        rows = cur.fetchall()
        cur.close(); conn.close()
    except Error as e:
        flash(f"Error al listar: {e}", "danger")
        rows = []
    return render_template("productos_list.html", productos=rows)

# FORM CREAR
@app.get("/crear")
def crear_form():
    return render_template("producto_form.html", producto=None, action="crear")

# CREAR (POST)
@app.post("/crear")
def crear_submit():
    nombre = (request.form.get("nombre") or "").strip()
    precio = request.form.get("precio") or "0"
    stock  = request.form.get("stock")  or "0"

    errores = []
    if not nombre: errores.append("El nombre es obligatorio.")
    try:
        precio = float(precio);  assert precio >= 0
    except Exception: errores.append("Precio inválido.")
    try:
        stock = int(stock);      assert stock >= 0
    except Exception: errores.append("Stock inválido.")

    if errores:
        for e in errores: flash(e, "warning")
        return render_template("producto_form.html", producto=request.form, action="crear")

    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO productos (nombre, precio, stock) VALUES (%s, %s, %s)", (nombre, precio, stock))
        conn.commit(); cur.close(); conn.close()
        flash("Producto creado.", "success")
        return redirect(url_for("listar_productos"))
    except Error as e:
        flash(f"Error al crear: {e}", "danger")
        return render_template("producto_form.html", producto=request.form, action="crear")

# FORM EDITAR
@app.get("/editar/<int:id_prod>")
def editar_form(id_prod):
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM productos WHERE id_producto=%s", (id_prod,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            flash("Producto no encontrado.", "warning")
            return redirect(url_for("listar_productos"))
        return render_template("producto_form.html", producto=row, action="editar")
    except Error as e:
        flash(f"Error al cargar edición: {e}", "danger")
        return redirect(url_for("listar_productos"))

# EDITAR (POST)
@app.post("/editar/<int:id_prod>")
def editar_submit(id_prod):
    nombre = (request.form.get("nombre") or "").strip()
    precio = request.form.get("precio") or "0"
    stock  = request.form.get("stock")  or "0"

    errores = []
    if not nombre: errores.append("El nombre es obligatorio.")
    try:
        precio = float(precio);  assert precio >= 0
    except Exception: errores.append("Precio inválido.")
    try:
        stock = int(stock);      assert stock >= 0
    except Exception: errores.append("Stock inválido.")

    if errores:
        for e in errores: flash(e, "warning")
        data = {"id_producto": id_prod, "nombre": nombre, "precio": precio, "stock": stock}
        return render_template("producto_form.html", producto=data, action="editar")

    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("UPDATE productos SET nombre=%s, precio=%s, stock=%s WHERE id_producto=%s",
                    (nombre, precio, stock, id_prod))
        conn.commit(); cur.close(); conn.close()
        flash("Producto actualizado.", "success")
        return redirect(url_for("listar_productos"))
    except Error as e:
        flash(f"Error al actualizar: {e}", "danger")
        data = {"id_producto": id_prod, "nombre": nombre, "precio": precio, "stock": stock}
        return render_template("producto_form.html", producto=data, action="editar")

# CONFIRMAR ELIMINAR
@app.get("/eliminar/<int:id_prod>")
def eliminar_confirm(id_prod):
    try:
        conn = get_connection(); cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id_producto, nombre FROM productos WHERE id_producto=%s", (id_prod,))
        row = cur.fetchone()
        cur.close(); conn.close()
        if not row:
            flash("Producto no encontrado.", "warning")
            return redirect(url_for("listar_productos"))
        return render_template("confirm_delete.html", producto=row)
    except Error as e:
        flash(f"Error: {e}", "danger")
        return redirect(url_for("listar_productos"))

# ELIMINAR (POST)
@app.post("/eliminar/<int:id_prod>")
def eliminar_do(id_prod):
    try:
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM productos WHERE id_producto=%s", (id_prod,))
        conn.commit(); cur.close(); conn.close()
        flash("Producto eliminado.", "success")
    except Error as e:
        flash(f"Error al eliminar: {e}", "danger")
    return redirect(url_for("listar_productos"))

# Sonda
@app.get("/ping")
def ping():
    return "pong"

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

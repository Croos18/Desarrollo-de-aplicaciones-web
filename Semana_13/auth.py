# auth.py (REEMPLAZO COMPLETO)

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user
from conexion import get_connection
from models import User  # si no tiene from_row, hay un fallback más abajo

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ---------- Utilidades de esquema dinámico ----------

def _pick(cols: set, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in cols:
            return c
    return None


def _colmap(conn):
    """Detecta nombres reales en tu tabla `usuarios`."""
    cur = conn.cursor(dictionary=True)
    cur.execute("SHOW COLUMNS FROM usuarios")
    cols = {row["Field"] for row in cur.fetchall()}
    cur.close()
    return {
        "id":   _pick(cols, ["id", "id_usuario", "usuario_id", "idUsuario", "user_id", "idUser"]),
        "user": _pick(cols, ["username", "usuario", "user", "login", "mail", "email", "correo", "correo_electronico"]),
        "pass": _pick(cols, ["password_hash", "password", "contrasena", "contrasenia", "clave", "pass", "pwd", "pswd"]),
        "name": _pick(cols, ["nombre", "nombres", "name", "full_name"]),
        "all":  cols,
    }


def _ensure_password_col(conn, m):
    """Si no existe columna de contraseña, la crea (password_hash VARCHAR(255))."""
    if m["pass"]:
        return m
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255) NULL")
        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        cur.close()
    return _colmap(conn)


# ---------- Consultas ----------

def get_user_by_username(username: str):
    conn = get_connection()
    try:
        m = _colmap(conn)
        m = _ensure_password_col(conn, m)
        if not m["user"] or not m["pass"] or not m["id"]:
            return None

        cur = conn.cursor(dictionary=True)
        sql = f"""
            SELECT
                {m['id']}   AS id,
                {m['user']} AS username,
                {m['pass']} AS password_hash,
                {m['name']} AS nombre
            FROM usuarios
            WHERE {m['user']}=%s
            LIMIT 1
        """
        cur.execute(sql, (username,))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()


# ---------- Rutas ----------

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        row = get_user_by_username(username)

        valid = False
        if row:
            # Si guarda hash -> check_password_hash; si no, comparar plano
            try:
                valid = check_password_hash(row["password_hash"], password)
            except Exception:
                valid = (row["password_hash"] == password)

        if not row or not valid:
            flash("Usuario o contraseña incorrectos.", "danger")
            return render_template("auth/login.html", username=username), 401

        # Login con Flask-Login
        try:
            user = User.from_row(row)  # tu clase puede tener este helper
        except Exception:
            # Fallback mínimo si no existe from_row o firma distinta
            class _U:
                def __init__(self, id, username):
                    self.id = id
                    self.username = username
                    self.is_authenticated = True
                    self.is_active = True
                    self.is_anonymous = False
                def get_id(self):
                    return str(self.id)
            user = _U(row["id"], row["username"])

        login_user(user)
        # También dejamos algunos datos en sesión para plantillas simples
        session["user_id"] = row["id"]
        session["username"] = row["username"]

        next_url = request.args.get("next")
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return redirect(next_url)
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        nombre   = (request.form.get("nombre") or "").strip()
        p1       = request.form.get("password") or ""
        p2       = request.form.get("password2") or ""

        if not username or not p1:
            flash("Usuario y contraseña son obligatorios.", "warning")
            return render_template("auth/register.html", username=username, nombre=nombre)
        if p1 != p2:
            flash("Las contraseñas no coinciden.", "warning")
            return render_template("auth/register.html", username=username, nombre=nombre)
        if len(p1) < 4:
            flash("La contraseña debe tener al menos 4 caracteres.", "warning")
            return render_template("auth/register.html", username=username, nombre=nombre)

        conn = get_connection()
        try:
            m = _colmap(conn)
            m = _ensure_password_col(conn, m)
            if not m["user"] or not m["pass"]:
                cols_txt = ", ".join(sorted(m["all"])) if m["all"] else "(sin columnas)"
                flash(f"La tabla 'usuarios' no tiene columnas compatibles. Detectadas: {cols_txt}.", "danger")
                return render_template("auth/register.html", username=username, nombre=nombre)

            cur = conn.cursor(dictionary=True)

            # ¿Ya existe el usuario/correo?
            cur.execute(f"SELECT {m['user']} FROM usuarios WHERE {m['user']}=%s LIMIT 1", (username,))
            if cur.fetchone():
                cur.close()
                flash("Ese usuario ya existe.", "warning")
                return render_template("auth/register.html", username=username, nombre=nombre)

            # Insertar usuario
            hashed = generate_password_hash(p1)
            if m["name"]:
                cur.execute(
                    f"INSERT INTO usuarios ({m['user']}, {m['pass']}, {m['name']}) VALUES (%s, %s, %s)",
                    (username, hashed, nombre or None)
                )
            else:
                cur.execute(
                    f"INSERT INTO usuarios ({m['user']}, {m['pass']}) VALUES (%s, %s)",
                    (username, hashed)
                )
            conn.commit()
            cur.close()

            flash("Registro exitoso. Ya puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))

        except Exception:
            conn.rollback()
            flash("No se pudo registrar (revisa permisos o longitud de columnas).", "danger")
            return render_template("auth/register.html", username=username, nombre=nombre)
        finally:
            conn.close()

    return render_template("auth/register.html")

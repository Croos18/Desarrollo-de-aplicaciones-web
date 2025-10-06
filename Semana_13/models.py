# models.py (REEMPLAZO COMPLETO)
from flask_login import UserMixin
from conexion import get_connection

# ---------- Utilidades de mapeo ----------
def _pick(cols: set, candidates: list[str]):
    for c in candidates:
        if c in cols:
            return c
    return None

def _colmap_usuarios(conn):
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

# ---------- Modelo de sesión ----------
class User(UserMixin):
    def __init__(self, id, username, nombre=None):
        # ¡OJO! NO asignamos self.is_active (UserMixin ya lo provee)
        self.id = str(id)          # Flask-Login espera string en get_id()
        self.username = username
        self.nombre = nombre

    @classmethod
    def from_row(cls, row: dict):
        # row debe venir aliaseado como id, username, nombre
        return cls(row["id"], row.get("username"), row.get("nombre"))

# ---------- Consultas usadas por LoginManager ----------
def get_user_public_by_id(user_id):
    """
    Devuelve el usuario con alias estándar (id, username, nombre)
    sin importar cómo se llamen realmente las columnas.
    """
    conn = get_connection()
    try:
        m = _colmap_usuarios(conn)
        if not m["id"] or not m["user"]:
            return None
        cur = conn.cursor(dictionary=True)
        sql = f"""
            SELECT
                {m['id']}   AS id,
                {m['user']} AS username,
                {m['name']} AS nombre
            FROM usuarios
            WHERE {m['id']}=%s
            LIMIT 1
        """
        cur.execute(sql, (user_id,))
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()

def get_user_public_by_username(username):
    """
    Útil si en algún lugar necesitas buscar por username/correo.
    También devuelve alias: id, username, nombre.
    """
    conn = get_connection()
    try:
        m = _colmap_usuarios(conn)
        if not m["id"] or not m["user"]:
            return None
        cur = conn.cursor(dictionary=True)
        sql = f"""
            SELECT
                {m['id']}   AS id,
                {m['user']} AS username,
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

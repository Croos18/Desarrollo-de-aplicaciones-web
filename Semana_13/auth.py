from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from db import get_conn
from models import User

auth_bp = Blueprint("auth", __name__)

def find_user_by_email(email):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id_usuario"],
            nombre=row["nombre"],
            email=row["email"],
            password_hash=row["password_hash"],
        )
    finally:
        conn.close()

def find_user_by_id(uid: int):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id_usuario=%s", (uid,))
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id_usuario"],
            nombre=row["nombre"],
            email=row["email"],
            password_hash=row["password_hash"],
        )
    finally:
        conn.close()

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email  = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not nombre or not email or not password:
            flash("Todos los campos son obligatorios", "danger")
            return render_template("register.html")

        if find_user_by_email(email):
            flash("Ese email ya está registrado", "warning")
            return render_template("register.html")

        phash = generate_password_hash(password)
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO usuarios (nombre, email, password_hash) VALUES (%s, %s, %s)",
                (nombre, email, phash),
            )
            conn.commit()
            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("auth.login"))
        finally:
            conn.close()

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email)
        if not user or not check_password_hash(user.password_hash, password):
            flash("Credenciales inválidas", "danger")
            return render_template("login.html")
        login_user(user)
        flash("¡Bienvenido!", "success")
        return redirect(url_for("index"))
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada", "info")
    return redirect(url_for("auth.login"))

# Exponer helper para app.py (user_loader)
get_user_by_id = find_user_by_id

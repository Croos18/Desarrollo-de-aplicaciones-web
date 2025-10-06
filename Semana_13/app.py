from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from mysql.connector import Error
from conexion import get_connection
from flask_login import LoginManager, login_required
from models import User, get_user_public_by_id
from auth import auth_bp

# -----------------------------------------------------
# App y Login Manager
# -----------------------------------------------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config.update(SECRET_KEY="cambia-esta-clave")

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    row = get_user_public_by_id(user_id)
    return User.from_row(row) if row else None

# Blueprint de auth
app.register_blueprint(auth_bp, url_prefix="/auth")

# -----------------------------------------------------
# Helpers de mapeo / existencia de tablas
# -----------------------------------------------------
def _pick(cols: set, candidates: list[str]):
    for c in candidates:
        if c in cols:
            return c
    return None

def _table_exists(conn, table: str) -> bool:
    cur = None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s",
            (table,)
        )
        return cur.fetchone()[0] == 1
    finally:
        if cur: cur.close()

def _cols_for_table(conn, table: str) -> set:
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SHOW COLUMNS FROM {table}")
        return {row["Field"] for row in cur.fetchall()}
    finally:
        if cur: cur.close()

# ---- Mapas (categorias / productos) ----
def map_categorias(conn):
    cols = _cols_for_table(conn, "categorias")
    return {
        "id": _pick(cols, ["id", "id_categoria", "categoria_id", "idCategoria"]),
        "nombre": _pick(cols, ["nombre", "name", "titulo"]),
        "descripcion": _pick(cols, ["descripcion", "description", "detalle"]),
        "all": cols
    }

def map_productos(conn):
    cols = _cols_for_table(conn, "productos")
    return {
        "id": _pick(cols, ["id", "id_producto", "producto_id", "idProducto"]),
        "nombre": _pick(cols, ["nombre", "name", "titulo"]),
        "precio": _pick(cols, ["precio", "price", "monto", "costo"]),
        "stock": _pick(cols, ["stock", "existencias", "cantidad"]),
        # FK opcional a categorías si tu tabla la tuviera en el futuro
        "cat_fk": _pick(cols, ["categoria_id", "id_categoria", "category_id", "categoria", "categoriaId"]),
        "all": cols
    }

# ---- Mapas (proyectos / tareas) ----
def map_proyectos(conn):
    cols = _cols_for_table(conn, "proyectos")
    return {
        "id": _pick(cols, ["id", "id_proyecto", "proyecto_id", "idProyecto"]),
        "nombre": _pick(cols, ["nombre", "name", "titulo"]),
        "descripcion": _pick(cols, ["descripcion", "description", "detalle"]),
        "creado": _pick(cols, ["creado_en", "created_at", "created"]),
        "all": cols
    }

def map_tareas(conn):
    cols = _cols_for_table(conn, "tareas")
    return {
        "id": _pick(cols, ["id", "id_tarea", "tarea_id", "idTarea"]),
        "proy_fk": _pick(cols, ["id_proyecto", "proyecto_id", "idProyecto"]),
        "titulo": _pick(cols, ["titulo", "title", "nombre"]),
        "estado": _pick(cols, ["estado", "status"]),
        "asignado": _pick(cols, ["asignado_a", "asignado", "responsable"]),
        "creado": _pick(cols, ["creado_en", "created_at", "created"]),
        "all": cols
    }

# -----------------------------------------------------
# HOME + SALUD
# -----------------------------------------------------
@app.route("/")
def home():
    return redirect(url_for("listar_proyectos"))

@app.route("/test_db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close(); conn.close()
        return jsonify({"ok": True, "msg": "Conexión a MySQL OK"})
    except Error as e:
        return jsonify({"ok": False, "error": str(e)}), 500

# =====================================================
# ============= CATEGORIAS (CRUD COMPLETO) ============
# =====================================================
@app.route("/categorias")
@login_required
def listar_categorias():
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "categorias"):
            flash("La tabla 'categorias' no existe.", "warning")
            return render_template("categorias/list.html", categorias=[])
        m = map_categorias(conn)
        if not m["id"] or not m["nombre"]:
            flash("La tabla 'categorias' no tiene columnas compatibles.", "danger")
            return render_template("categorias/list.html", categorias=[])
        cur = conn.cursor(dictionary=True)
        desc_sql = f", {m['descripcion']} AS descripcion" if m["descripcion"] else ", NULL AS descripcion"
        cur.execute(f"""
            SELECT {m['id']} AS id, {m['nombre']} AS nombre{desc_sql}
            FROM categorias
            ORDER BY {m['nombre']}
        """)
        categorias = cur.fetchall()
        return render_template("categorias/list.html", categorias=categorias)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/categorias/crear", methods=["GET","POST"])
@login_required
def crear_categoria():
    if request.method == "POST":
        conn = get_connection()
        cur = None
        try:
            if not _table_exists(conn, "categorias"):
                flash("La tabla 'categorias' no existe.", "danger")
                return render_template("categorias/form.html", categoria=None)
            m = map_categorias(conn)
            nombre = (request.form.get("nombre") or "").strip()
            descripcion = (request.form.get("descripcion") or "").strip()
            if not nombre:
                flash("El nombre es obligatorio.", "warning")
                return render_template("categorias/form.html", categoria=None)
            cur = conn.cursor()
            if m["descripcion"]:
                cur.execute(
                    f"INSERT INTO categorias ({m['nombre']}, {m['descripcion']}) VALUES (%s,%s)",
                    (nombre, descripcion or None)
                )
            else:
                cur.execute(f"INSERT INTO categorias ({m['nombre']}) VALUES (%s)", (nombre,))
            conn.commit()
            flash("Categoría creada.", "success")
            return redirect(url_for("listar_categorias"))
        except Exception:
            conn.rollback()
            flash("No se pudo crear la categoría.", "danger")
            return render_template("categorias/form.html", categoria=None)
        finally:
            if cur: cur.close()
            conn.close()
    return render_template("categorias/form.html", categoria=None)

@app.route("/categorias/editar/<int:cat_id>", methods=["GET","POST"])
@login_required
def editar_categoria(cat_id):
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "categorias"):
            flash("La tabla 'categorias' no existe.", "danger")
            return redirect(url_for("listar_categorias"))
        m = map_categorias(conn)
        if request.method == "POST":
            nombre = (request.form.get("nombre") or "").strip()
            descripcion = (request.form.get("descripcion") or "").strip()
            if not nombre:
                flash("El nombre es obligatorio.", "warning")
            else:
                cur = conn.cursor()
                try:
                    if m["descripcion"]:
                        cur.execute(
                            f"UPDATE categorias SET {m['nombre']}=%s, {m['descripcion']}=%s WHERE {m['id']}=%s",
                            (nombre, descripcion or None, cat_id)
                        )
                    else:
                        cur.execute(
                            f"UPDATE categorias SET {m['nombre']}=%s WHERE {m['id']}=%s",
                            (nombre, cat_id)
                        )
                    conn.commit()
                    flash("Categoría actualizada.", "success")
                    return redirect(url_for("listar_categorias"))
                except Exception:
                    conn.rollback()
                    flash("No se pudo actualizar la categoría.", "danger")
                finally:
                    if cur: cur.close(); cur = None
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"SELECT {m['id']} AS id, {m['nombre']} AS nombre"
            + (f", {m['descripcion']} AS descripcion" if m['descripcion'] else ", NULL AS descripcion")
            + f" FROM categorias WHERE {m['id']}=%s",
            (cat_id,)
        )
        categoria = cur.fetchone()
        return render_template("categorias/form.html", categoria=categoria)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/categorias/eliminar/<int:cat_id>", methods=["GET","POST"])
@login_required
def eliminar_categoria(cat_id):
    if request.method == "POST":
        conn = get_connection()
        cur = None
        try:
            if not _table_exists(conn, "categorias"):
                flash("La tabla 'categorias' no existe.", "danger")
                return redirect(url_for("listar_categorias"))
            m = map_categorias(conn)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM categorias WHERE {m['id']}=%s", (cat_id,))
            conn.commit()
            flash("Categoría eliminada.", "info")
            return redirect(url_for("listar_categorias"))
        except Exception:
            conn.rollback()
            flash("No se pudo eliminar (puede tener productos).", "danger")
            return redirect(url_for("listar_categorias"))
        finally:
            if cur: cur.close()
            conn.close()

    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "categorias"):
            flash("La tabla 'categorias' no existe.", "danger")
            return redirect(url_for("listar_categorias"))
        m = map_categorias(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute(
            f"SELECT {m['id']} AS id, {m['nombre']} AS nombre"
            + (f", {m['descripcion']} AS descripcion" if m['descripcion'] else ", NULL AS descripcion")
            + f" FROM categorias WHERE {m['id']}=%s",
            (cat_id,)
        )
        categoria = cur.fetchone()
        return render_template("categorias/confirm_delete.html", categoria=categoria)
    finally:
        if cur: cur.close()
        conn.close()

# =====================================================
# ===============   PROYECTOS (CRUD)   ================
# =====================================================
@app.route("/proyectos")
@login_required
def listar_proyectos():
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "proyectos"):
            flash("La tabla 'proyectos' no existe.", "danger")
            return render_template("proyectos/list.html", proyectos=[])
        mp = map_proyectos(conn)
        cur = conn.cursor(dictionary=True)
        parts = [f"{mp['id']} AS id", f"{mp['nombre']} AS nombre"]
        parts.append(f"{mp['descripcion']} AS descripcion" if mp["descripcion"] else "NULL AS descripcion")
        parts.append(f"{mp['creado']} AS creado_en" if mp["creado"] else "NULL AS creado_en")
        cur.execute(f"SELECT {', '.join(parts)} FROM proyectos ORDER BY {mp['id']} DESC")
        proyectos = cur.fetchall()
        return render_template("proyectos/list.html", proyectos=proyectos)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/proyectos/crear", methods=["GET", "POST"])
@login_required
def crear_proyecto():
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "warning")
            return render_template("proyectos/form.html", proyecto=None)
        conn = get_connection()
        cur = None
        try:
            mp = map_proyectos(conn)
            cur = conn.cursor()
            cols = [mp["nombre"]]; vals = [nombre]
            if mp["descripcion"]:
                cols.append(mp["descripcion"]); vals.append(descripcion or None)
            placeholders = ",".join(["%s"] * len(vals))
            cur.execute(f"INSERT INTO proyectos ({', '.join(cols)}) VALUES ({placeholders})", tuple(vals))
            conn.commit()
            flash("Proyecto creado.", "success")
            return redirect(url_for("listar_proyectos"))
        except Exception:
            conn.rollback()
            flash("No se pudo crear el proyecto.", "danger")
            return render_template("proyectos/form.html", proyecto=None)
        finally:
            if cur: cur.close()
            conn.close()
    return render_template("proyectos/form.html", proyecto=None)

@app.route("/proyectos/editar/<int:proy_id>", methods=["GET", "POST"])
@login_required
def editar_proyecto(proy_id):
    conn = get_connection()
    cur = None
    try:
        mp = map_proyectos(conn)
        if request.method == "POST":
            nombre = (request.form.get("nombre") or "").strip()
            descripcion = (request.form.get("descripcion") or "").strip()
            if not nombre:
                flash("El nombre es obligatorio.", "warning")
            else:
                cur = conn.cursor()
                sets, vals = [f"{mp['nombre']}=%s"], [nombre]
                if mp["descripcion"]:
                    sets.append(f"{mp['descripcion']}=%s"); vals.append(descripcion or None)
                vals.append(proy_id)
                try:
                    cur.execute(f"UPDATE proyectos SET {', '.join(sets)} WHERE {mp['id']}=%s", tuple(vals))
                    conn.commit()
                    flash("Proyecto actualizado.", "success")
                    return redirect(url_for("listar_proyectos"))
                except Exception:
                    conn.rollback()
                    flash("No se pudo actualizar el proyecto.", "danger")
                finally:
                    if cur: cur.close(); cur = None

        cur = conn.cursor(dictionary=True)
        cols = [f"{mp['id']} AS id", f"{mp['nombre']} AS nombre"]
        cols.append(f"{mp['descripcion']} AS descripcion" if mp["descripcion"] else "NULL AS descripcion")
        cur.execute(f"SELECT {', '.join(cols)} FROM proyectos WHERE {mp['id']}=%s", (proy_id,))
        proyecto = cur.fetchone()
        return render_template("proyectos/form.html", proyecto=proyecto)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/proyectos/eliminar/<int:proy_id>", methods=["GET", "POST"])
@login_required
def eliminar_proyecto(proy_id):
    if request.method == "POST":
        conn = get_connection()
        cur = None
        try:
            mp = map_proyectos(conn)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM proyectos WHERE {mp['id']}=%s", (proy_id,))
            conn.commit()
            flash("Proyecto eliminado.", "info")
            return redirect(url_for("listar_proyectos"))
        except Exception:
            conn.rollback()
            flash("No se pudo eliminar el proyecto (puede tener tareas).", "danger")
            return redirect(url_for("listar_proyectos"))
        finally:
            if cur: cur.close()
            conn.close()

    conn = get_connection()
    cur = None
    try:
        mp = map_proyectos(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT {mp['id']} AS id, {mp['nombre']} AS nombre FROM proyectos WHERE {mp['id']}=%s", (proy_id,))
        proyecto = cur.fetchone()
        return render_template("proyectos/confirm_delete.html", proyecto=proyecto)
    finally:
        if cur: cur.close()
        conn.close()

# =====================================================
# ==================  TAREAS (CRUD)  ==================
# =====================================================
def _fetch_proyectos(conn):
    if not _table_exists(conn, "proyectos"):
        return []
    mp = map_proyectos(conn)
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT {mp['id']} AS id, {mp['nombre']} AS nombre FROM proyectos ORDER BY {mp['nombre']}")
    rows = cur.fetchall()
    cur.close()
    return rows

@app.route("/tareas")
@login_required
def listar_tareas():
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "tareas"):
            flash("La tabla 'tareas' no existe.", "danger")
            return render_template("tareas/list.html", tareas=[])
        mt = map_tareas(conn)
        can_join = _table_exists(conn, "proyectos")
        mp = map_proyectos(conn) if can_join else None
        cur = conn.cursor(dictionary=True)
        if can_join and mp["id"] and mp["nombre"]:
            cur.execute(f"""
                SELECT
                    t.{mt['id']}       AS id,
                    t.{mt['titulo']}   AS titulo,
                    t.{mt['estado']}   AS estado,
                    t.{mt['asignado']} AS asignado_a,
                    {f"t.{mt['creado']} AS creado_en," if mt['creado'] else "NULL AS creado_en,"}
                    p.{mp['nombre']}   AS proyecto
                FROM tareas t
                LEFT JOIN proyectos p ON p.{mp['id']} = t.{mt['proy_fk']}
                ORDER BY t.{mt['id']} DESC
            """)
        else:
            cur.execute(f"""
                SELECT
                    t.{mt['id']}       AS id,
                    t.{mt['titulo']}   AS titulo,
                    t.{mt['estado']}   AS estado,
                    t.{mt['asignado']} AS asignado_a,
                    {f"t.{mt['creado']} AS creado_en" if mt['creado'] else "NULL AS creado_en"},
                    NULL AS proyecto
                FROM tareas t
                ORDER BY t.{mt['id']} DESC
            """)
        tareas = cur.fetchall()
        return render_template("tareas/list.html", tareas=tareas)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/tareas/crear", methods=["GET", "POST"])
@login_required
def crear_tarea():
    conn = get_connection()
    cur = None
    try:
        mt = map_tareas(conn)
        proyectos = _fetch_proyectos(conn)
        if request.method == "POST":
            proyecto_id = request.form.get("proyecto_id") or None
            titulo = (request.form.get("titulo") or "").strip()
            estado = (request.form.get("estado") or "pendiente").strip()
            asignado = (request.form.get("asignado_a") or "").strip()
            if not titulo or (mt["proy_fk"] and not proyecto_id):
                flash("Título y Proyecto son obligatorios.", "warning")
                return render_template("tareas/form.html", tarea=None, proyectos=proyectos)
            cols, vals = [], []
            if mt["proy_fk"]:
                cols.append(mt["proy_fk"]); vals.append(proyecto_id)
            cols += [mt["titulo"], mt["estado"], mt["asignado"]]
            vals += [titulo, estado, (asignado or None)]
            placeholders = ",".join(["%s"] * len(vals))
            cur = conn.cursor()
            try:
                cur.execute(f"INSERT INTO tareas ({', '.join(cols)}) VALUES ({placeholders})", tuple(vals))
                conn.commit()
                flash("Tarea creada.", "success")
                return redirect(url_for("listar_tareas"))
            except Exception:
                conn.rollback()
                flash("No se pudo crear la tarea.", "danger")
            finally:
                if cur: cur.close(); cur = None
        return render_template("tareas/form.html", tarea=None, proyectos=proyectos)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/tareas/editar/<int:tarea_id>", methods=["GET", "POST"])
@login_required
def editar_tarea(tarea_id):
    conn = get_connection()
    cur = None
    try:
        mt = map_tareas(conn)
        proyectos = _fetch_proyectos(conn)
        if request.method == "POST":
            proyecto_id = request.form.get("proyecto_id") or None
            titulo = (request.form.get("titulo") or "").strip()
            estado = (request.form.get("estado") or "pendiente").strip()
            asignado = (request.form.get("asignado_a") or "").strip()
            if not titulo or (mt["proy_fk"] and not proyecto_id):
                flash("Título y Proyecto son obligatorios.", "warning")
            else:
                sets, vals = [], []
                if mt["proy_fk"]:
                    sets.append(f"{mt['proy_fk']}=%s"); vals.append(proyecto_id)
                sets.append(f"{mt['titulo']}=%s");  vals.append(titulo)
                sets.append(f"{mt['estado']}=%s");  vals.append(estado)
                sets.append(f"{mt['asignado']}=%s"); vals.append(asignado or None)
                vals.append(tarea_id)
                cur = conn.cursor()
                try:
                    cur.execute(f"UPDATE tareas SET {', '.join(sets)} WHERE {mt['id']}=%s", tuple(vals))
                    conn.commit()
                    flash("Tarea actualizada.", "success")
                    return redirect(url_for("listar_tareas"))
                except Exception:
                    conn.rollback()
                    flash("No se pudo actualizar la tarea.", "danger")
                finally:
                    if cur: cur.close(); cur = None
        cur = conn.cursor(dictionary=True)
        campos = [f"{mt['id']} AS id",
                  f"{mt['titulo']} AS titulo",
                  f"{mt['estado']} AS estado",
                  f"{mt['asignado']} AS asignado_a"]
        if mt["proy_fk"]:
            campos.append(f"{mt['proy_fk']} AS proyecto_id")
        else:
            campos.append("NULL AS proyecto_id")
        cur.execute(f"SELECT {', '.join(campos)} FROM tareas WHERE {mt['id']}=%s", (tarea_id,))
        tarea = cur.fetchone()
        return render_template("tareas/form.html", tarea=tarea, proyectos=proyectos)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/tareas/eliminar/<int:tarea_id>", methods=["GET", "POST"])
@login_required
def eliminar_tarea(tarea_id):
    if request.method == "POST":
        conn = get_connection()
        cur = None
        try:
            mt = map_tareas(conn)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM tareas WHERE {mt['id']}=%s", (tarea_id,))
            conn.commit()
            flash("Tarea eliminada.", "info")
            return redirect(url_for("listar_tareas"))
        except Exception:
            conn.rollback()
            flash("No se pudo eliminar la tarea.", "danger")
            return redirect(url_for("listar_tareas"))
        finally:
            if cur: cur.close()
            conn.close()
    conn = get_connection()
    cur = None
    try:
        mt = map_tareas(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT {mt['id']} AS id, {mt['titulo']} AS titulo FROM tareas WHERE {mt['id']}=%s", (tarea_id,))
        tarea = cur.fetchone()
        return render_template("tareas/confirm_delete.html", tarea=tarea)
    finally:
        if cur: cur.close()
        conn.close()

# =====================================================
# ==============  PRODUCTOS (CRUD)  ===================
# =====================================================
def _fetch_categorias(conn):
    if not _table_exists(conn, "categorias"):
        return []
    m = map_categorias(conn)
    cur = conn.cursor(dictionary=True)
    cur.execute(f"SELECT {m['id']} AS id, {m['nombre']} AS nombre FROM categorias ORDER BY {m['nombre']}")
    rows = cur.fetchall()
    cur.close()
    return rows

@app.route("/productos")
@login_required
def listar_productos():
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "productos"):
            flash("La tabla 'productos' no existe.", "warning")
            return render_template("productos/list.html", productos=[])
        mp = map_productos(conn)
        can_join = mp["cat_fk"] and _table_exists(conn, "categorias")
        mc = map_categorias(conn) if can_join else None
        cur = conn.cursor(dictionary=True)
        if can_join and mc["id"] and mc["nombre"]:
            cur.execute(f"""
                SELECT
                    p.{mp['id']}     AS id,
                    p.{mp['nombre']} AS nombre,
                    {f"p.{mp['precio']} AS precio" if mp['precio'] else "NULL AS precio"},
                    {f"p.{mp['stock']}  AS stock"  if mp['stock']  else "NULL AS stock"},
                    c.{mc['nombre']} AS categoria
                FROM productos p
                LEFT JOIN categorias c ON c.{mc['id']} = p.{mp['cat_fk']}
                ORDER BY p.{mp['id']} DESC
            """)
        else:
            cur.execute(f"""
                SELECT
                    p.{mp['id']}     AS id,
                    p.{mp['nombre']} AS nombre,
                    {f"p.{mp['precio']} AS precio" if mp['precio'] else "NULL AS precio"},
                    {f"p.{mp['stock']}  AS stock"  if mp['stock']  else "NULL AS stock"},
                    NULL AS categoria
                FROM productos p
                ORDER BY p.{mp['id']} DESC
            """)
        productos = cur.fetchall()
        return render_template("productos/list.html", productos=productos)
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/productos/crear", methods=["GET","POST"])
@login_required
def crear_producto():
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "productos"):
            flash("La tabla 'productos' no existe.", "danger")
            return redirect(url_for("listar_productos"))
        mp = map_productos(conn)
        categorias = _fetch_categorias(conn) if mp["cat_fk"] else []
        if request.method == "POST":
            nombre = (request.form.get("nombre") or "").strip()
            precio = (request.form.get("precio") or "0").strip()
            stock  = (request.form.get("stock") or "0").strip()
            cat_id = request.form.get("categoria_id") if mp["cat_fk"] else None

            if not nombre:
                flash("El nombre es obligatorio.", "warning")
                return render_template("productos/form.html", producto=None, categorias=categorias, cat_fk=mp["cat_fk"])
            try:
                precio_val = float(precio or 0); stock_val = int(stock or 0)
            except ValueError:
                flash("Precio/Stock inválidos.", "warning")
                return render_template("productos/form.html", producto=None, categorias=categorias, cat_fk=mp["cat_fk"])

            cols, vals = [mp["nombre"]], [nombre]
            if mp["precio"]: cols.append(mp["precio"]); vals.append(precio_val)
            if mp["stock"]:  cols.append(mp["stock"]);  vals.append(stock_val)
            if mp["cat_fk"]: cols.append(mp["cat_fk"]); vals.append(cat_id or None)

            placeholders = ",".join(["%s"] * len(vals))
            cur = conn.cursor()
            try:
                cur.execute(f"INSERT INTO productos ({', '.join(cols)}) VALUES ({placeholders})", tuple(vals))
                conn.commit()
                flash("Producto creado.", "success")
                return redirect(url_for("listar_productos"))
            except Exception:
                conn.rollback()
                flash("No se pudo crear el producto.", "danger")
            finally:
                if cur: cur.close(); cur = None
        return render_template("productos/form.html", producto=None, categorias=categorias, cat_fk=mp["cat_fk"])
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/productos/editar/<int:prod_id>", methods=["GET","POST"])
@login_required
def editar_producto(prod_id):
    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "productos"):
            flash("La tabla 'productos' no existe.", "danger")
            return redirect(url_for("listar_productos"))
        mp = map_productos(conn)
        categorias = _fetch_categorias(conn) if mp["cat_fk"] else []

        if request.method == "POST":
            nombre = (request.form.get("nombre") or "").strip()
            precio = (request.form.get("precio") or "0").strip()
            stock  = (request.form.get("stock") or "0").strip()
            cat_id = request.form.get("categoria_id") if mp["cat_fk"] else None

            if not nombre:
                flash("El nombre es obligatorio.", "warning")
            else:
                try:
                    precio_val = float(precio or 0); stock_val = int(stock or 0)
                except ValueError:
                    flash("Precio/Stock inválidos.", "warning")
                    return render_template("productos/form.html", producto=None, categorias=categorias, cat_fk=mp["cat_fk"])

                sets, vals = [f"{mp['nombre']}=%s"], [nombre]
                if mp["precio"]: sets.append(f"{mp['precio']}=%s"); vals.append(precio_val)
                if mp["stock"]:  sets.append(f"{mp['stock']}=%s");  vals.append(stock_val)
                if mp["cat_fk"]: sets.append(f"{mp['cat_fk']}=%s"); vals.append(cat_id or None)
                vals.append(prod_id)

                cur = conn.cursor()
                try:
                    cur.execute(f"UPDATE productos SET {', '.join(sets)} WHERE {mp['id']}=%s", tuple(vals))
                    conn.commit()
                    flash("Producto actualizado.", "success")
                    return redirect(url_for("listar_productos"))
                except Exception:
                    conn.rollback()
                    flash("No se pudo actualizar el producto.", "danger")
                finally:
                    if cur: cur.close(); cur = None

        # cargar producto
        cur = conn.cursor(dictionary=True)
        campos = [f"{mp['id']} AS id", f"{mp['nombre']} AS nombre"]
        campos.append(f"{mp['precio']} AS precio" if mp["precio"] else "NULL AS precio")
        campos.append(f"{mp['stock']} AS stock" if mp["stock"] else "NULL AS stock")
        if mp["cat_fk"]:
            campos.append(f"{mp['cat_fk']} AS categoria_id")
        else:
            campos.append("NULL AS categoria_id")
        cur.execute(f"SELECT {', '.join(campos)} FROM productos WHERE {mp['id']}=%s", (prod_id,))
        producto = cur.fetchone()
        return render_template("productos/form.html", producto=producto, categorias=categorias, cat_fk=mp["cat_fk"])
    finally:
        if cur: cur.close()
        conn.close()

@app.route("/productos/eliminar/<int:prod_id>", methods=["GET","POST"])
@login_required
def eliminar_producto(prod_id):
    if request.method == "POST":
        conn = get_connection()
        cur = None
        try:
            if not _table_exists(conn, "productos"):
                flash("La tabla 'productos' no existe.", "danger")
                return redirect(url_for("listar_productos"))
            mp = map_productos(conn)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM productos WHERE {mp['id']}=%s", (prod_id,))
            conn.commit()
            flash("Producto eliminado.", "info")
            return redirect(url_for("listar_productos"))
        except Exception:
            conn.rollback()
            flash("No se pudo eliminar el producto.", "danger")
            return redirect(url_for("listar_productos"))
        finally:
            if cur: cur.close()
            conn.close()

    conn = get_connection()
    cur = None
    try:
        if not _table_exists(conn, "productos"):
            flash("La tabla 'productos' no existe.", "danger")
            return redirect(url_for("listar_productos"))
        mp = map_productos(conn)
        cur = conn.cursor(dictionary=True)
        cur.execute(f"SELECT {mp['id']} AS id, {mp['nombre']} AS nombre FROM productos WHERE {mp['id']}=%s", (prod_id,))
        producto = cur.fetchone()
        return render_template("productos/confirm_delete.html", producto=producto)
    finally:
        if cur: cur.close()
        conn.close()

# -----------------------------------------------------
# Run
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

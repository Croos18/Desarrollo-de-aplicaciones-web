#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Avanzado de Gestión de Inventario (POO + Colecciones + SQLite)
Autor: (coloca tu nombre)
Descripción:
- Consola interactiva para gestionar inventario de una tienda (ferretería, panadería, librería, etc.).
- Usa clases Producto e Inventario.
- Usa colecciones (dict, list, set, tuple) para optimizar búsquedas y operaciones.
- Persiste todo en SQLite (inventario.db).
Requisitos: Python 3.10+ (sin librerías externas).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import sqlite3
from datetime import datetime

# -------------------------------
#  Utilidades
# -------------------------------

def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def normalize(s: str) -> str:
    return " ".join(s.strip().lower().split())

def tokenize_name(name: str) -> List[str]:
    """Tokeniza el nombre para el índice de búsqueda por palabras."""
    sep = " "
    clean = normalize(name).replace(",", sep).replace(".", sep).replace("-", sep).replace("_", sep).replace("/", sep)
    tokens = [t for t in clean.split() if t]
    return tokens

# -------------------------------
#  Modelo: Producto
# -------------------------------

@dataclass
class Producto:
    """
    Representa un producto del inventario.
    Atributos:
        id: int | None  (si es None, se asigna al guardar en la BD)
        nombre: str
        cantidad: int (>= 0)
        precio: float  (>= 0)
    """
    id: Optional[int]
    nombre: str
    cantidad: int
    precio: float

    def get_id(self) -> Optional[int]:
        return self.id

    def get_nombre(self) -> str:
        return self.nombre

    def get_cantidad(self) -> int:
        return self.cantidad

    def get_precio(self) -> float:
        return self.precio

    def set_nombre(self, nuevo_nombre: str) -> None:
        nuevo_nombre = nuevo_nombre.strip()
        if not nuevo_nombre:
            raise ValueError("El nombre no puede estar vacío.")
        self.nombre = nuevo_nombre

    def set_cantidad(self, nueva_cantidad: int) -> None:
        if nueva_cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa.")
        self.cantidad = int(nueva_cantidad)

    def set_precio(self, nuevo_precio: float) -> None:
        if nuevo_precio < 0:
            raise ValueError("El precio no puede ser negativo.")
        self.precio = float(nuevo_precio)

    @staticmethod
    def from_row(row: Tuple) -> "Producto":
        return Producto(id=row[0], nombre=row[1], cantidad=row[2], precio=row[3])

# -------------------------------
#  Repositorio + Servicio: Inventario
# -------------------------------

class Inventario:
    """
    Maneja el cache en memoria (colecciones) y la persistencia en SQLite.
    - Colecciones:
        * self.productos: Dict[int, Producto]
        * self.index_nombre: Dict[str, Set[int]]
    """

    def __init__(self, db_path: str = "inventario.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")

        self._create_schema()

        self.productos: Dict[int, Producto] = {}
        self.index_nombre: Dict[str, Set[int]] = {}
        self._load_cache()

    def _create_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cantidad INTEGER NOT NULL CHECK (cantidad >= 0),
                precio REAL NOT NULL CHECK (precio >= 0),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos (nombre)")
        self.conn.commit()

    def _load_cache(self) -> None:
        self.productos.clear()
        self.index_nombre.clear()
        cur = self.conn.cursor()
        for row in cur.execute("SELECT id, nombre, cantidad, precio, created_at, updated_at FROM productos"):
            p = Producto.from_row(row)
            self.productos[p.id] = p
            self._add_to_index(p)

    def _add_to_index(self, p: Producto) -> None:
        for tok in tokenize_name(p.nombre):
            self.index_nombre.setdefault(tok, set()).add(p.id)

    def _remove_from_index(self, p: Producto) -> None:
        for tok in tokenize_name(p.nombre):
            ids = self.index_nombre.get(tok)
            if ids:
                ids.discard(p.id)
                if not ids:
                    self.index_nombre.pop(tok, None)

    def _update_index(self, old: Producto, new: Producto) -> None:
        self._remove_from_index(old)
        self._add_to_index(new)

    # ---------- CRUD ----------
    def add_producto(self, p: Producto) -> Producto:
        if p.cantidad < 0 or p.precio < 0:
            raise ValueError("Cantidad y precio deben ser >= 0.")
        cur = self.conn.cursor()
        ts = now_iso()
        if p.id is None:
            cur.execute(
                "INSERT INTO productos (nombre, cantidad, precio, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (p.nombre, p.cantidad, p.precio, ts, ts),
            )
            p.id = cur.lastrowid
        else:
            cur.execute("SELECT 1 FROM productos WHERE id = ?", (p.id,))
            if cur.fetchone():
                raise ValueError(f"Ya existe un producto con id={p.id}.")
            cur.execute(
                "INSERT INTO productos (id, nombre, cantidad, precio, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (p.id, p.nombre, p.cantidad, p.precio, ts, ts),
            )
        self.conn.commit()
        self.productos[p.id] = p
        self._add_to_index(p)
        return p

    def eliminar_producto(self, id_producto: int) -> bool:
        p = self.productos.get(id_producto)
        if not p:
            return False
        cur = self.conn.cursor()
        cur.execute("DELETE FROM productos WHERE id = ?", (id_producto,))
        self.conn.commit()
        self._remove_from_index(p)
        self.productos.pop(id_producto, None)
        return True

    def actualizar_producto(self, id_producto: int, nombre: Optional[str] = None, cantidad: Optional[int] = None, precio: Optional[float] = None) -> bool:
        p = self.productos.get(id_producto)
        if not p:
            return False
        old = Producto(p.id, p.nombre, p.cantidad, p.precio)
        if nombre is not None: p.set_nombre(nombre)
        if cantidad is not None: p.set_cantidad(cantidad)
        if precio is not None: p.set_precio(precio)
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE productos SET nombre = ?, cantidad = ?, precio = ?, updated_at = ? WHERE id = ?",
            (p.nombre, p.cantidad, p.precio, now_iso(), id_producto),
        )
        self.conn.commit()
        if old.nombre != p.nombre: self._update_index(old, p)
        return True

    def buscar_por_nombre(self, consulta: str) -> List[Producto]:
        consulta_norm = normalize(consulta)
        if not consulta_norm: return []
        tokens = tokenize_name(consulta_norm)
        candidatos: Set[int] = set()
        if tokens:
            token_sets = [self.index_nombre.get(tok, set()) for tok in tokens]
            if token_sets:
                candidatos = token_sets[0].copy()
                for s in token_sets[1:]: candidatos &= s
        resultados: Dict[int, Producto] = {}
        if not candidatos:
            like = f"%{consulta_norm}%"
            cur = self.conn.cursor()
            for row in cur.execute(
                "SELECT id, nombre, cantidad, precio, created_at, updated_at FROM productos WHERE lower(nombre) LIKE ?",
                (like,),
            ):
                p = Producto.from_row(row)
                resultados[p.id] = p
        else:
            for pid in candidatos:
                p = self.productos.get(pid)
                if p and consulta_norm in normalize(p.nombre):
                    resultados[p.id] = p
        return sorted(resultados.values(), key=lambda x: x.id or 0)

    def mostrar_todos(self) -> List[Producto]:
        return sorted(self.productos.values(), key=lambda p: p.id or 0)

    def close(self) -> None:
        try: self.conn.close()
        except Exception: pass

# -------------------------------
#  Interfaz de Usuario (CLI)
# -------------------------------

def print_table(productos: List[Producto]) -> None:
    if not productos:
        print("No hay productos para mostrar.")
        return
    headers = ("ID", "NOMBRE", "CANTIDAD", "PRECIO")
    rows = [(str(p.id), p.nombre, str(p.cantidad), f"{p.precio:.2f}") for p in productos]
    col_widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    def fmt_row(cols: Tuple[str, str, str, str]) -> str:
        return " | ".join(c.ljust(col_widths[i]) for i, c in enumerate(cols))
    print(fmt_row(headers))
    print("-+-".join("-" * w for w in col_widths))
    for r in rows: print(fmt_row(r))

def prompt_int(msg: str, allow_empty: bool = False) -> Optional[int]:
    while True:
        val = input(msg).strip()
        if not val and allow_empty: return None
        try: return int(val)
        except ValueError: print("Ingrese un número entero válido.")

def prompt_float(msg: str, allow_empty: bool = False) -> Optional[float]:
    while True:
        val = input(msg).strip()
        if not val and allow_empty: return None
        try:
            v = float(val)
            if v < 0: 
                print("El valor no puede ser negativo."); continue
            return v
        except ValueError: print("Ingrese un número válido (use punto para decimales).")

def prompt_str(msg: str, allow_empty: bool = False) -> Optional[str]:
    while True:
        val = input(msg).strip()
        if not val and allow_empty: return None
        if not val: print("No puede estar vacío."); continue
        return val

def menu() -> None:
    inv = Inventario()
    if not inv.productos:
        print("Inicializando con datos de ejemplo...")
        inv.add_producto(Producto(None, "Lápiz HB", 100, 0.35))
        inv.add_producto(Producto(None, "Cuaderno universitario 100 hojas", 50, 2.10))
        inv.add_producto(Producto(None, "Borrador blanco", 80, 0.50))
    try:
        while True:
            print("\n=== MENÚ INVENTARIO ===")
            print("1. Añadir producto")
            print("2. Eliminar producto por ID")
            print("3. Actualizar producto")
            print("4. Buscar productos por nombre")
            print("5. Mostrar todos los productos")
            print("6. Salir")
            opcion = input("Elija una opción [1-6]: ").strip()
            if opcion == "1":
                pid_opt = prompt_int("ID (enter para autogenerar): ", allow_empty=True)
                nombre = prompt_str("Nombre: ")
                cantidad = prompt_int("Cantidad: ")
                precio = prompt_float("Precio: ")
                try:
                    p = Producto(pid_opt, nombre, cantidad, precio)
                    inv.add_producto(p)
                    print(f"Producto añadido con ID {p.id}.")
                except Exception as e: print(f"Error: {e}")
            elif opcion == "2":
                pid = prompt_int("ID del producto a eliminar: ")
                print("Producto eliminado." if inv.eliminar_producto(pid) else "No existe un producto con ese ID.")
            elif opcion == "3":
                pid = prompt_int("ID del producto a actualizar: ")
                if pid not in inv.productos:
                    print("No existe un producto con ese ID."); continue
                nombre = prompt_str("Nuevo nombre: ", allow_empty=True)
                cantidad = prompt_int("Nueva cantidad: ", allow_empty=True)
                precio = prompt_float("Nuevo precio: ", allow_empty=True)
                try:
                    ok = inv.actualizar_producto(
                        pid,
                        nombre=nombre if nombre is not None else None,
                        cantidad=cantidad if cantidad is not None else None,
                        precio=precio if precio is not None else None,
                    )
                    print("Producto actualizado." if ok else "No se pudo actualizar.")
                except Exception as e: print(f"Error: {e}")
            elif opcion == "4":
                q = prompt_str("Texto a buscar: ")
                print_table(inv.buscar_por_nombre(q))
            elif opcion == "5":
                print_table(inv.mostrar_todos())
            elif opcion == "6":
                print("Saliendo... ¡Inventario en orden, capitán!"); break
            else:
                print("Opción inválida.")
    finally:
        inv.close()

if __name__ == "__main__":
    menu()

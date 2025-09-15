# conexion.py
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# carga .env desde el directorio actual
load_dotenv()

def get_connection():
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = int(os.getenv("DB_PORT", "3306"))
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    pwd  = os.getenv("DB_PASS", "")

    # Validación explícita (evita el caso 'ODBC' por valores vacíos)
    missing = [k for k,v in [("DB_NAME",name),("DB_USER",user)] if not v]
    if missing:
        raise RuntimeError(f"Faltan variables en .env: {', '.join(missing)}")

    # Log útil (aparece en la consola de Flask)
    print(f"[DB] host={host} port={port} db={name} user={user!r}")

    return mysql.connector.connect(
        host=host,
        port=port,
        database=name,
        user=user,
        password=pwd,
        autocommit=True
    )

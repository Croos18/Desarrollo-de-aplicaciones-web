# Semana_13 — Flask + Login + CRUD (Categorías ↔ Productos)

- Login/Registro con Flask-Login (hash de contraseñas)
- CRUD de categorías y productos (relación 1:N)
- MySQL/MariaDB con variables de entorno `.env`
- Script SQL: `schema.sql` con tablas y datos de prueba

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env  # (si usas plantilla) o crea .env
# Edita DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
mysql -u root -p -h 127.0.0.1 < schema.sql
python app.py

import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'InventarioBD_2.db'

default_admin_pass = 'admin123'
hashed_password = generate_password_hash(default_admin_pass)

conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

def run_query(query, params=(), error_ok=False):
    """Ejecuta una consulta y maneja errores comunes."""
    try:
        cursor.execute(query, params)
        print(f"Éxito: {query.split()[0]} {query.split()[1]}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e) or "already exists" in str(e) or error_ok:
            print(f"Advertencia: {e}")
        else:
            raise e

print("--- Iniciando migración de la base de datos ---")

run_query("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    rol TEXT NOT NULL CHECK(rol IN ('admin', 'productos', 'almacenes'))
)
""")

run_query("ALTER TABLE productos ADD COLUMN fecha_modificacion TEXT")
run_query("ALTER TABLE productos ADD COLUMN usuario_modificacion TEXT")

run_query("ALTER TABLE almacenes ADD COLUMN fecha_modificacion TEXT")
run_query("ALTER TABLE almacenes ADD COLUMN usuario_modificacion TEXT")

try:
    cursor.execute("INSERT INTO usuarios (nombre, password, rol) VALUES (?, ?, ?)", 
                   ('admin', hashed_password, 'admin'))
    print(f"\n*** ¡Usuario Admin Creado! ***")
    print(f"Usuario: admin")
    print(f"Password: {default_admin_pass}")
    print("Usa estas credenciales para iniciar sesión.")
except sqlite3.IntegrityError:
    print("\nEl usuario 'admin' ya existe. No se creó uno nuevo.")

conn.commit()
conn.close()

print("--- Migración de la base de datos completada ---")
import sqlite3
import datetime
from werkzeug.security import generate_password_hash

DATABASE = 'InventarioBD_2.db'
conn = sqlite3.connect(DATABASE)
cursor = conn.cursor()

print("--- Actualizando Base de Datos a Requisitos Finales ---")

# 1. Agregar columnas faltantes a USUARIOS
try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN fecha_hora_ultimo_inicio TEXT")
    print("Columna 'fecha_hora_ultimo_inicio' agregada a usuarios.")
except sqlite3.OperationalError:
    print("Columna 'fecha_hora_ultimo_inicio' ya existe.")

# 2. Agregar columnas faltantes a PRODUCTOS
try:
    cursor.execute("ALTER TABLE productos ADD COLUMN fecha_hora_creacion TEXT")
    # Establecer fecha actual por defecto para los existentes
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE productos SET fecha_hora_creacion = ? WHERE fecha_hora_creacion IS NULL", (now,))
    print("Columna 'fecha_hora_creacion' agregada a productos.")
except sqlite3.OperationalError:
    print("Columna 'fecha_hora_creacion' ya existe.")

# 3. Agregar columnas faltantes a ALMACENES
try:
    cursor.execute("ALTER TABLE almacenes ADD COLUMN fecha_hora_creacion TEXT")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE almacenes SET fecha_hora_creacion = ? WHERE fecha_hora_creacion IS NULL", (now,))
    print("Columna 'fecha_hora_creacion' agregada a almacenes.")
except sqlite3.OperationalError:
    print("Columna 'fecha_hora_creacion' ya existe.")

# 4. Actualizar los usuarios 
users_to_create = [
    ('ADMIN', 'admin23', 'admin'),
    ('PRODUCTOS', 'productos 19', 'productos'), 
    ('ALMACENES', 'almacenes11', 'almacenes')
]

for name, pwd, role in users_to_create:
    try:
        hashed = generate_password_hash(pwd)
        # Intentamos insertar
        cursor.execute("INSERT INTO usuarios (nombre, password, rol) VALUES (?, ?, ?)", (name, hashed, role))
        print(f"Usuario {name} creado.")
    except sqlite3.IntegrityError:
        # Si ya existe (por nombre único), se actualiza el password y rol
        hashed = generate_password_hash(pwd)
        cursor.execute("UPDATE usuarios SET password = ?, rol = ? WHERE nombre = ?", (hashed, role, name))
        print(f"Usuario {name} actualizado a los requisitos del PDF.")

conn.commit()
conn.close()
print("--- Finalizado ---")
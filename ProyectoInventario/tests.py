import unittest
import sqlite3
import os
from app import app
from werkzeug.security import generate_password_hash

class InventarioTestCase(unittest.TestCase):

    def setUp(self):
        """Se ejecuta ANTES de cada prueba. Configura una BD temporal."""
        # Configurar la app para modo de pruebas
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        # Usar una BD diferente para no borrar tus datos reales
        self.db_name = 'Test_Inventario.db'
        app.config['DATABASE'] = self.db_name
        
        # Parchear la variable global DATABASE en app.py para que apunte a la de prueba
        import app as application
        application.DATABASE = self.db_name

        self.client = app.test_client()
        
        # Crear la estructura de la BD temporal
        self.init_test_db()

    def tearDown(self):
        """Se ejecuta DESPUÉS de cada prueba. Borra la BD temporal."""
        if os.path.exists(self.db_name):
            os.remove(self.db_name)

    def init_test_db(self):
        """Crea las tablas y un usuario Admin para probar."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Crear tabla usuarios (copia simplificada del esquema real)
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                rol TEXT NOT NULL,
                fecha_hora_ultimo_inicio TEXT
            )
        """)
        
        # Crear un usuario ADMIN para las pruebas
        password_hash = generate_password_hash('admin123')
        cursor.execute("INSERT INTO usuarios (nombre, password, rol) VALUES (?, ?, ?)", 
                       ('ADMIN', password_hash, 'ADMIN'))
        
        conn.commit()
        conn.close()

    # --- LAS PRUEBAS ---

    def test_pagina_inicio_redirige(self):
        """Prueba 1: Entrar a /inicio sin loguearse debe redirigir al login."""
        response = self.client.get('/inicio', follow_redirects=True)
        # Buscamos texto que solo aparece en el login
        self.assertIn(b'Iniciar sesi', response.data) 

    def test_login_exitoso(self):
        """Prueba 2: Loguearse con credenciales correctas."""
        response = self.client.post('/', data=dict(
            nombre='ADMIN',
            password='admin123'
        ), follow_redirects=True)
        
        # Si es exitoso, deberíamos ver el título del dashboard
        self.assertIn(b'SISTEMA', response.data)

    def test_login_fallido(self):
        """Prueba 3: Loguearse con contraseña incorrecta."""
        response = self.client.post('/', data=dict(
            nombre='ADMIN',
            password='clave_incorrecta'
        ), follow_redirects=True)
        
        # Debería mantenerse en el login y mostrar error
        self.assertIn(b'Usuario o contrase', response.data)

if __name__ == '__main__':
    unittest.main()
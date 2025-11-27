import sqlite3
import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# --- Configuración ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_proyecto_final' 
DATABASE = 'InventarioBD_2.db'

# --- Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder.'

# --- Modelo de Usuario ---
class User(UserMixin):
    def __init__(self, id, nombre, rol):
        self.id = id
        self.nombre = nombre
        self.rol = rol

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        if user_row:
            return User(id=user_row['id'], nombre=user_row['nombre'], rol=user_row['rol'])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# --- Decorador de Roles ---
def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return login_manager.unauthorized()
            
            # Se normaliza a mayúsculas para comparar (ADMIN vs admin)
            user_role = current_user.rol.upper() if current_user.rol else ''
            allowed_roles = [r.upper() for r in roles]
            
            if user_role not in allowed_roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('inicio'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# --- Base de Datos ---
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTAS PRINCIPALES ---

@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))
    
    if request.method == 'POST':
        nombre = request.form['nombre']
        password = request.form['password']
        
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM usuarios WHERE nombre = ?', (nombre,)).fetchone()
        
        if user_row and check_password_hash(user_row['password'], password):
            # Actualizar fecha_hora_ultimo_inicio al loguearse
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute('UPDATE usuarios SET fecha_hora_ultimo_inicio = ? WHERE id = ?', (now, user_row['id']))
            conn.commit()
            conn.close()
            # ------------------------------------------
            
            user = User(id=user_row['id'], nombre=user_row['nombre'], rol=user_row['rol'])
            login_user(user)
            return redirect(url_for('inicio'))
        else:
            conn.close()
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/inicio')
@login_required
def inicio():
    return render_template('inicio.html', active_page='inicio')

@app.route('/productos')
@login_required
def productos():
    return render_template('productos.html', active_page='productos')

@app.route('/almacenes')
@login_required
def almacenes():
    return render_template('almacenes.html', active_page='almacenes')

@app.route('/admin')
@login_required
@role_required('ADMIN')
def admin_panel():
    return render_template('admin.html', active_page='admin')

# --- API ENDPOINTS (CRUD) ---

# 1. USUARIOS
@app.route('/api/usuarios', methods=['POST'])
@login_required
@role_required('ADMIN')
def add_usuario():
    data = request.json
    try:
        hashed = generate_password_hash(data['password'])
        # Aseguramos que el rol se guarde en mayúsculas
        rol_upper = data['rol'].upper()
        
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (nombre, password, rol) VALUES (?, ?, ?)',
                     (data['nombre'], hashed, rol_upper))
        conn.commit()
        conn.close()
        return jsonify({'success': True}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

# 2. PRODUCTOS
@app.route('/api/productos', methods=['GET'])
@login_required
def get_productos():
    conn = get_db_connection()
    productos = conn.execute('SELECT * FROM productos').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in productos])

@app.route('/api/productos', methods=['POST'])
@login_required
@role_required('ADMIN', 'PRODUCTOS')
def add_producto():
    data = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = current_user.nombre
    
    conn = get_db_connection()
    # Insertamos incluyendo la fecha de creación
    conn.execute(
        '''INSERT INTO productos (nombre, precio, cantidad, departamento, almacen, 
           fecha_hora_creacion, fecha_modificacion, usuario_modificacion) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen'], now, now, usuario)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/productos/<int:id>', methods=['PUT'])
@login_required
@role_required('ADMIN', 'PRODUCTOS')
def update_producto(id):
    data = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = current_user.nombre
    
    conn = get_db_connection()
    # Actualizamos solo fecha de modificación, NO la de creación
    conn.execute(
        '''UPDATE productos SET nombre = ?, precio = ?, cantidad = ?, departamento = ?, 
           almacen = ?, fecha_modificacion = ?, usuario_modificacion = ? WHERE id = ?''',
        (data['nombre'], data['precio'], data['cantidad'], data['departamento'], data['almacen'], now, usuario, id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/productos/<int:id>', methods=['DELETE'])
@login_required
@role_required('ADMIN', 'PRODUCTOS')
def delete_producto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM productos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# 3. ALMACENES
@app.route('/api/almacenes', methods=['GET'])
@login_required
def get_almacenes():
    conn = get_db_connection()
    almacenes = conn.execute('SELECT * FROM almacenes').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in almacenes])

@app.route('/api/almacenes', methods=['POST'])
@login_required
@role_required('ADMIN', 'ALMACENES')
def add_almacen():
    data = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = current_user.nombre

    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO almacenes (nombre, fecha_hora_creacion, fecha_modificacion, usuario_modificacion) 
           VALUES (?, ?, ?, ?)''',
        (data['nombre'], now, now, usuario)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/almacenes/<int:id>', methods=['PUT'])
@login_required
@role_required('ADMIN', 'ALMACENES')
def update_almacen(id):
    data = request.json
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario = current_user.nombre

    conn = get_db_connection()
    conn.execute(
        'UPDATE almacenes SET nombre = ?, fecha_modificacion = ?, usuario_modificacion = ? WHERE id = ?',
        (data['nombre'], now, usuario, id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/almacenes/<int:id>', methods=['DELETE'])
@login_required
@role_required('ADMIN', 'ALMACENES')
def delete_almacen(id):
    conn = get_db_connection()
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.execute('DELETE FROM almacenes WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'No se puede eliminar. El almacén está siendo usado por productos.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
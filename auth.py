import os
from datetime import date
from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


def get_usuario(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.path))
        fecha_cad = session.get('fecha_caducidad', '')
        if fecha_cad:
            try:
                if date.today() > date.fromisoformat(fecha_cad):
                    session.clear()
                    flash('Tu acceso ha vencido. Contacta al administrador.', 'danger')
                    return redirect(url_for('login'))
            except ValueError:
                pass
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.path))
        user = get_usuario(session['user_id'])
        if not user or not user['es_admin']:
            flash('Acceso denegado. Solo el administrador puede hacer eso.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def crear_usuario(username, password, es_admin=False):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, es_admin) VALUES (?, ?, ?)",
            (username.strip().lower(), generate_password_hash(password), 1 if es_admin else 0)
        )
        conn.commit()
        return True, None
    except Exception as e:
        if 'UNIQUE' in str(e):
            return False, 'El nombre de usuario ya existe.'
        return False, str(e)
    finally:
        conn.close()


def verificar_login(username, password):
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
        (username.strip().lower(),)
    ).fetchone()
    conn.close()
    if not user or not check_password_hash(user['password_hash'], password):
        return None
    fecha_cad = user['fecha_caducidad'] if user['fecha_caducidad'] else ''
    if fecha_cad:
        try:
            if date.today() > date.fromisoformat(fecha_cad):
                return 'expired'
        except ValueError:
            pass
    return user


def init_admin():
    admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_pass = os.environ.get('ADMIN_PASSWORD', '')
    if not admin_pass:
        return
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    conn.close()
    if count == 0:
        crear_usuario(admin_user, admin_pass, es_admin=True)

#!/usr/bin/env python3
"""
Asegura que el usuario admin principal exista en la BD.
Se ejecuta al iniciar via wsgi.py.
"""
import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conthome.db'))

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'Ediel2215')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def ensure_admin_exists():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username, es_admin FROM usuarios WHERE username = ?", (ADMIN_USERNAME,))
    user = cursor.fetchone()

    if user:
        # Existe pero no es admin → hacerlo admin
        if not user[2]:
            cursor.execute("UPDATE usuarios SET es_admin = 1 WHERE username = ?", (ADMIN_USERNAME,))
            conn.commit()
            print(f"✓ {ADMIN_USERNAME} actualizado a admin")
        else:
            print(f"✓ Admin {ADMIN_USERNAME} OK")
    else:
        # No existe → crearlo
        password_hash = generate_password_hash(ADMIN_PASSWORD)
        cursor.execute(
            "INSERT INTO usuarios (username, password_hash, es_admin, activo) VALUES (?, ?, 1, 1)",
            (ADMIN_USERNAME, password_hash)
        )
        conn.commit()
        print(f"✓ Admin {ADMIN_USERNAME} creado")

    conn.close()


if __name__ == '__main__':
    ensure_admin_exists()

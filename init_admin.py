#!/usr/bin/env python3
"""
Script para asegurar que existe el usuario admin en la BD.
Se ejecuta al iniciar la aplicación.
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'conthome.db'))

def ensure_admin_exists():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Verificar si existe usuario con id=1
    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        # Crear usuario admin
        password_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO usuarios (id, username, password_hash, es_admin, activo) VALUES (?, ?, ?, ?, ?)",
            (1, 'admin', password_hash, 1, 1)
        )
        conn.commit()
        print("✓ Usuario admin creado: admin/admin123")
    else:
        cursor.execute("SELECT username, es_admin FROM usuarios WHERE id = 1")
        user = cursor.fetchone()
        if user:
            print(f"✓ Usuario admin existe: {user[0]} (es_admin={user[1]})")
            # Asegurar que sea admin
            if not user[1]:
                cursor.execute("UPDATE usuarios SET es_admin = 1 WHERE id = 1")
                conn.commit()
                print("✓ Actualizado: usuario es admin")

    conn.close()

if __name__ == '__main__':
    ensure_admin_exists()

import sqlite3
import os

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'conthome.db'))


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            tipo_gasto TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            tipo_gasto TEXT NOT NULL CHECK(tipo_gasto IN ('fijo', 'variable')),
            categoria_id INTEGER,
            fecha TEXT NOT NULL,
            nota TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        );

        CREATE TABLE IF NOT EXISTS ingresos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            nota TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS inversiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            monto_invertido REAL NOT NULL,
            fecha_inicio TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'activa' CHECK(estado IN ('activa', 'cerrada')),
            nota TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS retornos_inversion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inversion_id INTEGER NOT NULL,
            monto REAL NOT NULL,
            fecha TEXT NOT NULL,
            nota TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (inversion_id) REFERENCES inversiones(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            es_admin INTEGER NOT NULL DEFAULT 0,
            activo INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );
    ''')

    # Seed categorias if empty
    count = cursor.execute("SELECT COUNT(*) FROM categorias").fetchone()[0]
    if count == 0:
        categorias_seed = [
            ("Alquiler", "fijo"),
            ("Electricidad", "fijo"),
            ("Agua", "fijo"),
            ("Internet", "fijo"),
            ("Telefono", "fijo"),
            ("Gas", "fijo"),
            ("Seguro", "fijo"),
            ("Comida/Mercado", "variable"),
            ("Transporte", "variable"),
            ("Salud", "variable"),
            ("Educacion", "variable"),
            ("Entretenimiento", "variable"),
            ("Ropa", "variable"),
            ("Mantenimiento", "variable"),
            ("Suscripciones", "fijo"),
            ("Otros", "variable"),
        ]
        cursor.executemany(
            "INSERT INTO categorias (nombre, tipo_gasto) VALUES (?, ?)",
            categorias_seed
        )

    conn.commit()
    conn.close()

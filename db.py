import sqlite3
from datetime import datetime

DB_NAME = "medibot.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                rol TEXT CHECK(rol IN ('user', 'assistant')) NOT NULL,
                contenido TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                nombre TEXT PRIMARY KEY,
                perfil TEXT CHECK(perfil IN ('niño', 'adulto_mayor', 'general')) NOT NULL DEFAULT 'general'
            )
        ''')
        conn.commit()

def guardar_mensaje(usuario, rol, contenido):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO historial (usuario, rol, contenido, fecha)
            VALUES (?, ?, ?, ?)
        ''', (usuario, rol, contenido, datetime.now()))
        conn.commit()

def obtener_historial(usuario, limite=10):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT rol, contenido FROM historial
            WHERE usuario = ?
            ORDER BY fecha DESC
            LIMIT ?
        ''', (usuario, limite))
        filas = c.fetchall()
        return [{"role": rol, "content": contenido} for rol, contenido in reversed(filas)]

def guardar_perfil(nombre, perfil):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO usuarios (nombre, perfil) VALUES (?, ?)", (nombre, perfil))
        conn.commit()

def obtener_perfil(nombre):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT perfil FROM usuarios WHERE nombre = ?", (nombre,))
        fila = c.fetchone()
        return fila[0] if fila else "general"

def nombre_existe(nombre):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM usuarios WHERE nombre = ?", (nombre,))
        return c.fetchone() is not None

# Script para importar agrodata.sql y seed_demo.sql usando mysql-connector-python
# Ejecuta: .\.venv\Scripts\python AgroData\scripts\seed_demo.py

import os
import sys
import mysql.connector
from pathlib import Path
from passlib.hash import pbkdf2_sha256

# Importar configuración
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import Config  # noqa

def run_sql_file(cursor, path):
    # Carga el archivo SQL, ignora bloques con DELIMITER (procedimientos) y ejecuta resto de sentencias
    statements = []
    in_delimiter_block = False
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if stripped.upper().startswith('DELIMITER'):
                in_delimiter_block = not in_delimiter_block
                continue
            if in_delimiter_block:
                # Omitimos procedimientos/funciones que requieren delimitadores personalizados
                continue
            statements.append(line)

    buffer = ''
    for chunk in ''.join(statements).split(';'):
        stmt = (buffer + chunk).strip()
        buffer = ''
        if not stmt:
            continue
        try:
            cursor.execute(stmt)
        except mysql.connector.Error as e:
            # Si falla por fragmentación poco común, acumulamos y reintentamos en la próxima iteración
            buffer = stmt + ';'
    if buffer:
        try:
            cursor.execute(buffer)
        except mysql.connector.Error:
            pass

def main():
    base_dir = Path(__file__).resolve().parents[1]
    db_dir = base_dir / 'database'
    sql_schema = db_dir / 'agrodata.sql'
    sql_seed = db_dir / 'seed_demo.sql'
    sql_seed_more = db_dir / 'seed_more.sql'
    sql_migration = db_dir / 'migration_auth.sql'

    # Conexión al servidor (sin seleccionar BD) para crearla si no existe
    conn_server = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        autocommit=True,
    )
    cur_server = conn_server.cursor()
    cur_server.execute("CREATE DATABASE IF NOT EXISTS agrodata;")
    cur_server.close()
    conn_server.close()

    # Conectar a la BD agrodata
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
    )
    cur = conn.cursor()

    # Ejecutar esquema base y seeds demo
    print(f"Importando esquema: {sql_schema}")
    run_sql_file(cur, sql_schema)
    conn.commit()

    print(f"Importando seeds: {sql_seed}")
    run_sql_file(cur, sql_seed)
    conn.commit()

    if sql_seed_more.exists():
        print(f"Importando seeds extra: {sql_seed_more}")
        run_sql_file(cur, sql_seed_more)
        conn.commit()

    # Aplicar migración de autenticación
    # Asegurar esquema de autenticación (compatible con MySQL sin ALTER ... IF NOT EXISTS)
    print("Verificando esquema de autenticación...")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INT PRIMARY KEY AUTO_INCREMENT,
            email VARCHAR(120) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            nombre VARCHAR(100),
            fecha_registro DATE DEFAULT (CURRENT_DATE)
        )
        """
    )
    conn.commit()

    # Agregar columna user_id si falta
    cur.execute(
        "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='finca' AND COLUMN_NAME='user_id'",
        (Config.MYSQL_DB,)
    )
    if (cur.fetchone() or [0])[0] == 0:
        print("Añadiendo columna finca.user_id ...")
        cur.execute("ALTER TABLE finca ADD COLUMN user_id INT NULL")
        conn.commit()

    # Agregar FK si falta
    cur.execute(
        """
        SELECT COUNT(*)
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME='finca' AND CONSTRAINT_NAME='fk_finca_usuario'
        """,
        (Config.MYSQL_DB,)
    )
    if (cur.fetchone() or [0])[0] == 0:
        print("Añadiendo FK fk_finca_usuario ...")
        cur.execute(
            "ALTER TABLE finca ADD CONSTRAINT fk_finca_usuario FOREIGN KEY (user_id) REFERENCES usuario(id_usuario) ON DELETE SET NULL"
        )
        conn.commit()

    # Crear usuario demo si no existe
    print("Creando usuario demo si no existe...")
    cur.execute("SELECT id_usuario FROM usuario WHERE email=%s", ("demo@agrodata.com",))
    row = cur.fetchone()
    if not row:
        pwd_hash = pbkdf2_sha256.hash("demo123")
        cur.execute(
            "INSERT INTO usuario (email, password_hash, nombre) VALUES (%s, %s, %s)",
            ("demo@agrodata.com", pwd_hash, "Usuario Demo")
        )
        conn.commit()
        user_id = cur.lastrowid
    else:
        user_id = row[0]

    # Asignar finca 1 al usuario demo si existe
    cur.execute("SELECT id_finca, user_id FROM finca WHERE id_finca=1")
    f = cur.fetchone()
    if f and (f[1] is None or f[1] != user_id):
        print("Asignando finca 1 al usuario demo")
        cur.execute("UPDATE finca SET user_id=%s WHERE id_finca=1", (user_id,))
        conn.commit()

    cur.close()
    conn.close()
    print("Importación completada.")

if __name__ == '__main__':
    main()

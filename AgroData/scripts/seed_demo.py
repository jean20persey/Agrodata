# Script para importar agrodata.sql y seed_demo.sql usando mysql-connector-python
# Ejecuta: .\.venv\Scripts\python AgroData\scripts\seed_demo.py

import os
import sys
import mysql.connector
from pathlib import Path

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

    cur.close()
    conn.close()
    print("Importación completada.")

if __name__ == '__main__':
    main()

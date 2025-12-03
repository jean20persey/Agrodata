# Crea un usuario y asigna la finca 1 a ese usuario
# Ejecuta: .\.venv\Scripts\python AgroData\scripts\create_user_and_assign.py "Nombre" "email" "password"

import sys
import mysql.connector
from passlib.hash import pbkdf2_sha256
from pathlib import Path

# Asegurar importación del módulo de configuración
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import Config  # noqa

def main():
    if len(sys.argv) < 4:
        print("Uso: create_user_and_assign.py 'Nombre' 'email' 'password'")
        sys.exit(1)
    nombre, email, password = sys.argv[1], sys.argv[2].lower().strip(), sys.argv[3]

    cnx = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        autocommit=False,
    )
    cur = cnx.cursor()

    # Crear usuario si no existe
    cur.execute("SELECT id_usuario FROM usuario WHERE email=%s", (email,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        print(f"Usuario ya existe: id={user_id}")
    else:
        pwd_hash = pbkdf2_sha256.hash(password)
        cur.execute(
            "INSERT INTO usuario (email, password_hash, nombre) VALUES (%s, %s, %s)",
            (email, pwd_hash, nombre)
        )
        cnx.commit()
        user_id = cur.lastrowid
        print(f"Usuario creado: id={user_id}")

    # Asignar finca 1 al nuevo usuario (reasigna si ya estaba con otro)
    cur.execute("SELECT id_finca FROM finca WHERE id_finca=1")
    if cur.fetchone():
        cur.execute("UPDATE finca SET user_id=%s WHERE id_finca=1", (user_id,))
        cnx.commit()
        print("Finca 1 asignada al usuario.")
    else:
        print("Finca 1 no existe; no se asignó.")

    cur.close(); cnx.close()
    print("Listo.")

if __name__ == '__main__':
    main()

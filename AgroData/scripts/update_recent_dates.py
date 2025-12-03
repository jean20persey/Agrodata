# Actualiza fechas a un rango reciente (último año hasta hoy)
# Ejecuta: .\.venv\Scripts\python AgroData\scripts\update_recent_dates.py

from datetime import date, timedelta
import random
import mysql.connector
import sys
from pathlib import Path

# Asegurar importación del módulo AgroData
sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import Config  # noqa

random.seed(42)


def clamp(d, min_d, max_d):
    if d < min_d:
        return min_d
    if d > max_d:
        return max_d
    return d


def main():
    today = date.today()
    min_date = today - timedelta(days=365)
    max_date = today - timedelta(days=1)

    cnx = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        autocommit=False,
    )
    cur = cnx.cursor()

    # Mover siembras al último año, distribuyendo fechas
    cur.execute("SELECT id_siembra, id_cultivo FROM siembra ORDER BY id_siembra")
    siembras = cur.fetchall()

    # Mapear cultivo -> dias_cosecha_estimado
    cur.execute("SELECT id_cultivo, COALESCE(dias_cosecha_estimado,90) FROM cultivo")
    dias_map = {row[0]: int(row[1]) for row in cur.fetchall()}

    for i, (id_siembra, id_cultivo) in enumerate(siembras):
        # Espaciar las fechas a lo largo del último año
        offset_days = 30 + int((i * 330) / max(1, len(siembras)))  # entre ~1 y 11 meses
        new_siembra = clamp(today - timedelta(days=offset_days), min_date, max_date)
        cur.execute("UPDATE siembra SET fecha_siembra=%s WHERE id_siembra=%s", (new_siembra, id_siembra))

        # Actualizar cosechas de esa siembra
        dias_estim = dias_map.get(id_cultivo, 90)
        # Variación +/- 15 días
        delta = dias_estim + random.randint(-15, 15)
        new_cosecha = clamp(new_siembra + timedelta(days=max(20, delta)), new_siembra + timedelta(days=20), max_date)
        cur.execute("UPDATE cosecha SET fecha_cosecha=%s WHERE id_siembra=%s", (new_cosecha, id_siembra))

        # Actualizar aplicaciones de insumo cercanas a la siembra
        app_date = clamp(new_siembra + timedelta(days=15), min_date, max_date)
        cur.execute("UPDATE aplicacion_insumo SET fecha_aplicacion=%s WHERE id_siembra=%s", (app_date, id_siembra))

    cnx.commit()
    cur.close(); cnx.close()
    print("Fechas actualizadas al último año.")


if __name__ == '__main__':
    main()

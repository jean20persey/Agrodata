# Diagnóstico de Punto de Equilibrio
# Ejecuta: .\.venv\Scripts\python AgroData\scripts\diagnose_pe.py

import mysql.connector
from AgroData.config import Config

def q1(cur, sql):
    cur.execute(sql)
    return cur.fetchone()

def main():
    cnx = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
    )
    cur = cnx.cursor()

    costo_fijo = q1(cur, "SELECT AVG(s.costo_siembra) FROM siembra s")[0]
    costo_apps, kg_totales = q1(cur, (
        "SELECT COALESCE(SUM(ai.costo_aplicacion),0), COALESCE(SUM(co.cantidad_kg),0) "
        "FROM siembra s LEFT JOIN aplicacion_insumo ai ON ai.id_siembra=s.id_siembra "
        "LEFT JOIN cosecha co ON co.id_siembra=s.id_siembra"
    ))
    precio_prom = q1(cur, "SELECT AVG(precio_venta_kg) FROM cosecha WHERE precio_venta_kg>0")[0]

    costo_variable = None
    if kg_totales and float(kg_totales) > 0:
        costo_variable = float(costo_apps)/float(kg_totales)

    print({
        'costo_fijo_avg': float(costo_fijo) if costo_fijo is not None else None,
        'costo_apps_sum': float(costo_apps or 0),
        'kg_totales_sum': float(kg_totales or 0),
        'costo_variable_por_kg': costo_variable,
        'precio_prom_kg': float(precio_prom) if precio_prom is not None else None,
    })

    cur.close(); cnx.close()

if __name__ == '__main__':
    main()

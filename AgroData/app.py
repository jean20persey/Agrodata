# PASO 8: Aplicación Flask principal
# Archivo: app.py

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from config import Config
from modulos import (
    EstadisticasAgricolas,
    ListaEnlazadaSiembras,
    ArbolBinarioCultivos,
    ColaPrioridadAlertas,
    MetodosNumericos,
    Algoritmos
)
from datetime import datetime, date

app = Flask(__name__)
app.config.from_object(Config)

# ==================== FUNCIONES DE CONEXIÓN ====================

def obtener_conexion():
    """Crea y retorna una conexión a MySQL"""
    try:
        conexion = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return conexion
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

def ejecutar_query(query, params=None, fetch=True):
    """Ejecuta una query y retorna resultados"""
    conexion = obtener_conexion()
    if not conexion:
        return None
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch:
            resultado = cursor.fetchall()
        else:
            conexion.commit()
            resultado = cursor.lastrowid
        
        cursor.close()
        conexion.close()
        return resultado
    except mysql.connector.Error as err:
        print(f"Error en query: {err}")
        return None

# ==================== RUTA PRINCIPAL (DASHBOARD) ====================

@app.route('/')
def index():
    """
    Dashboard principal con resumen de estadísticas
    Demuestra: Integración de todas las materias
    """
    conexion = obtener_conexion()
    if not conexion:
        flash('Error de conexión a la base de datos', 'danger')
        return render_template('index.html', error=True)
    
    # Estadísticas básicas
    stats = {
        'total_siembras': 0,
        'siembras_activas': 0,
        'total_cosechas': 0,
        'ingreso_total': 0
    }
    
    # Consultar datos básicos
    query_stats = """
        SELECT 
            COUNT(DISTINCT s.id_siembra) as total_siembras,
            SUM(CASE WHEN s.estado != 'cosechado' THEN 1 ELSE 0 END) as siembras_activas,
            COUNT(DISTINCT c.id_cosecha) as total_cosechas,
            COALESCE(SUM(c.ingreso_total), 0) as ingreso_total
        FROM siembra s
        LEFT JOIN cosecha c ON s.id_siembra = c.id_siembra
    """
    
    resultado = ejecutar_query(query_stats)
    if resultado:
        stats = resultado[0]
    
    # Generar alertas con cola de prioridad (Estructura de Datos)
    cola_alertas = ColaPrioridadAlertas()
    
    # Alertas: siembras próximas a cosechar
    query_alertas = """
        SELECT 
            s.id_siembra,
            c.nombre as cultivo,
            l.nombre as lote,
            s.fecha_siembra,
            cu.dias_cosecha_estimado,
            DATEDIFF(CURDATE(), s.fecha_siembra) as dias_transcurridos
        FROM siembra s
        JOIN cultivo cu ON s.id_cultivo = cu.id_cultivo
        JOIN lote l ON s.id_lote = l.id_lote
        LEFT JOIN cosecha c ON s.id_siembra = c.id_siembra
        WHERE s.estado IN ('sembrado', 'crecimiento') AND c.nombre IS NULL
    """
    
    siembras = ejecutar_query(query_alertas)
    alertas = []
    
    if siembras:
        for siembra in siembras:
            dias = siembra['dias_transcurridos']
            dias_estimados = siembra['dias_cosecha_estimado']
            
            if dias >= dias_estimados - 5:  # Falta 5 días o menos
                prioridad = 1  # Alta prioridad
                mensaje = f"🔴 URGENTE: {siembra['cultivo']} en {siembra['lote']} listo para cosechar"
            elif dias >= dias_estimados - 15:  # Falta 15 días o menos
                prioridad = 2  # Media prioridad
                mensaje = f"🟡 {siembra['cultivo']} en {siembra['lote']} próximo a cosechar"
            else:
                prioridad = 3  # Baja prioridad
                continue  # No mostrar alertas muy lejanas
            
            cola_alertas.agregar_alerta(prioridad, mensaje, siembra['id_siembra'])
    
    alertas = cola_alertas.obtener_todas()[:5]  # Top 5 alertas
    
    # Generar gráfico de rendimientos (Estadística II)
    estadisticas = EstadisticasAgricolas(conexion)
    grafico_rendimientos = estadisticas.generar_grafico_rendimientos()
    
    conexion.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         alertas=alertas,
                         grafico=grafico_rendimientos)

# ==================== RUTAS DE SIEMBRAS ====================

@app.route('/siembras')
def listar_siembras():
    """
    Lista todas las siembras usando estructura de datos
    Demuestra: Lista Enlazada
    """
    query = """
        SELECT 
            s.id_siembra,
            l.nombre as lote,
            c.nombre as cultivo,
            s.fecha_siembra,
            s.area_sembrada,
            s.estado
        FROM siembra s
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN cultivo c ON s.id_cultivo = c.id_cultivo
        ORDER BY s.fecha_siembra DESC
    """
    
    siembras = ejecutar_query(query)
    
    # Almacenar en lista enlazada (Estructura de Datos)
    lista_siembras = ListaEnlazadaSiembras()
    if siembras:
        for siembra in siembras:
            lista_siembras.agregar_siembra(siembra)
    
    # Obtener datos de lotes y cultivos para el formulario
    lotes = ejecutar_query("SELECT * FROM lote WHERE estado = 'activo'")
    cultivos = ejecutar_query("SELECT * FROM cultivo")
    
    return render_template('siembras.html', 
                         siembras=lista_siembras.obtener_todas(),
                         lotes=lotes,
                         cultivos=cultivos)

@app.route('/siembras/agregar', methods=['POST'])
def agregar_siembra():
    """Registra una nueva siembra"""
    try:
        id_lote = request.form['id_lote']
        id_cultivo = request.form['id_cultivo']
        fecha_siembra = request.form['fecha_siembra']
        area_sembrada = request.form['area_sembrada']
        cantidad_semilla = request.form.get('cantidad_semilla', 0)
        costo_siembra = request.form.get('costo_siembra', 0)
        
        query = """
            INSERT INTO siembra 
            (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        resultado = ejecutar_query(query, 
                                  (id_lote, id_cultivo, fecha_siembra, 
                                   area_sembrada, cantidad_semilla, costo_siembra),
                                  fetch=False)
        
        if resultado:
            flash('Siembra registrada exitosamente', 'success')
        else:
            flash('Error al registrar siembra', 'danger')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('listar_siembras'))

@app.route('/siembras/buscar', methods=['POST'])
def buscar_siembra():
    """
    Busca siembra usando algoritmos de búsqueda
    Demuestra: Búsqueda Lineal vs Binaria
    """
    id_buscar = int(request.form.get('id_siembra', 0))
    
    # Obtener todas las siembras
    siembras = ejecutar_query("SELECT * FROM siembra")
    
    if not siembras:
        return jsonify({'error': 'No hay siembras registradas'})
    
    # Comparar algoritmos (Análisis de Algoritmos)
    resultado = Algoritmos.comparar_algoritmos_busqueda(siembras, id_buscar)
    
    return jsonify({
        'encontrado': resultado['lineal']['encontrado'],
        'tiempo_lineal': f"{resultado['lineal']['tiempo']:.6f} seg",
        'tiempo_binaria': f"{resultado['binaria']['tiempo']:.6f} seg",
        'comparaciones_binaria': resultado['binaria']['comparaciones'],
        'mejora': f"{resultado['mejora']:.2f}x más rápido"
    })

# ==================== RUTAS DE COSECHAS ====================

@app.route('/cosechas')
def listar_cosechas():
    """Lista todas las cosechas registradas"""
    query = """
        SELECT 
            co.id_cosecha,
            c.nombre as cultivo,
            l.nombre as lote,
            s.fecha_siembra,
            co.fecha_cosecha,
            co.cantidad_kg,
            s.area_sembrada,
            co.cantidad_kg / s.area_sembrada as rendimiento,
            co.ingreso_total
        FROM cosecha co
        JOIN siembra s ON co.id_siembra = s.id_siembra
        JOIN cultivo c ON s.id_cultivo = c.id_cultivo
        JOIN lote l ON s.id_lote = l.id_lote
        ORDER BY co.fecha_cosecha DESC
    """
    
    cosechas = ejecutar_query(query)
    
    # Obtener siembras sin cosechar para el formulario
    siembras_disponibles = ejecutar_query("""
        SELECT 
            s.id_siembra,
            CONCAT(c.nombre, ' - Lote ', l.nombre, ' (', s.fecha_siembra, ')') as descripcion
        FROM siembra s
        JOIN cultivo c ON s.id_cultivo = c.id_cultivo
        JOIN lote l ON s.id_lote = l.id_lote
        LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
        WHERE s.estado != 'cosechado' AND co.id_cosecha IS NULL
    """)
    
    return render_template('cosechas.html', 
                         cosechas=cosechas,
                         siembras=siembras_disponibles)

@app.route('/cosechas/agregar', methods=['POST'])
def agregar_cosecha():
    """Registra una nueva cosecha"""
    try:
        id_siembra = request.form['id_siembra']
        fecha_cosecha = request.form['fecha_cosecha']
        cantidad_kg = float(request.form['cantidad_kg'])
        calidad = request.form.get('calidad_porcentaje', 100)
        precio_kg = float(request.form.get('precio_venta_kg', 0))
        ingreso_total = cantidad_kg * precio_kg
        observaciones = request.form.get('observaciones', '')
        
        query = """
            INSERT INTO cosecha 
            (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, 
             precio_venta_kg, ingreso_total, observaciones)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        resultado = ejecutar_query(query,
                                  (id_siembra, fecha_cosecha, cantidad_kg, 
                                   calidad, precio_kg, ingreso_total, observaciones),
                                  fetch=False)
        
        if resultado:
            # Actualizar estado de siembra
            ejecutar_query("UPDATE siembra SET estado = 'cosechado' WHERE id_siembra = %s",
                         (id_siembra,), fetch=False)
            flash('Cosecha registrada exitosamente', 'success')
        else:
            flash('Error al registrar cosecha', 'danger')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('listar_cosechas'))

# ==================== RUTAS DE INSUMOS ====================

@app.route('/insumos')
def listar_insumos():
    """Lista inventario de insumos"""
    query = """
        SELECT 
            i.*,
            f.nombre as finca
        FROM insumo i
        JOIN finca f ON i.id_finca = f.id_finca
        ORDER BY i.cantidad_disponible ASC
    """
    
    insumos = ejecutar_query(query)
    
    # Alertas de stock bajo
    alertas_stock = []
    if insumos:
        for insumo in insumos:
            if insumo['cantidad_disponible'] < 50:  # Umbral de 50 unidades
                alertas_stock.append({
                    'nombre': insumo['nombre'],
                    'cantidad': insumo['cantidad_disponible'],
                    'tipo': insumo['tipo']
                })
    
    fincas = ejecutar_query("SELECT * FROM finca")
    
    return render_template('insumos.html', 
                         insumos=insumos,
                         alertas_stock=alertas_stock,
                         fincas=fincas)

@app.route('/insumos/agregar', methods=['POST'])
def agregar_insumo():
    """Registra un nuevo insumo"""
    try:
        id_finca = request.form['id_finca']
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        unidad = request.form['unidad_medida']
        cantidad = request.form['cantidad_disponible']
        costo = request.form.get('costo_unitario', 0)
        proveedor = request.form.get('proveedor', '')
        
        query = """
            INSERT INTO insumo 
            (id_finca, nombre, tipo, unidad_medida, cantidad_disponible, 
             costo_unitario, fecha_compra, proveedor)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), %s)
        """
        
        resultado = ejecutar_query(query,
                                  (id_finca, nombre, tipo, unidad, cantidad, 
                                   costo, proveedor),
                                  fetch=False)
        
        if resultado:
            flash('Insumo agregado exitosamente', 'success')
        else:
            flash('Error al agregar insumo', 'danger')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    
    return redirect(url_for('listar_insumos'))

# ==================== RUTAS DE REPORTES ====================

@app.route('/reportes')
def reportes():
    """
    Página de reportes y análisis
    Demuestra: Estadística II, Métodos Numéricos, Algoritmos
    """
    conexion = obtener_conexion()
    if not conexion:
        flash('Error de conexión', 'danger')
        return render_template('reportes.html', error=True)
    
    # 1. ESTADÍSTICAS DESCRIPTIVAS (Estadística II)
    estadisticas = EstadisticasAgricolas(conexion)
    stats_desc = estadisticas.estadisticas_descriptivas()
    
    # 2. CORRELACIÓN (Estadística II)
    correlacion = estadisticas.correlacion_insumo_rendimiento()
    grafico_correlacion = estadisticas.generar_grafico_correlacion()
    
    # 3. RANKING DE LOTES (Algoritmos - QuickSort)
    query_lotes = """
        SELECT 
            l.nombre as lote,
            AVG(co.cantidad_kg / s.area_sembrada) as rendimiento,
            COUNT(s.id_siembra) as total_siembras
        FROM lote l
        JOIN siembra s ON l.id_lote = s.id_lote
        JOIN cosecha co ON s.id_siembra = co.id_siembra
        GROUP BY l.id_lote
        HAVING COUNT(s.id_siembra) > 0
    """
    
    lotes_data = ejecutar_query(query_lotes)
    ranking = []
    if lotes_data:
        ranking = Algoritmos.ranking_lotes(lotes_data)
    
    # 4. PROYECCIÓN DE PRODUCCIÓN (Métodos Numéricos - Interpolación)
    proyeccion = None
    query_historico = """
        SELECT 
            DATEDIFF(co.fecha_cosecha, s.fecha_siembra) as dia,
            co.cantidad_kg as kg
        FROM cosecha co
        JOIN siembra s ON co.id_siembra = s.id_siembra
        ORDER BY s.fecha_siembra
        LIMIT 10
    """
    
    datos_historicos = ejecutar_query(query_historico)
    if datos_historicos and len(datos_historicos) >= 3:
        # Proyectar para los próximos 30, 60, 90 días
        proyeccion = MetodosNumericos.proyectar_produccion(
            datos_historicos, 
            [30, 60, 90, 120]
        )
    
    # 5. PUNTO DE EQUILIBRIO (Métodos Numéricos - Bisección)
    costo_promedio = ejecutar_query("""
        SELECT 
            AVG(s.costo_siembra) as costo_fijo,
            AVG(ai.costo_aplicacion / ai.cantidad_aplicada) as costo_variable
        FROM siembra s
        LEFT JOIN aplicacion_insumo ai ON s.id_siembra = ai.id_siembra
    """)
    
    punto_equilibrio = None
    if costo_promedio is not None:
        costo_fijo = costo_promedio[0].get('costo_fijo') if costo_promedio else None
        costo_variable = costo_promedio[0].get('costo_variable') if costo_promedio else None
        
        if costo_fijo is not None:
            precio_venta_promedio = ejecutar_query("""
                SELECT AVG(precio_venta_kg) as precio FROM cosecha WHERE precio_venta_kg > 0
            """)
            precio_prom = precio_venta_promedio[0].get('precio') if precio_venta_promedio else None
            
            if precio_prom is not None and float(precio_prom) > 0:
                punto_eq = MetodosNumericos.calcular_punto_equilibrio(
                    float(costo_fijo or 0),
                    float(costo_variable or 0),
                    float(precio_prom)
                )
                if punto_eq is not None:
                    punto_equilibrio = round(punto_eq, 2)
    
    conexion.close()
    
    return render_template('reportes.html',
                         stats=stats_desc,
                         correlacion=correlacion,
                         grafico_correlacion=grafico_correlacion,
                         ranking=ranking,
                         proyeccion=proyeccion,
                         punto_equilibrio=punto_equilibrio)

# ==================== RUTA DE DEMOSTRACIÓN ====================

@app.route('/demo/estructuras')
def demo_estructuras():
    """
    Demostración visual de estructuras de datos
    Para presentaciones y explicaciones
    """
    # Árbol binario de búsqueda
    arbol = ArbolBinarioCultivos()
    
    query = """
        SELECT 
            c.nombre as cultivo,
            AVG(co.cantidad_kg / s.area_sembrada) as rendimiento
        FROM cultivo c
        JOIN siembra s ON c.id_cultivo = s.id_cultivo
        JOIN cosecha co ON s.id_siembra = co.id_siembra
        GROUP BY c.id_cultivo
    """
    
    cultivos = ejecutar_query(query)
    
    if cultivos:
        for cultivo in cultivos:
            arbol.insertar(cultivo['cultivo'], cultivo['rendimiento'])
    
    arbol_ordenado = arbol.recorrido_inorden()
    
    return jsonify({
        'estructura': 'Árbol Binario de Búsqueda',
        'datos': arbol_ordenado,
        'descripcion': 'Cultivos organizados por rendimiento (kg/ha)'
    })

# ==================== EJECUTAR APLICACIÓN ====================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
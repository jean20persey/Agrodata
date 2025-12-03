# PASO 8: Aplicación Flask principal
# Archivo: app.py

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager, login_user, logout_user, login_required,
    current_user, UserMixin
)
from passlib.hash import pbkdf2_sha256

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

# ==================== AUTENTICACIÓN ====================
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'


class User(UserMixin):
    def __init__(self, id_usuario, email, nombre=None):
        self.id = id_usuario
        self.email = email
        self.nombre = nombre

    @staticmethod
    def get_by_id(user_id):
        row = ejecutar_query(
            "SELECT id_usuario, email, nombre FROM usuario WHERE id_usuario = %s",
            (user_id,)
        )
        if row:
            r = row[0]
            return User(r['id_usuario'], r['email'], r.get('nombre'))
        return None

    @staticmethod
    def get_by_email(email):
        row = ejecutar_query(
            "SELECT id_usuario, email, nombre, password_hash FROM usuario WHERE email = %s",
            (email,)
        )
        return row[0] if row else None


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)


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
@login_required
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
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        LEFT JOIN cosecha c ON s.id_siembra = c.id_siembra
        WHERE f.user_id = %s
    """
    
    resultado = ejecutar_query(query_stats, (current_user.id,))
    if resultado:
        stats = resultado[0]
    
    # Generar alertas con cola de prioridad (Estructura de Datos)
    cola_alertas = ColaPrioridadAlertas()
    
    # Alertas: siembras próximas a cosechar
    query_alertas = """
        SELECT 
            s.id_siembra,
            cu.nombre as cultivo,
            l.nombre as lote,
            s.fecha_siembra,
            cu.dias_cosecha_estimado,
            DATEDIFF(CURDATE(), s.fecha_siembra) as dias_transcurridos
        FROM siembra s
        JOIN cultivo cu ON s.id_cultivo = cu.id_cultivo
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
        WHERE f.user_id = %s AND s.estado IN ('sembrado', 'crecimiento') AND co.id_cosecha IS NULL
    """
    
    siembras = ejecutar_query(query_alertas, (current_user.id,))
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
    grafico_rendimientos = estadisticas.generar_grafico_rendimientos(user_id=current_user.id)
    
    conexion.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         alertas=alertas,
                         grafico=grafico_rendimientos)

# ==================== RUTAS DE SIEMBRAS ====================

@app.route('/siembras')
@login_required
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
        JOIN finca f ON l.id_finca = f.id_finca
        JOIN cultivo c ON s.id_cultivo = c.id_cultivo
        WHERE f.user_id = %s
        ORDER BY s.fecha_siembra DESC
    """
    
    siembras = ejecutar_query(query, (current_user.id,))
    
    # Almacenar en lista enlazada (Estructura de Datos)
    lista_siembras = ListaEnlazadaSiembras()
    if siembras:
        for siembra in siembras:
            lista_siembras.agregar_siembra(siembra)
    
    # Obtener datos de lotes y cultivos para el formulario
    lotes = ejecutar_query(
        """
        SELECT l.* FROM lote l
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE l.estado = 'activo' AND f.user_id = %s
        ORDER BY l.nombre
        """,
        (current_user.id,)
    )
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
    siembras = ejecutar_query(
        """
        SELECT s.* FROM siembra s
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
        """,
        (current_user.id,)
    )
    
    if not siembras:
        return jsonify({'error': 'No hay siembras registradas'})
    
    # Comparar algoritmos (Análisis de Algoritmos)
    resultado = Algoritmos.comparar_algoritmos_busqueda(siembras, id_buscar)

    detalle = None
    if resultado['lineal']['encontrado']:
        for s in siembras:
            if int(s.get('id_siembra')) == id_buscar:
                detalle = {
                    'id_siembra': s.get('id_siembra'),
                    'lote': s.get('lote'),
                    'cultivo': s.get('cultivo'),
                    'fecha_siembra': s.get('fecha_siembra'),
                    'area_sembrada': float(s.get('area_sembrada') or 0),
                    'estado': s.get('estado'),
                }
                break
    
    return jsonify({
        'encontrado': resultado['lineal']['encontrado'],
        'tiempo_lineal': f"{resultado['lineal']['tiempo']:.6f} seg",
        'tiempo_binaria': f"{resultado['binaria']['tiempo']:.6f} seg",
        'comparaciones_binaria': resultado['binaria']['comparaciones'],
        'mejora': f"{resultado['mejora']:.2f}x más rápido",
        'siembra': detalle
    })

# ==================== RUTAS DE COSECHAS ====================

@app.route('/cosechas')
@login_required
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
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
        ORDER BY co.fecha_cosecha DESC
    """
    
    cosechas = ejecutar_query(query, (current_user.id,))
    
    # Obtener siembras sin cosechar para el formulario
    siembras_disponibles = ejecutar_query(
        """
        SELECT 
            s.id_siembra,
            CONCAT(c.nombre, ' - Lote ', l.nombre, ' (', s.fecha_siembra, ')') as descripcion
        FROM siembra s
        JOIN cultivo c ON s.id_cultivo = c.id_cultivo
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
        WHERE f.user_id = %s AND s.estado != 'cosechado' AND co.id_cosecha IS NULL
    """,
        (current_user.id,)
    )
    
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
@login_required
def listar_insumos():
    """Lista inventario de insumos"""
    query = """
        SELECT 
            i.*,
            f.nombre as finca
        FROM insumo i
        JOIN finca f ON i.id_finca = f.id_finca
        WHERE f.user_id = %s
        ORDER BY i.cantidad_disponible ASC
    """
    
    insumos = ejecutar_query(query, (current_user.id,))
    
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
    
    fincas = ejecutar_query("SELECT * FROM finca WHERE user_id = %s", (current_user.id,))
    
    return render_template('insumos.html', 
                         insumos=insumos,
                         alertas_stock=alertas_stock,
                         fincas=fincas)

# ==================== RUTAS DE FINCAS ====================

@app.route('/fincas')
@login_required
def listar_fincas():
    fincas = ejecutar_query(
        "SELECT * FROM finca WHERE user_id = %s ORDER BY nombre",
        (current_user.id,)
    )
    return render_template('fincas.html', fincas=fincas)


@app.route('/fincas/agregar', methods=['POST'])
@login_required
def agregar_finca():
    try:
        nombre = request.form['nombre']
        ubicacion = request.form.get('ubicacion', '')
        area = request.form.get('area_total_hectareas', 0)
        propietario = request.form.get('propietario', current_user.nombre or current_user.email)
        telefono = request.form.get('telefono', '')
        email = request.form.get('email', '')
        query = (
            "INSERT INTO finca (nombre, ubicacion, area_total_hectareas, propietario, telefono, email, user_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)"
        )
        ejecutar_query(query, (nombre, ubicacion, area, propietario, telefono, email, current_user.id), fetch=False)
        flash('Finca creada', 'success')
    except Exception as e:
        flash(f'Error al crear finca: {str(e)}', 'danger')
    return redirect(url_for('listar_fincas'))

# ==================== RUTAS DE LOTES ====================

@app.route('/lotes')
@login_required
def listar_lotes():
    lotes = ejecutar_query(
        """
        SELECT l.*, f.nombre AS finca
        FROM lote l
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
        ORDER BY f.nombre, l.nombre
        """,
        (current_user.id,)
    )
    fincas = ejecutar_query(
        "SELECT id_finca, nombre FROM finca WHERE user_id = %s ORDER BY nombre",
        (current_user.id,)
    )
    return render_template('lotes.html', lotes=lotes, fincas=fincas)


@app.route('/lotes/agregar', methods=['POST'])
@login_required
def agregar_lote():
    try:
        id_finca = request.form['id_finca']
        nombre = request.form['nombre']
        area = request.form.get('area_hectareas', 0)
        tipo_suelo = request.form.get('tipo_suelo', '')
        ph_suelo = request.form.get('ph_suelo') or None
        ubicacion_gps = request.form.get('ubicacion_gps', '')
        estado = request.form.get('estado', 'activo')

        # Verificar que la finca pertenezca al usuario actual
        ver = ejecutar_query(
            "SELECT id_finca FROM finca WHERE id_finca=%s AND user_id=%s",
            (id_finca, current_user.id)
        )
        if not ver:
            flash('No puedes agregar lotes a una finca que no es tuya', 'danger')
            return redirect(url_for('listar_lotes'))

        ejecutar_query(
            """
            INSERT INTO lote (id_finca, nombre, area_hectareas, tipo_suelo, ph_suelo, ubicacion_gps, estado)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (id_finca, nombre, area, tipo_suelo, ph_suelo, ubicacion_gps, estado),
            fetch=False
        )
        flash('Lote creado', 'success')
    except Exception as e:
        flash(f'Error al crear lote: {str(e)}', 'danger')
    return redirect(url_for('listar_lotes'))

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
@login_required
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
    stats_desc = estadisticas.estadisticas_descriptivas(user_id=current_user.id)
    
    # 2. CORRELACIÓN (Estadística II)
    correlacion = estadisticas.correlacion_insumo_rendimiento(user_id=current_user.id)
    grafico_correlacion = estadisticas.generar_grafico_correlacion(user_id=current_user.id)
    
    # 3. RANKING DE LOTES (Algoritmos - QuickSort)
    query_lotes = """
        SELECT 
            l.nombre as lote,
            AVG(co.cantidad_kg / s.area_sembrada) as rendimiento,
            COUNT(s.id_siembra) as total_siembras
        FROM lote l
        JOIN siembra s ON l.id_lote = s.id_lote
        JOIN cosecha co ON s.id_siembra = co.id_siembra
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
        GROUP BY l.id_lote
        HAVING COUNT(s.id_siembra) > 0
    """
    
    lotes_data = ejecutar_query(query_lotes, (current_user.id,))
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
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
        ORDER BY s.fecha_siembra
        LIMIT 10
    """
    
    datos_historicos = ejecutar_query(query_historico, (current_user.id,))
    if datos_historicos and len(datos_historicos) >= 3:
        # Proyectar para los próximos 30, 60, 90 días
        proyeccion = MetodosNumericos.proyectar_produccion(
            datos_historicos, 
            [30, 60, 90, 120]
        )
    
    # 5. PUNTO DE EQUILIBRIO (Métodos Numéricos - Bisección)
    # Costo fijo: promedio de costo de siembra
    costo_fijo_row = ejecutar_query("""
        SELECT AVG(s.costo_siembra) as costo_fijo
        FROM siembra s
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        WHERE f.user_id = %s
    """, (current_user.id,))
    # Costo variable estimado por kg producido: suma de costos de aplicación / suma de kg cosechados
    costo_var_row = ejecutar_query("""
        SELECT 
            COALESCE(SUM(ai.costo_aplicacion), 0) AS costo_apps,
            COALESCE(SUM(co.cantidad_kg), 0) AS kg_totales
        FROM siembra s
        JOIN lote l ON s.id_lote = l.id_lote
        JOIN finca f ON l.id_finca = f.id_finca
        LEFT JOIN aplicacion_insumo ai ON ai.id_siembra = s.id_siembra
        LEFT JOIN cosecha co ON co.id_siembra = s.id_siembra
        WHERE f.user_id = %s
    """, (current_user.id,))
    
    punto_equilibrio = None
    costo_fijo = costo_fijo_row[0].get('costo_fijo') if costo_fijo_row else None
    costo_apps = costo_var_row[0].get('costo_apps') if costo_var_row else 0
    kg_totales = costo_var_row[0].get('kg_totales') if costo_var_row else 0
    costo_variable = None
    if kg_totales and float(kg_totales) > 0:
        costo_variable = float(costo_apps) / float(kg_totales)
    
    if costo_fijo is not None:
        precio_venta_promedio = ejecutar_query("""
            SELECT AVG(co.precio_venta_kg) as precio 
            FROM cosecha co
            JOIN siembra s ON co.id_siembra = s.id_siembra
            JOIN lote l ON s.id_lote = l.id_lote
            JOIN finca f ON l.id_finca = f.id_finca
            WHERE co.precio_venta_kg > 0 AND f.user_id = %s
        """, (current_user.id,))
        precio_prom = precio_venta_promedio[0].get('precio') if precio_venta_promedio else None
        if precio_prom is not None and float(precio_prom) > 0 and costo_variable is not None:
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
@login_required
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

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        row = User.get_by_email(email)
        if row and pbkdf2_sha256.verify(password, row['password_hash']):
            user = User(row['id_usuario'], row['email'], row.get('nombre'))
            login_user(user)
            flash('Bienvenido', 'success')
            return redirect(url_for('index'))
        flash('Credenciales inválidas', 'danger')
    return render_template('auth_login.html')


@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        nombre = request.form.get('nombre', '').strip()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        if password != password2:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth_register.html')
        if User.get_by_email(email):
            flash('El email ya está registrado', 'warning')
            return render_template('auth_register.html')
        pwd_hash = pbkdf2_sha256.hash(password)
        ejecutar_query(
            "INSERT INTO usuario (email, password_hash, nombre) VALUES (%s, %s, %s)",
            (email, pwd_hash, nombre), fetch=False
        )
        flash('Registro exitoso. Inicia sesión.', 'success')
        return redirect(url_for('login'))
    return render_template('auth_register.html')


@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('login'))

# ==================== EJECUTAR APLICACIÓN ====================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
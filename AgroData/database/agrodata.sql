-- PASO 6: Creación de Base de Datos MySQL
-- Archivo: database/agrodata.sql
-- Sistema de Gestión Agrícola - AgroData

-- Crear base de datos
CREATE DATABASE IF NOT EXISTS agrodata;
USE agrodata;

-- Eliminar tablas si existen (en orden inverso por dependencias)
DROP TABLE IF EXISTS aplicacion_insumo;
DROP TABLE IF EXISTS cosecha;
DROP TABLE IF EXISTS siembra;
DROP TABLE IF EXISTS insumo;
DROP TABLE IF EXISTS cultivo;
DROP TABLE IF EXISTS lote;
DROP TABLE IF EXISTS finca;

-- ==================== TABLA: FINCA ====================
CREATE TABLE finca (
    id_finca INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(200),
    area_total_hectareas DECIMAL(10,2),
    propietario VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100),
    fecha_registro DATE DEFAULT (CURRENT_DATE),
    estado ENUM('activa', 'inactiva') DEFAULT 'activa'
);

-- ==================== TABLA: LOTE ====================
CREATE TABLE lote (
    id_lote INT PRIMARY KEY AUTO_INCREMENT,
    id_finca INT NOT NULL,
    nombre VARCHAR(50) NOT NULL,
    area_hectareas DECIMAL(10,2) NOT NULL,
    tipo_suelo VARCHAR(50),
    ph_suelo DECIMAL(3,1),
    ubicacion_gps VARCHAR(100),
    estado ENUM('activo', 'en_descanso', 'inactivo') DEFAULT 'activo',
    FOREIGN KEY (id_finca) REFERENCES finca(id_finca) ON DELETE CASCADE
);

-- ==================== TABLA: CULTIVO ====================
CREATE TABLE cultivo (
    id_cultivo INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    variedad VARCHAR(100),
    tipo ENUM('cereal', 'legumbre', 'hortaliza', 'fruta', 'otro') DEFAULT 'otro',
    dias_cosecha_estimado INT,
    rendimiento_esperado_kg_ha DECIMAL(10,2),
    precio_referencia_kg DECIMAL(10,2),
    descripcion TEXT
);

-- ==================== TABLA: SIEMBRA ====================
CREATE TABLE siembra (
    id_siembra INT PRIMARY KEY AUTO_INCREMENT,
    id_lote INT NOT NULL,
    id_cultivo INT NOT NULL,
    fecha_siembra DATE NOT NULL,
    area_sembrada DECIMAL(10,2) NOT NULL,
    cantidad_semilla DECIMAL(10,2),
    costo_siembra DECIMAL(10,2),
    estado ENUM('sembrado', 'crecimiento', 'floracion', 'cosechado', 'perdido') DEFAULT 'sembrado',
    observaciones TEXT,
    FOREIGN KEY (id_lote) REFERENCES lote(id_lote) ON DELETE CASCADE,
    FOREIGN KEY (id_cultivo) REFERENCES cultivo(id_cultivo) ON DELETE CASCADE
);

-- ==================== TABLA: COSECHA ====================
CREATE TABLE cosecha (
    id_cosecha INT PRIMARY KEY AUTO_INCREMENT,
    id_siembra INT NOT NULL,
    fecha_cosecha DATE NOT NULL,
    cantidad_kg DECIMAL(10,2) NOT NULL,
    calidad_porcentaje DECIMAL(5,2) DEFAULT 100.00,
    precio_venta_kg DECIMAL(10,2),
    ingreso_total DECIMAL(12,2),
    observaciones TEXT,
    FOREIGN KEY (id_siembra) REFERENCES siembra(id_siembra) ON DELETE CASCADE
);

-- ==================== TABLA: INSUMO ====================
CREATE TABLE insumo (
    id_insumo INT PRIMARY KEY AUTO_INCREMENT,
    id_finca INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tipo ENUM('fertilizante', 'pesticida', 'herbicida', 'semilla', 'otro') NOT NULL,
    unidad_medida VARCHAR(20),
    cantidad_disponible DECIMAL(10,2) DEFAULT 0,
    costo_unitario DECIMAL(10,2),
    fecha_compra DATE,
    proveedor VARCHAR(100),
    FOREIGN KEY (id_finca) REFERENCES finca(id_finca) ON DELETE CASCADE
);

-- ==================== TABLA: APLICACION_INSUMO ====================
CREATE TABLE aplicacion_insumo (
    id_aplicacion INT PRIMARY KEY AUTO_INCREMENT,
    id_siembra INT NOT NULL,
    id_insumo INT NOT NULL,
    fecha_aplicacion DATE NOT NULL,
    cantidad_aplicada DECIMAL(10,2) NOT NULL,
    costo_aplicacion DECIMAL(10,2),
    metodo_aplicacion VARCHAR(100),
    responsable VARCHAR(100),
    observaciones TEXT,
    FOREIGN KEY (id_siembra) REFERENCES siembra(id_siembra) ON DELETE CASCADE,
    FOREIGN KEY (id_insumo) REFERENCES insumo(id_insumo) ON DELETE CASCADE
);

-- ==================== DATOS DE EJEMPLO ====================

-- Insertar finca de ejemplo
INSERT INTO finca (nombre, ubicacion, area_total_hectareas, propietario, telefono) VALUES
('Finca El Progreso', 'Valle Central, Km 45', 50.00, 'Juan Pérez', '555-1234');

-- Insertar lotes
INSERT INTO lote (id_finca, nombre, area_hectareas, tipo_suelo, ph_suelo) VALUES
(1, 'Lote A', 10.00, 'Franco arcilloso', 6.5),
(1, 'Lote B', 15.00, 'Franco arenoso', 6.8),
(1, 'Lote C', 12.00, 'Arcilloso', 7.0),
(1, 'Lote D', 13.00, 'Franco', 6.7);

-- Insertar cultivos
INSERT INTO cultivo (nombre, variedad, tipo, dias_cosecha_estimado, rendimiento_esperado_kg_ha, precio_referencia_kg) VALUES
('Maíz', 'Híbrido DK-7088', 'cereal', 120, 8000.00, 0.45),
('Frijol', 'Negro Jamapa', 'legumbre', 90, 1500.00, 1.20),
('Tomate', 'Saladette', 'hortaliza', 75, 50000.00, 0.80),
('Papa', 'Alpha', 'hortaliza', 100, 25000.00, 0.60),
('Trigo', 'Cristalino', 'cereal', 150, 4500.00, 0.35);

-- Insertar siembras de ejemplo
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado) VALUES
(1, 1, '2024-03-15', 10.00, 25.00, 1500.00, 'crecimiento'),
(2, 2, '2024-04-01', 8.00, 120.00, 800.00, 'crecimiento'),
(3, 3, '2024-05-10', 5.00, 2.50, 2500.00, 'floracion'),
(4, 4, '2024-02-20', 12.00, 1800.00, 3000.00, 'cosechado'),
(1, 5, '2024-01-10', 10.00, 180.00, 1200.00, 'cosechado');

-- Insertar cosechas de ejemplo
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total) VALUES
(4, '2024-05-30', 28500.00, 95.00, 0.60, 17100.00),
(5, '2024-06-10', 42000.00, 92.00, 0.35, 14700.00);

-- Insertar insumos
INSERT INTO insumo (id_finca, nombre, tipo, unidad_medida, cantidad_disponible, costo_unitario, fecha_compra, proveedor) VALUES
(1, 'Urea 46%', 'fertilizante', 'kg', 500.00, 0.85, '2024-01-15', 'AgroInsumos SA'),
(1, 'Fosfato Diamónico', 'fertilizante', 'kg', 300.00, 1.20, '2024-01-15', 'AgroInsumos SA'),
(1, 'Glifosato', 'herbicida', 'litro', 50.00, 12.50, '2024-02-01', 'Químicos Agrícolas'),
(1, 'Insecticida Cipermetrina', 'pesticida', 'litro', 30.00, 18.00, '2024-02-10', 'Químicos Agrícolas');

-- Insertar aplicaciones de insumos
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion) VALUES
(1, 1, '2024-03-25', 250.00, 212.50, 'Aplicación al voleo'),
(1, 2, '2024-03-25', 150.00, 180.00, 'Aplicación al voleo'),
(2, 1, '2024-04-10', 180.00, 153.00, 'Aplicación localizada'),
(3, 4, '2024-05-20', 5.00, 90.00, 'Fumigación foliar');

-- ==================== ÍNDICES PARA OPTIMIZACIÓN ====================
CREATE INDEX idx_siembra_fecha ON siembra(fecha_siembra);
CREATE INDEX idx_cosecha_fecha ON cosecha(fecha_cosecha);
CREATE INDEX idx_lote_finca ON lote(id_finca);
CREATE INDEX idx_siembra_estado ON siembra(estado);

-- ==================== VISTAS ÚTILES ====================

-- Vista: Resumen de siembras activas
CREATE OR REPLACE VIEW vista_siembras_activas AS
SELECT 
    s.id_siembra,
    f.nombre as finca,
    l.nombre as lote,
    c.nombre as cultivo,
    c.variedad,
    s.fecha_siembra,
    s.area_sembrada,
    s.estado,
    DATEDIFF(CURDATE(), s.fecha_siembra) as dias_transcurridos,
    c.dias_cosecha_estimado,
    c.dias_cosecha_estimado - DATEDIFF(CURDATE(), s.fecha_siembra) as dias_restantes
FROM siembra s
JOIN lote l ON s.id_lote = l.id_lote
JOIN finca f ON l.id_finca = f.id_finca
JOIN cultivo c ON s.id_cultivo = c.id_cultivo
WHERE s.estado IN ('sembrado', 'crecimiento', 'floracion');

-- Vista: Rendimiento por cultivo
CREATE OR REPLACE VIEW vista_rendimiento_cultivos AS
SELECT 
    c.nombre as cultivo,
    c.variedad,
    COUNT(co.id_cosecha) as total_cosechas,
    SUM(s.area_sembrada) as area_total,
    SUM(co.cantidad_kg) as produccion_total,
    AVG(co.cantidad_kg / s.area_sembrada) as rendimiento_promedio,
    SUM(co.ingreso_total) as ingreso_total
FROM cultivo c
JOIN siembra s ON c.id_cultivo = s.id_cultivo
JOIN cosecha co ON s.id_siembra = co.id_siembra
GROUP BY c.id_cultivo;

-- Vista: Inventario de insumos
CREATE OR REPLACE VIEW vista_inventario_insumos AS
SELECT 
    i.id_insumo,
    f.nombre as finca,
    i.nombre as insumo,
    i.tipo,
    i.cantidad_disponible,
    i.unidad_medida,
    i.costo_unitario,
    i.cantidad_disponible * i.costo_unitario as valor_inventario,
    CASE 
        WHEN i.cantidad_disponible < 50 THEN 'Bajo'
        WHEN i.cantidad_disponible < 200 THEN 'Medio'
        ELSE 'Suficiente'
    END as nivel_stock
FROM insumo i
JOIN finca f ON i.id_finca = f.id_finca;

-- ==================== PROCEDIMIENTOS ALMACENADOS ====================

DELIMITER //

-- Procedimiento: Calcular rendimiento de una siembra
CREATE PROCEDURE calcular_rendimiento_siembra(IN p_id_siembra INT)
BEGIN
    SELECT 
        s.id_siembra,
        c.nombre as cultivo,
        s.area_sembrada,
        co.cantidad_kg,
        co.cantidad_kg / s.area_sembrada as rendimiento_kg_ha,
        s.costo_siembra,
        co.ingreso_total,
        co.ingreso_total - s.costo_siembra as utilidad
    FROM siembra s
    JOIN cultivo c ON s.id_cultivo = c.id_cultivo
    LEFT JOIN cosecha co ON s.id_siembra = co.id_siembra
    WHERE s.id_siembra = p_id_siembra;
END //

DELIMITER ;

-- ==================== COMENTARIOS FINALES ====================
-- Base de datos creada exitosamente
-- Incluye:
-- - 7 tablas principales con relaciones
-- - Datos de ejemplo para pruebas
-- - Índices para optimización
-- - 3 vistas útiles
-- - 1 procedimiento almacenado

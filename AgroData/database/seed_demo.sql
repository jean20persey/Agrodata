-- Seeds adicionales para demo de Proyección y Punto de Equilibrio
USE agrodata;

-- Nueva siembra ya cosechada para garantizar >= 3 cosechas
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado)
VALUES (2, 1, '2024-07-01', 6.00, 90.00, 1100.00, 'cosechado');
SET @id_siembra_nueva := LAST_INSERT_ID();

-- Cosecha asociada a la nueva siembra
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total)
VALUES (@id_siembra_nueva, '2024-10-01', 35000.00, 93.00, 0.50, 17500.00);

-- Aplicación de insumo para aportar costo variable (usa insumo id 1 existente en agrodata.sql)
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion)
VALUES (@id_siembra_nueva, 1, '2024-07-15', 120.00, 102.00, 'Aplicación localizada');

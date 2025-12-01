-- Seeds extendidos para enriquecer histórico de proyección y costos
USE agrodata;

-- Siembra y cosecha 1 (Maíz en Lote A)
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado)
VALUES (1, 1, '2024-07-05', 9.50, 24.00, 1400.00, 'cosechado');
SET @s1 := LAST_INSERT_ID();
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total)
VALUES (@s1, '2024-10-12', 33000.00, 94.00, 0.52, 17160.00);
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion)
VALUES (@s1, 1, '2024-08-01', 110.00, 93.50, 'Aplicación al voleo');

-- Siembra y cosecha 2 (Tomate en Lote C)
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado)
VALUES (3, 3, '2024-08-15', 4.00, 2.00, 2200.00, 'cosechado');
SET @s2 := LAST_INSERT_ID();
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total)
VALUES (@s2, '2024-11-20', 21500.00, 91.00, 0.85, 18275.00);
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion)
VALUES (@s2, 4, '2024-09-10', 6.00, 95.00, 'Fumigación foliar');

-- Siembra y cosecha 3 (Frijol en Lote B)
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado)
VALUES (2, 2, '2024-09-01', 7.50, 110.00, 780.00, 'cosechado');
SET @s3 := LAST_INSERT_ID();
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total)
VALUES (@s3, '2024-12-03', 13000.00, 90.00, 1.18, 15340.00);
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion)
VALUES (@s3, 2, '2024-09-20', 95.00, 114.00, 'Aplicación localizada');

-- Siembra y cosecha 4 (Papa en Lote D)
INSERT INTO siembra (id_lote, id_cultivo, fecha_siembra, area_sembrada, cantidad_semilla, costo_siembra, estado)
VALUES (4, 4, '2024-07-25', 11.00, 1650.00, 2950.00, 'cosechado');
SET @s4 := LAST_INSERT_ID();
INSERT INTO cosecha (id_siembra, fecha_cosecha, cantidad_kg, calidad_porcentaje, precio_venta_kg, ingreso_total)
VALUES (@s4, '2024-11-15', 27000.00, 93.00, 0.62, 16740.00);
INSERT INTO aplicacion_insumo (id_siembra, id_insumo, fecha_aplicacion, cantidad_aplicada, costo_aplicacion, metodo_aplicacion)
VALUES (@s4, 1, '2024-08-20', 150.00, 127.50, 'Aplicación al voleo');

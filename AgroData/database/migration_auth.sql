-- Migración: usuarios y relación con fincas
USE agrodata;

-- Crear tabla usuario si no existe
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(100),
    fecha_registro DATE DEFAULT (CURRENT_DATE)
);

-- Agregar columna user_id a finca si no existe
ALTER TABLE finca ADD COLUMN IF NOT EXISTS user_id INT NULL;
ALTER TABLE finca ADD CONSTRAINT IF NOT EXISTS fk_finca_usuario FOREIGN KEY (user_id) REFERENCES usuario(id_usuario) ON DELETE SET NULL;

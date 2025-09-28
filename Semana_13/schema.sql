-- Crea la base de datos y la tabla productos
CREATE DATABASE IF NOT EXISTS desarrollo_web
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE desarrollo_web;

CREATE TABLE IF NOT EXISTS productos (
  id_producto INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(150) NOT NULL,
  precio      DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  stock       INT NOT NULL DEFAULT 0,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

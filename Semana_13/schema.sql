CREATE DATABASE IF NOT EXISTS desarrollo_web CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE desarrollo_web;

DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS categorias;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  nombre VARCHAR(100),
  password_hash VARCHAR(255) NOT NULL,
  is_admin TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE categorias (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL UNIQUE,
  descripcion VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(150) NOT NULL,
  precio DECIMAL(10,2) NOT NULL DEFAULT 0.00,
  stock INT NOT NULL DEFAULT 0,
  categoria_id INT NULL,
  descripcion TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_prod_cat FOREIGN KEY (categoria_id)
    REFERENCES categorias(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB;

INSERT INTO categorias (nombre, descripcion) VALUES
('Electrónica','Dispositivos y gadgets'),
('Hogar','Artículos para el hogar'),
('Oficina','Utiles y mobiliario');

INSERT INTO productos (nombre, precio, stock, categoria_id, descripcion) VALUES
('Teclado mecánico', 59.90, 20, 1, 'Switches blue'),
('Cafetera italiana', 24.50, 15, 2, 'Aluminio 6 tazas'),
('Resma A4 500h', 6.80, 50, 3, 'Papel 75g');

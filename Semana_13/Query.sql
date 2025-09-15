-- 1) Crear la base de datos
CREATE DATABASE IF NOT EXISTS desarrollo_web
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2) Usar la base de datos
USE desarrollo_web;

-- 3) (OPCIONAL) Crear un usuario dedicado para Flask
--    Si usas XAMPP con root sin contraseña, puedes saltarte esta parte.
CREATE USER IF NOT EXISTS 'flask_user'@'localhost' IDENTIFIED BY 'flask_pass_123';
GRANT ALL PRIVILEGES ON desarrollo_web.* TO 'flask_user'@'localhost';
FLUSH PRIVILEGES;

-- 4) Tabla requerida por la tarea
CREATE TABLE IF NOT EXISTS usuarios (
  id_usuario INT AUTO_INCREMENT PRIMARY KEY,
  nombre     VARCHAR(100) NOT NULL,
  mail       VARCHAR(150) NOT NULL,
  creado_en  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_usuarios_mail (mail)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5) Tablas extra (ajústalas a tu proyecto)
CREATE TABLE IF NOT EXISTS proyectos (
  id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(120) NOT NULL,
  descripcion TEXT,
  creado_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS tareas (
  id_tarea    INT AUTO_INCREMENT PRIMARY KEY,
  id_proyecto INT NOT NULL,
  titulo      VARCHAR(150) NOT NULL,
  estado      ENUM('pendiente','en_progreso','hecha') DEFAULT 'pendiente',
  asignado_a  VARCHAR(100),
  creado_en   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tareas_proyectos
    FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6) Datos de prueba (opcional)
INSERT INTO usuarios (nombre, mail) VALUES
('Juan Pérez', 'juan@example.com'),
('Ana Díaz', 'ana@example.com')
ON DUPLICATE KEY UPDATE nombre = VALUES(nombre);

INSERT INTO proyectos (nombre, descripcion) VALUES
('Demo Flask', 'Proyecto de ejemplo con Flask + MySQL')
ON DUPLICATE KEY UPDATE descripcion = VALUES(descripcion);

INSERT INTO tareas (id_proyecto, titulo, estado) VALUES
(1, 'Configurar conexión', 'hecha'),
(1, 'Crear endpoints', 'en_progreso')
ON DUPLICATE KEY UPDATE estado = VALUES(estado);

-- 7) Verificaciones rápidas
SHOW TABLES;
SELECT * FROM usuarios;

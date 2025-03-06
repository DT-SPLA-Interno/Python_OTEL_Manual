CREATE DATABASE IF NOT EXISTS inventario;
USE inventario;

-- Creación de tabla 'items'
CREATE TABLE IF NOT EXISTS items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL DEFAULT 0
);

-- Opcional: Insertar datos de ejemplo
INSERT INTO items (name, quantity) VALUES ('Laptop', 10);
INSERT INTO items (name, quantity) VALUES ('Mouse', 50);
INSERT INTO items (name, quantity) VALUES ('Teclado', 30);
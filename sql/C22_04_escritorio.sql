-- FoodPass Escritorio · Cambios mínimos a foodpass_v2 para el escritorio (C2.2-04)
-- Ejecutar una sola vez en la base que usa la API. No borra ni cambia datos.

-- 1. Servicio entregado en cada canje (RN01). Si ya existe, MySQL muestra un
--    error de columna duplicada: se puede ignorar.
ALTER TABLE canjes
  ADD COLUMN servicio ENUM('desayuno','almuerzo','refrigerio') NULL AFTER estado;

-- 2. La clave única (usuario_id, periodo) debe existir: es la que impide dos
--    canjes del mismo usuario el mismo día. Comprobar con:
--      SHOW INDEX FROM canjes WHERE Key_name = 'uq_usuario_periodo';
--    Si no aparece, crearla:
--      ALTER TABLE canjes ADD UNIQUE KEY uq_usuario_periodo (usuario_id, periodo);

-- 3. Tabla de códigos del móvil (la API la crea sola al generar el primer QR;
--    se deja aquí por si la base es nueva).
CREATE TABLE IF NOT EXISTS qr_tokens (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  usuario_id BIGINT UNSIGNED NOT NULL,
  token VARCHAR(64) NOT NULL UNIQUE,
  code VARCHAR(20) NOT NULL,
  expires_at DATETIME NOT NULL,
  usado TINYINT(1) DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_qr_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
  INDEX idx_qr_token (token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Usuario de MySQL solo para el escritorio (recomendado; cambiar la clave):
--   CREATE USER 'fp_escritorio'@'%' IDENTIFIED BY 'cambiar-esta-clave';
--   GRANT SELECT ON foodpass_v2.usuarios TO 'fp_escritorio'@'%';
--   GRANT SELECT ON foodpass_v2.restaurantes TO 'fp_escritorio'@'%';
--   GRANT SELECT ON foodpass_v2.roles TO 'fp_escritorio'@'%';
--   GRANT SELECT ON foodpass_v2.rol_usuario TO 'fp_escritorio'@'%';
--   GRANT SELECT, INSERT, UPDATE ON foodpass_v2.canjes TO 'fp_escritorio'@'%';
--   GRANT SELECT, UPDATE ON foodpass_v2.qr_tokens TO 'fp_escritorio'@'%';
--   GRANT SELECT, INSERT, UPDATE ON foodpass_v2.beneficiarios_sena TO 'fp_escritorio'@'%';

-- 5. Rol y cuenta del operador para la demo (si el rol no existe):
--   INSERT INTO roles (nombre, descripcion) VALUES ('operador_restaurante', 'Personal de la cafetería');
--   Luego asignarlo al usuario del operador en rol_usuario.

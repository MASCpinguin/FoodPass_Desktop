-- FoodPass Escritorio · Códigos de prueba para la ventanilla
-- Ejecutar en phpMyAdmin (base foodpass_v2, pestaña SQL) sobre la base de
-- demostración (foodpass_v2_escritorio_demo.sql). Los códigos vencen hoy a
-- medianoche y sirven una sola vez.

-- 0. Limpieza (para repetir la prueba desde cero)
DELETE FROM qr_tokens WHERE code IN ('FP-A1B2C3','FP-B2C3D4','FP-C3D4E5','FP-D4E5F6','FP-E5F6A7','FP-F6A7B8','FP-0A0B0C');
DELETE FROM canjes WHERE codigo_qr LIKE 'FP-QR-PRUEBA-%' OR detalle LIKE 'Escritorio%';

-- 1. Códigos cortos del celular (qr_tokens)
INSERT INTO qr_tokens (usuario_id, token, code, expires_at, usado)
SELECT u.id, SHA2(CONCAT('prueba-', u.email, NOW()), 256), c.code,
       DATE_ADD(CURDATE(), INTERVAL 1 DAY), 0
FROM usuarios u
JOIN (SELECT 'aprendiz2@soy.sena.edu.co' AS email, 'FP-A1B2C3' AS code
      UNION ALL SELECT 'aprendiz3@soy.sena.edu.co', 'FP-B2C3D4'
      UNION ALL SELECT 'aprendiz4@soy.sena.edu.co', 'FP-C3D4E5'
      UNION ALL SELECT 'aprendiz5@soy.sena.edu.co', 'FP-D4E5F6'
      UNION ALL SELECT 'pedro@soy.sena.edu.co',     'FP-E5F6A7'
      UNION ALL SELECT 'aprendiz19@soy.sena.edu.co','FP-F6A7B8') c
  ON c.email = u.email;

-- 2. QR de la web (canjes en estado pendiente)
INSERT INTO canjes (usuario_id, restaurante_id, monto, fecha_canje, periodo,
                    estado, detalle, codigo_qr, expira_en)
SELECT u.id, 1, 0, CURDATE(), CONCAT('pendiente-', c.qr), 'pendiente',
       'Beneficio SENA', c.qr, DATE_ADD(CURDATE(), INTERVAL 1 DAY)
FROM usuarios u
JOIN (SELECT 'aprendiz6@soy.sena.edu.co' AS email, 'FP-QR-PRUEBA-0001' AS qr
      UNION ALL SELECT 'aprendiz7@soy.sena.edu.co', 'FP-QR-PRUEBA-0002'
      UNION ALL SELECT 'aprendiz8@soy.sena.edu.co', 'FP-QR-PRUEBA-0003') c
  ON c.email = u.email;

-- 3. Código vencido (para probar «Código vencido»)
INSERT INTO qr_tokens (usuario_id, token, code, expires_at, usado)
SELECT id, SHA2(CONCAT('vencido-', email, NOW()), 256), 'FP-0A0B0C',
       DATE_SUB(NOW(), INTERVAL 1 HOUR), 0
FROM usuarios WHERE email = 'aprendiz9@soy.sena.edu.co';

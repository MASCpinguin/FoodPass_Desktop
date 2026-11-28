-- ======================================================================
-- FoodPass · Base de datos foodpass_v2 lista para el escritorio (v2.2)
-- Importar en una base NUEVA y vacía (la crea DROP/CREATE de cada tabla).
-- NO importar sobre la base real de la API: borraría sus tablas.
-- Origen: foodpass_v2_actualizada.sql (repositorio FoodPassWeb) + ajustes del escritorio.
-- ======================================================================
SET NAMES utf8mb4;

-- MySQL dump 10.13  Distrib 8.4.3, for Win64 (x86_64)
--
-- Host: localhost    Database: foodpass_v2_db
-- ------------------------------------------------------
-- Server version	8.4.3

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `audit_logs`
--

DROP TABLE IF EXISTS `audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `audit_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `evento_codigo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `modulo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `actor_id` bigint unsigned DEFAULT NULL,
  `actor_nombre` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `actor_rol` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `metadata_json` json DEFAULT NULL,
  `hash_integridad` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `audit_logs`
--

LOCK TABLES `audit_logs` WRITE;
/*!40000 ALTER TABLE `audit_logs` DISABLE KEYS */;
INSERT INTO `audit_logs` VALUES (1,'PADRON_SINCRONIZADO','Administración','Padrón oficial sincronizado con archivo \'pad6F8B.tmp.csv\'. Activados: 3, Inactivados: 3, Errores: 0 por Test Automático.',NULL,'Sistema Automatizado / Guest','SYSTEM','127.0.0.1','{\"archivo\": \"pad6F8B.tmp.csv\", \"errores\": 0, \"carga_id\": 1, \"activados\": 3, \"inactivados\": 3}','a09967ee8d74fc5e7a3aa825a81b47a3e32ba07c635d6af841b434598f2df942','2026-11-17 09:26:50'),(2,'QR_ENVIADO_CORREO','Beneficios SENA','Credencial QR FP-QR-TEST-1794889579 enviada satisfactoriamente al correo carlos.aprendiz@soy.sena.edu.co.',3,'Carlos Santiago Aprendiz','ROLE_APRENDIZ','127.0.0.1','{\"email\": \"carlos.aprendiz@soy.sena.edu.co\", \"canje_id\": 1, \"codigo_qr\": \"FP-QR-TEST-1794889579\", \"fecha_canje\": \"2026-11-17T00:00:00.000000Z\"}','7b4f5a4e6de7fbce66f7a8f663eb8a89b484006587e5d1bc25035603ba8002a3','2026-11-17 09:57:21');
/*!40000 ALTER TABLE `audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `beneficiarios_sena`
--

DROP TABLE IF EXISTS `beneficiarios_sena`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `beneficiarios_sena` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `numero_documento` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nombre_completo` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `sincronizado_at` timestamp NULL DEFAULT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `beneficiarios_sena`
--

LOCK TABLES `beneficiarios_sena` WRITE;
/*!40000 ALTER TABLE `beneficiarios_sena` DISABLE KEYS */;
INSERT INTO `beneficiarios_sena` VALUES (1,'1144098312','Carlos Eduardo Aprendiz','carlos.aprendiz@soy.sena.edu.co',1,'2026-11-17 09:26:50','2026-11-17 04:08:02','2026-11-17 09:26:50'),(2,'1144098312','Jose Alejandro Delgado','jose.delgado@soy.sena.edu.co',1,'2026-11-17 04:08:02','2026-11-17 04:08:02','2026-11-17 04:08:02'),(3,'1006508918','Laura Camila Silva','laura.silva@soy.sena.edu.co',0,'2026-11-17 09:26:50','2026-11-17 04:08:02','2026-11-17 09:26:50'),(4,'1098456789','Ana María Rodríguez','ana@soy.sena.edu.co',0,'2026-11-17 09:26:50','2026-11-17 04:08:02','2026-11-17 09:26:50'),(5,'1006441023','Luisa Fernanda Lane','luisa@soy.sena.edu.co',0,'2026-11-17 09:26:50','2026-11-17 04:08:02','2026-11-17 09:26:50'),(6,'1001001001','Nuevo Aprendiz Beneficiario Uno','nuevo1@sena.edu.co',1,'2026-11-17 09:26:50','2026-11-17 09:26:50','2026-11-17 09:26:50'),(7,'1002002002','Nuevo Aprendiz Beneficiario Dos','nuevo2@sena.edu.co',1,'2026-11-17 09:26:50','2026-11-17 09:26:50','2026-11-17 09:26:50');
/*!40000 ALTER TABLE `beneficiarios_sena` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cache`
--

DROP TABLE IF EXISTS `cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cache` (
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` mediumtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expiration` int NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cache`
--

LOCK TABLES `cache` WRITE;
/*!40000 ALTER TABLE `cache` DISABLE KEYS */;
/*!40000 ALTER TABLE `cache` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cache_locks`
--

DROP TABLE IF EXISTS `cache_locks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cache_locks` (
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `owner` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expiration` int NOT NULL,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cache_locks`
--

LOCK TABLES `cache_locks` WRITE;
/*!40000 ALTER TABLE `cache_locks` DISABLE KEYS */;
/*!40000 ALTER TABLE `cache_locks` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `canjes`
--

DROP TABLE IF EXISTS `canjes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `canjes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `beneficiario_sena_id` bigint unsigned DEFAULT NULL,
  `restaurante_id` bigint unsigned NOT NULL,
  `monto` decimal(10,2) NOT NULL DEFAULT '0.00',
  `fecha_canje` date DEFAULT NULL,
  `periodo` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `estado` enum('entregado','pendiente','rechazado') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'entregado',
  `detalle` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `codigo_qr` varchar(191) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `expira_en` timestamp NULL DEFAULT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuario_periodo` (`usuario_id`,`periodo`),
  UNIQUE KEY `codigo_qr` (`codigo_qr`),
  KEY `fk_canje_beneficiario` (`beneficiario_sena_id`),
  KEY `fk_canje_restaurante` (`restaurante_id`),
  CONSTRAINT `fk_canje_beneficiario` FOREIGN KEY (`beneficiario_sena_id`) REFERENCES `beneficiarios_sena` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_canje_restaurante` FOREIGN KEY (`restaurante_id`) REFERENCES `restaurantes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_canje_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `canjes`
--

LOCK TABLES `canjes` WRITE;
/*!40000 ALTER TABLE `canjes` DISABLE KEYS */;
INSERT INTO `canjes` VALUES (1,3,1,1,0.00,'2026-11-17','2026-11-17 04:26:20','pendiente','Beneficio Almuerzo SENA','FP-QR-TEST-1794889579','2026-11-18 05:00:00','2026-11-17 09:26:20','2026-11-17 09:26:20');
/*!40000 ALTER TABLE `canjes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cargas_beneficiarios`
--

DROP TABLE IF EXISTS `cargas_beneficiarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cargas_beneficiarios` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `nombre_archivo_original` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ruta_archivo_privado` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `formato` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_filas_leidas` int unsigned NOT NULL DEFAULT '0',
  `aprendices_activados` int unsigned NOT NULL DEFAULT '0',
  `aprendices_inactivados` int unsigned NOT NULL DEFAULT '0',
  `errores_count` int unsigned NOT NULL DEFAULT '0',
  `errores_detalle` json DEFAULT NULL,
  `ejecutado_por` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Sistema',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cargas_beneficiarios`
--

LOCK TABLES `cargas_beneficiarios` WRITE;
/*!40000 ALTER TABLE `cargas_beneficiarios` DISABLE KEYS */;
INSERT INTO `cargas_beneficiarios` VALUES (1,'pad6F8B.tmp.csv','private/sena_padron/20261117_042650_pad6F8B.tmp.csv','csv',3,3,3,0,'[]','Test Automático','2026-11-17 09:26:50','2026-11-17 09:26:50');
/*!40000 ALTER TABLE `cargas_beneficiarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (1,'Almuerzo Ejecutivo','Plato fuerte del día'),(2,'Bebidas Calientes','Café, chocolate, infusiones'),(3,'Postres','Dulces después del almuerzo');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_pedidos`
--

DROP TABLE IF EXISTS `detalle_pedidos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_pedidos` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `pedido_id` bigint unsigned NOT NULL,
  `platillo_id` bigint unsigned NOT NULL,
  `cantidad` int NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_detalle_pedido` (`pedido_id`),
  KEY `fk_detalle_platillo` (`platillo_id`),
  CONSTRAINT `fk_detalle_pedido` FOREIGN KEY (`pedido_id`) REFERENCES `pedidos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalle_platillo` FOREIGN KEY (`platillo_id`) REFERENCES `platillos` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_pedidos`
--

LOCK TABLES `detalle_pedidos` WRITE;
/*!40000 ALTER TABLE `detalle_pedidos` DISABLE KEYS */;
INSERT INTO `detalle_pedidos` VALUES (1,1,1,1,2500.00,'2026-11-17 09:56:57','2026-11-17 09:56:57');
/*!40000 ALTER TABLE `detalle_pedidos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `failed_jobs`
--

DROP TABLE IF EXISTS `failed_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `failed_jobs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `uuid` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `connection` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `queue` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `exception` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `failed_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `failed_jobs`
--

LOCK TABLES `failed_jobs` WRITE;
/*!40000 ALTER TABLE `failed_jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `failed_jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historial_beneficios_sena`
--

DROP TABLE IF EXISTS `historial_beneficios_sena`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial_beneficios_sena` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `fecha_canje` date NOT NULL,
  `hora_canje` time NOT NULL,
  `estado` enum('Aprobado','Rechazado') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'Aprobado',
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_hist_beneficio_usuario` (`usuario_id`),
  CONSTRAINT `fk_hist_beneficio_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial_beneficios_sena`
--

LOCK TABLES `historial_beneficios_sena` WRITE;
/*!40000 ALTER TABLE `historial_beneficios_sena` DISABLE KEYS */;
/*!40000 ALTER TABLE `historial_beneficios_sena` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `queue` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `attempts` tinyint unsigned NOT NULL,
  `reserved_at` int DEFAULT NULL,
  `available_at` int NOT NULL,
  `created_at` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `migrations`
--

DROP TABLE IF EXISTS `migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `migrations` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `migration` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `batch` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `migrations`
--

LOCK TABLES `migrations` WRITE;
/*!40000 ALTER TABLE `migrations` DISABLE KEYS */;
/*!40000 ALTER TABLE `migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `password_reset_tokens`
--

DROP TABLE IF EXISTS `password_reset_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `password_reset_tokens` (
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `token` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `password_reset_tokens`
--

LOCK TABLES `password_reset_tokens` WRITE;
/*!40000 ALTER TABLE `password_reset_tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `password_reset_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pedidos`
--

DROP TABLE IF EXISTS `pedidos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pedidos` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `usuario_id` bigint unsigned NOT NULL,
  `restaurante_id` bigint unsigned NOT NULL,
  `total` decimal(10,2) NOT NULL,
  `estado` enum('pendiente','preparacion','entregado','cancelado') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'pendiente',
  `fecha_pedido` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_pedidos_usuario` (`usuario_id`),
  KEY `fk_pedidos_restaurante` (`restaurante_id`),
  CONSTRAINT `fk_pedidos_restaurante` FOREIGN KEY (`restaurante_id`) REFERENCES `restaurantes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pedidos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pedidos`
--

LOCK TABLES `pedidos` WRITE;
/*!40000 ALTER TABLE `pedidos` DISABLE KEYS */;
INSERT INTO `pedidos` VALUES (1,3,1,2500.00,'pendiente','2026-11-17 09:56:57','2026-11-17 09:56:57','2026-11-17 09:56:57');
/*!40000 ALTER TABLE `pedidos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `platillos`
--

DROP TABLE IF EXISTS `platillos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `platillos` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `restaurante_id` bigint unsigned NOT NULL,
  `categoria_id` int NOT NULL,
  `nombre` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` text COLLATE utf8mb4_unicode_ci,
  `precio` decimal(10,2) NOT NULL,
  `ingredientes` text COLLATE utf8mb4_unicode_ci,
  `imagen` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `disponible` tinyint(1) NOT NULL DEFAULT '1',
  `stock` int DEFAULT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_restaurante_nombre` (`restaurante_id`,`nombre`),
  KEY `fk_platillos_categoria` (`categoria_id`),
  CONSTRAINT `fk_platillos_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_platillos_restaurante` FOREIGN KEY (`restaurante_id`) REFERENCES `restaurantes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `platillos`
--

LOCK TABLES `platillos` WRITE;
/*!40000 ALTER TABLE `platillos` DISABLE KEYS */;
INSERT INTO `platillos` VALUES (1,1,1,'Arvejas','Arvejas tiernas guisadas con hogao y un toque de color.',2500.00,'Arvejas, tomate, cebolla, ajo, comino, color, sal',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(2,1,1,'Ensalada Fresca','Ensalada del día con verduras frescas y aderezo de limón.',3500.00,'Lechuga, tomate, pepino, zanahoria, limón, sal, aceite de oliva',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(3,1,1,'Frijoles','Frijoles rojos o negros cocidos con hogao.',2500.00,'Frijoles, tomate, cebolla larga, ajo, comino, color, cilantro',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(4,1,1,'Lentejas','Sopa espesa de lentejas con plátano maduro y zanahoria.',2500.00,'Lentejas, plátano maduro, zanahoria, cebolla, ajo, comino, sal',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(5,1,1,'Puré de Papa','Puré cremoso de papa criolla con mantequilla.',3000.00,'Papa criolla, mantequilla, leche, sal, pimienta',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(6,1,1,'Verduras Variadas','Mezcla de verduras al vapor.',3000.00,'Brócoli, zanahoria, habichuela, calabacín, sal, aceite',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(7,1,2,'Arroz con Pollo','Arroz con pollo y vegetales.',8500.00,'Arroz, pollo, zanahoria, arveja, ajo, cebolla, comino, color, sal',NULL,0,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(8,1,1,'Carne de Cerdo','Carne de cerdo guisada en salsa criolla.',9000.00,'Cerdo, tomate, cebolla, ajo, comino, color, cilantro, sal',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(9,1,1,'Carne de Res','Bistec de res en salsa criolla.',9500.00,'Res, tomate, cebolla larga, ajo, comino, sal, pimienta',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05'),(10,1,1,'Pollo Guisado','Pollo en salsa de tomate con arroz y ensalada.',8000.00,'Pollo, tomate, cebolla, ajo, pimentón, comino, laurel, sal',NULL,1,NULL,'2026-11-12 17:02:05','2026-11-12 17:02:05');
/*!40000 ALTER TABLE `platillos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `restaurantes`
--

DROP TABLE IF EXISTS `restaurantes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `restaurantes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `restaurantes`
--

LOCK TABLES `restaurantes` WRITE;
/*!40000 ALTER TABLE `restaurantes` DISABLE KEYS */;
INSERT INTO `restaurantes` VALUES (1,'FoodPass Café','Calle 123 #45-67','3001234567','2026-11-12 17:02:05','2026-11-12 17:02:05');
/*!40000 ALTER TABLE `restaurantes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rol_usuario`
--

DROP TABLE IF EXISTS `rol_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol_usuario` (
  `usuario_id` bigint unsigned NOT NULL,
  `rol_id` bigint unsigned NOT NULL,
  PRIMARY KEY (`usuario_id`,`rol_id`),
  KEY `fk_rol_usuario_rol` (`rol_id`),
  CONSTRAINT `fk_rol_usuario_rol` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rol_usuario_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol_usuario`
--

LOCK TABLES `rol_usuario` WRITE;
/*!40000 ALTER TABLE `rol_usuario` DISABLE KEYS */;
INSERT INTO `rol_usuario` VALUES (1,1),(2,2),(3,4),(4,4),(5,4),(6,4);
/*!40000 ALTER TABLE `rol_usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `descripcion` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'admin','Administrador del sistema'),(2,'instructor','Líder o instructor'),(3,'tecnico','Técnico con permisos de gestión'),(4,'cliente','Usuario final');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sessions`
--

DROP TABLE IF EXISTS `sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sessions` (
  `id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` bigint unsigned DEFAULT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_agent` text COLLATE utf8mb4_unicode_ci,
  `payload` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_activity` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `sessions_user_id_index` (`user_id`),
  KEY `sessions_last_activity_index` (`last_activity`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sessions`
--

LOCK TABLES `sessions` WRITE;
/*!40000 ALTER TABLE `sessions` DISABLE KEYS */;
INSERT INTO `sessions` VALUES ('7juNOID6WL0QalMxUUy24QLQHWHcGH1iWfSDBl6V',NULL,'127.0.0.1','curl/8.22.0','YTozOntzOjY6Il90b2tlbiI7czo0MDoiYUtJVlBQMVkyQlpnZEFZcGlnUVFvWlo0cnVDVG13WHo1VnpmRDRvciI7czo5OiJfcHJldmlvdXMiO2E6Mjp7czozOiJ1cmwiO3M6Mjc6Imh0dHA6Ly8xMjcuMC4wLjE6ODAwMC9sb2dpbiI7czo1OiJyb3V0ZSI7czo1OiJsb2dpbiI7fXM6NjoiX2ZsYXNoIjthOjI6e3M6Mzoib2xkIjthOjA6e31zOjM6Im5ldyI7YTowOnt9fX0=',1794891261),('W7An6gvbR3JhZCii6zOuNyL0DCiupi2qWdt7CUcI',NULL,'127.0.0.1','curl/8.22.0','YTozOntzOjY6Il90b2tlbiI7czo0MDoiYTZZR0RpZ21xZlhKdzlBNGpWQXkzckhtYkN6cGdZaHg2b3phMVFlUyI7czo5OiJfcHJldmlvdXMiO2E6Mjp7czozOiJ1cmwiO3M6Mjc6Imh0dHA6Ly8xMjcuMC4wLjE6ODAwMC9sb2dpbiI7czo1OiJyb3V0ZSI7czo1OiJsb2dpbiI7fXM6NjoiX2ZsYXNoIjthOjI6e3M6Mzoib2xkIjthOjA6e31zOjM6Im5ldyI7YTowOnt9fX0=',1794889787),('y4O8yqSlx3hH2AVPCXKja7FYyfFh37cAI5ClK2Nj',NULL,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36','YTozOntzOjY6Il90b2tlbiI7czo0MDoiZWRwc1hTR09TT3RlTFZtTWtOMXNDOWMydFV6ME9lQWZyckdYdHNBcSI7czo2OiJfZmxhc2giO2E6Mjp7czozOiJvbGQiO2E6MDp7fXM6MzoibmV3IjthOjA6e319czo5OiJfcHJldmlvdXMiO2E6Mjp7czozOiJ1cmwiO3M6Mjc6Imh0dHA6Ly8xMjcuMC4wLjE6ODAwMC9sb2dpbiI7czo1OiJyb3V0ZSI7czo1OiJsb2dpbiI7fX0=',1794891459);
/*!40000 ALTER TABLE `sessions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `documento` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `actualizado_en` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Administrador SENA FoodPass','admin@foodpass.com','$2y$10$RInsQlOvtQLliv.swdAzw.NImIzvwuRWbMW3mhXvEe85wVLBHNi0q','123456789',1,'2026-11-12 17:02:05','2026-11-17 09:44:38'),(2,'Instructor SENA CEAI','instructor@foodpass.com','$2y$10$RInsQlOvtQLliv.swdAzw.NImIzvwuRWbMW3mhXvEe85wVLBHNi0q','987654321',1,'2026-11-17 04:08:02','2026-11-17 04:08:02'),(3,'Carlos Santiago Aprendiz','carlos.aprendiz@soy.sena.edu.co','$2y$10$RInsQlOvtQLliv.swdAzw.NImIzvwuRWbMW3mhXvEe85wVLBHNi0q','1005894321',1,'2026-11-17 04:08:02','2026-11-17 09:26:50'),(4,'Juan Aprendiz Regular','aprendiz@foodpass.com','$2y$10$RInsQlOvtQLliv.swdAzw.NImIzvwuRWbMW3mhXvEe85wVLBHNi0q','1006999888',1,'2026-11-17 04:08:02','2026-11-17 04:08:02'),(5,'Nuevo Usuario Google Test','prueba.google.1794891211@gmail.com','$2y$12$yYsWBtFpGK9iERtlAkrsx.D9AvqV37Zeu9ROsLCSuXF3FRYiaCuR6',NULL,1,'2026-11-17 09:53:31','2026-11-17 09:53:31'),(6,'Nuevo Usuario Google Test','prueba.google.1794891250@gmail.com','$2y$12$bzp6XkFlzRdSt/nRp1hB0.SV2BKFNSxnemhCswW.w7s22YpIdGNYW',NULL,1,'2026-11-17 09:54:10','2026-11-17 09:54:10');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-17  0:10:25


-- ======================================================================
-- FoodPass Escritorio · Ajustes para el escritorio y la API (v2.2)
-- ======================================================================
-- Columna ficha que usa la API FoodPass (registro y login)
ALTER TABLE usuarios ADD COLUMN ficha VARCHAR(20) NULL AFTER documento;

-- Servicio entregado en cada canje (RN01)
ALTER TABLE canjes ADD COLUMN servicio ENUM('desayuno','almuerzo','refrigerio') NULL AFTER estado;

-- Códigos del móvil (los crea la API)
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

-- Roles del escritorio y de los aprendices
INSERT INTO roles (nombre, descripcion) VALUES
  ('operador_restaurante','Personal de la cafetería'),
  ('beneficiario','Aprendiz beneficiario');

-- ======================================================================
-- Datos de prueba (entorno simulado)
--   Operador:  operador@foodpass.com      / FoodPass2026!
--   Aprendices: aprendiz1..aprendiz19@soy.sena.edu.co / Aprendiz2026!
-- ======================================================================

INSERT INTO usuarios (nombre,email,password_hash,documento,activo) VALUES ('Operador Cafetería CEAI','operador@foodpass.com','$2b$10$YVie6tBATOKXcJfMiWhZBeRU2SSsy0T3SUcapiTMSjfjchrTBsy1a','1100000001',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='operador@foodpass.com' AND r.nombre='operador_restaurante';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001100','Ana Gómez','aprendiz1@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Ana Gómez','aprendiz1@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001100','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz1@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001101','Mateo Rodríguez','aprendiz2@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Mateo Rodríguez','aprendiz2@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001101','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz2@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001102','Sofía Amaya','aprendiz3@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Sofía Amaya','aprendiz3@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001102','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz3@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001103','Juan Pérez','aprendiz4@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Juan Pérez','aprendiz4@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001103','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz4@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001104','Valentina Martínez','aprendiz5@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Valentina Martínez','aprendiz5@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001104','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz5@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001105','Santiago García','aprendiz6@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Santiago García','aprendiz6@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001105','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz6@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001106','Isabella López','aprendiz7@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Isabella López','aprendiz7@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001106','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz7@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001107','David Hernández','aprendiz8@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('David Hernández','aprendiz8@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001107','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz8@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001108','Mariana Sánchez','aprendiz9@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Mariana Sánchez','aprendiz9@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001108','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz9@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001109','Alejandro Ramírez','aprendiz10@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Alejandro Ramírez','aprendiz10@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001109','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz10@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001110','Camila Torres','aprendiz11@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Camila Torres','aprendiz11@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001110','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz11@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001111','Andrés Díaz','aprendiz12@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Andrés Díaz','aprendiz12@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001111','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz12@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001112','Daniela Vargas','aprendiz13@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Daniela Vargas','aprendiz13@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001112','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz13@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001113','Sebastián Castro','aprendiz14@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Sebastián Castro','aprendiz14@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001113','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz14@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001114','Lucía Morales','aprendiz15@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Lucía Morales','aprendiz15@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001114','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz15@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001115','Nicolás Ríos','aprendiz16@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Nicolás Ríos','aprendiz16@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001115','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz16@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001116','Gabriela Ortiz','aprendiz17@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Gabriela Ortiz','aprendiz17@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001116','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz17@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001117','Felipe Mendoza','aprendiz18@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Felipe Mendoza','aprendiz18@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001117','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz18@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001118','Paula Silva','aprendiz19@soy.sena.edu.co',0);
INSERT INTO usuarios (nombre,email,password_hash,documento,ficha,activo) VALUES ('Paula Silva','aprendiz19@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1001001118','3173467',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='aprendiz19@soy.sena.edu.co' AND r.nombre='beneficiario';
INSERT INTO beneficiarios_sena (numero_documento,nombre_completo,email,activo) VALUES ('1001001119','Diego Guerrero','aprendiz20@soy.sena.edu.co',1);
INSERT INTO usuarios (nombre,email,password_hash,documento,activo) VALUES ('Pedro Sin Apoyo','pedro@soy.sena.edu.co','$2b$10$Rb88zl6zNy1vtXIUYNRQAO3U/p/J8lJRqBUHzCQySVKq8zyKrWB3S','1009990001',1);
INSERT INTO rol_usuario (usuario_id, rol_id) SELECT u.id, r.id FROM usuarios u, roles r WHERE u.email='pedro@soy.sena.edu.co' AND r.nombre='beneficiario';

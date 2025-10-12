-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: sv46.byethost46.org    Database: iunaorg_chatBeto
-- ------------------------------------------------------
-- Server version	5.5.5-10.11.11-MariaDB-cll-lve

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `conversations`
--

DROP TABLE IF EXISTS `conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conversations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` text DEFAULT NULL,
  `create_time` float DEFAULT NULL,
  `update_time` float DEFAULT NULL,
  `mapping` text DEFAULT NULL,
  `moderation_results` text DEFAULT NULL,
  `current_node` text DEFAULT NULL,
  `plugin_ids` text DEFAULT NULL,
  `conversation_id` text DEFAULT NULL,
  `conversation_template_id` text DEFAULT NULL,
  `gizmo_id` text DEFAULT NULL,
  `gizmo_type` text DEFAULT NULL,
  `is_archived` int(11) DEFAULT NULL,
  `is_starred` text DEFAULT NULL,
  `safe_urls` text DEFAULT NULL,
  `default_model_slug` text DEFAULT NULL,
  `conversation_origin` text DEFAULT NULL,
  `voice` text DEFAULT NULL,
  `async_status` text DEFAULT NULL,
  `disabled_tool_ids` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=780 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `message_feedback`
--

DROP TABLE IF EXISTS `message_feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `message_feedback` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `conversation_id` text DEFAULT NULL,
  `user_id` text DEFAULT NULL,
  `rating` text DEFAULT NULL,
  `create_time` text DEFAULT NULL,
  `workspace_id` text DEFAULT NULL,
  `content` text DEFAULT NULL,
  `evaluation_name` text DEFAULT NULL,
  `evaluation_treatment` text DEFAULT NULL,
  `update_time` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `model_comparisons`
--

DROP TABLE IF EXISTS `model_comparisons`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `model_comparisons` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `message_id` text DEFAULT NULL,
  `conversation_id` text DEFAULT NULL,
  `original_message_id` text DEFAULT NULL,
  `new_message_id` text DEFAULT NULL,
  `rating` text DEFAULT NULL,
  `placement` text DEFAULT NULL,
  `ui_variant` int(11) DEFAULT NULL,
  `evaluation_name` text DEFAULT NULL,
  `evaluation_treatment` text DEFAULT NULL,
  `evaluation_type` text DEFAULT NULL,
  `message_metadatas` text DEFAULT NULL,
  `received_timestamp` int(11) DEFAULT NULL,
  `source_timestamp` int(11) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `client_type` text DEFAULT NULL,
  `user_id` text DEFAULT NULL,
  `product_surface` int(11) DEFAULT NULL,
  `create_time` text DEFAULT NULL,
  `update_time` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `shared_conversations`
--

DROP TABLE IF EXISTS `shared_conversations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `shared_conversations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `conversation_id` text DEFAULT NULL,
  `title` text DEFAULT NULL,
  `is_anonymous` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-03-05 18:24:43

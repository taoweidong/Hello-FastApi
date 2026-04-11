/*
Navicat MySQL Data Transfer

Source Server         : 本地MySql
Source Server Version : 80032
Source Host           : localhost:3306
Source Database       : xadmin-fastapi

Target Server Type    : MYSQL
Target Server Version : 80032
File Encoding         : 65001

Date: 2026-04-11 22:09:45
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for sys_departments
-- ----------------------------
DROP TABLE IF EXISTS `sys_departments`;
CREATE TABLE `sys_departments` (
  `id` char(32) NOT NULL,
  `mode_type` smallint NOT NULL,
  `name` varchar(128) NOT NULL,
  `code` varchar(128) NOT NULL,
  `rank` int NOT NULL,
  `auto_bind` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `parent_id` char(32) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `sys_departments_parent_id_fk` (`parent_id`),
  CONSTRAINT `sys_departments_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `sys_departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_ip_rules
-- ----------------------------
DROP TABLE IF EXISTS `sys_ip_rules`;
CREATE TABLE `sys_ip_rules` (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(45) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_type` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `created_at` datetime DEFAULT (now()),
  `expires_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sys_ip_rules_ip_address` (`ip_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_logs
-- ----------------------------
DROP TABLE IF EXISTS `sys_logs`;
CREATE TABLE `sys_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `module` varchar(64) DEFAULT NULL,
  `path` varchar(400) DEFAULT NULL,
  `body` longtext,
  `method` varchar(8) DEFAULT NULL,
  `ipaddress` char(39) DEFAULT NULL,
  `browser` varchar(64) DEFAULT NULL,
  `system` varchar(64) DEFAULT NULL,
  `response_code` int DEFAULT NULL,
  `response_result` longtext,
  `status_code` int DEFAULT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_menumeta
-- ----------------------------
DROP TABLE IF EXISTS `sys_menumeta`;
CREATE TABLE `sys_menumeta` (
  `id` char(32) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `r_svg_name` varchar(255) DEFAULT NULL,
  `is_show_menu` tinyint(1) NOT NULL,
  `is_show_parent` tinyint(1) NOT NULL,
  `is_keepalive` tinyint(1) NOT NULL,
  `frame_url` varchar(255) DEFAULT NULL,
  `frame_loading` tinyint(1) NOT NULL,
  `transition_enter` varchar(255) DEFAULT NULL,
  `transition_leave` varchar(255) DEFAULT NULL,
  `is_hidden_tag` tinyint(1) NOT NULL,
  `fixed_tag` tinyint(1) NOT NULL,
  `dynamic_level` int NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_menus
-- ----------------------------
DROP TABLE IF EXISTS `sys_menus`;
CREATE TABLE `sys_menus` (
  `id` char(32) NOT NULL,
  `menu_type` smallint NOT NULL,
  `name` varchar(128) NOT NULL,
  `rank` int NOT NULL,
  `path` varchar(255) NOT NULL,
  `component` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL,
  `method` varchar(10) DEFAULT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `parent_id` char(32) DEFAULT NULL,
  `meta_id` char(32) NOT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `meta_id` (`meta_id`),
  KEY `sys_menus_parent_id_fk` (`parent_id`),
  CONSTRAINT `sys_menus_ibfk_1` FOREIGN KEY (`meta_id`) REFERENCES `sys_menumeta` (`id`),
  CONSTRAINT `sys_menus_ibfk_2` FOREIGN KEY (`parent_id`) REFERENCES `sys_menus` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_roles
-- ----------------------------
DROP TABLE IF EXISTS `sys_roles`;
CREATE TABLE `sys_roles` (
  `id` char(32) NOT NULL,
  `name` varchar(128) NOT NULL,
  `code` varchar(128) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `code` (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_systemconfig
-- ----------------------------
DROP TABLE IF EXISTS `sys_systemconfig`;
CREATE TABLE `sys_systemconfig` (
  `id` char(32) NOT NULL,
  `value` longtext NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `access` tinyint(1) NOT NULL,
  `key` varchar(255) NOT NULL,
  `inherit` tinyint(1) NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_userinfo_roles
-- ----------------------------
DROP TABLE IF EXISTS `sys_userinfo_roles`;
CREATE TABLE `sys_userinfo_roles` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `userinfo_id` bigint NOT NULL,
  `userrole_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userinfo_id_userrole_id_uniq` (`userinfo_id`,`userrole_id`),
  KEY `sys_userinfo_roles_userrole_id_fk` (`userrole_id`),
  CONSTRAINT `sys_userinfo_roles_ibfk_1` FOREIGN KEY (`userinfo_id`) REFERENCES `sys_users` (`id`),
  CONSTRAINT `sys_userinfo_roles_ibfk_2` FOREIGN KEY (`userrole_id`) REFERENCES `sys_roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_userloginlog
-- ----------------------------
DROP TABLE IF EXISTS `sys_userloginlog`;
CREATE TABLE `sys_userloginlog` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` tinyint(1) NOT NULL,
  `ipaddress` char(39) DEFAULT NULL,
  `browser` varchar(64) DEFAULT NULL,
  `system` varchar(64) DEFAULT NULL,
  `agent` varchar(128) DEFAULT NULL,
  `login_type` smallint NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_userrole_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_userrole_menu`;
CREATE TABLE `sys_userrole_menu` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `userrole_id` char(32) NOT NULL,
  `menu_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `userrole_id_menu_id_uniq` (`userrole_id`,`menu_id`),
  KEY `sys_userrole_menu_menu_id_fk` (`menu_id`),
  CONSTRAINT `sys_userrole_menu_ibfk_1` FOREIGN KEY (`menu_id`) REFERENCES `sys_menus` (`id`),
  CONSTRAINT `sys_userrole_menu_ibfk_2` FOREIGN KEY (`userrole_id`) REFERENCES `sys_roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_users
-- ----------------------------
DROP TABLE IF EXISTS `sys_users`;
CREATE TABLE `sys_users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `mode_type` smallint NOT NULL,
  `avatar` varchar(100) DEFAULT NULL,
  `nickname` varchar(150) NOT NULL,
  `gender` int NOT NULL,
  `phone` varchar(16) NOT NULL,
  `email` varchar(254) NOT NULL,
  `creator_id` varchar(150) DEFAULT NULL,
  `modifier_id` varchar(150) DEFAULT NULL,
  `dept_id` char(32) DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `sys_users_dept_id_fk` (`dept_id`),
  KEY `sys_users_phone` (`phone`),
  KEY `sys_users_email` (`email`),
  CONSTRAINT `sys_users_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `sys_departments` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

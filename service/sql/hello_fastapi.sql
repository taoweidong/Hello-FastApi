/*
Navicat MySQL Data Transfer

Source Server         : 本地MySql
Source Server Version : 80032
Source Host           : localhost:3306
Source Database       : hello_fastapi

Target Server Type    : MYSQL
Target Server Version : 80032
File Encoding         : 65001

Date: 2026-04-18 09:24:18
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for sys_departments
-- ----------------------------
DROP TABLE IF EXISTS `sys_departments`;
CREATE TABLE `sys_departments` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `mode_type` int NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rank` int NOT NULL,
  `auto_bind` int NOT NULL,
  `is_active` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `sys_departments_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `sys_departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_dictionary
-- ----------------------------
DROP TABLE IF EXISTS `sys_dictionary`;
CREATE TABLE `sys_dictionary` (
  `id` varchar(255) NOT NULL COMMENT 'Id',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '字典名称：要求英文大写，下划线',
  `label` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '显示名称',
  `value` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '实际值',
  `status` int NOT NULL COMMENT '状态',
  `sort` int DEFAULT NULL COMMENT '显示排序',
  `parent_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '父级',
  `creator_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL COMMENT '创建人',
  `modifier_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `updated_time` datetime(6) DEFAULT NULL COMMENT '修改时间',
  `created_time` datetime(6) DEFAULT NULL COMMENT '创建时间',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  PRIMARY KEY (`id`),
  KEY `dvadmin_dictionary_creator_id_a76540f5` (`creator_id`),
  KEY `dvadmin_dictionary_parent_id_13040134` (`parent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_ip_rules
-- ----------------------------
DROP TABLE IF EXISTS `sys_ip_rules`;
CREATE TABLE `sys_ip_rules` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rule_type` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `expires_at` datetime DEFAULT NULL,
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_sys_ip_rules_ip_address` (`ip_address`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_logs
-- ----------------------------
DROP TABLE IF EXISTS `sys_logs`;
CREATE TABLE `sys_logs` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `module` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `path` varchar(400) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `body` text COLLATE utf8mb4_unicode_ci,
  `method` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ipaddress` varchar(39) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `browser` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `system` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `response_code` int DEFAULT NULL,
  `response_result` text COLLATE utf8mb4_unicode_ci,
  `status_code` int DEFAULT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_menumeta
-- ----------------------------
DROP TABLE IF EXISTS `sys_menumeta`;
CREATE TABLE `sys_menumeta` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `r_svg_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_show_menu` int NOT NULL,
  `is_show_parent` int NOT NULL,
  `is_keepalive` int NOT NULL,
  `frame_url` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `frame_loading` int NOT NULL,
  `transition_enter` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `transition_leave` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_hidden_tag` int NOT NULL,
  `fixed_tag` int NOT NULL,
  `dynamic_level` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_menus
-- ----------------------------
DROP TABLE IF EXISTS `sys_menus`;
CREATE TABLE `sys_menus` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `menu_type` int NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `rank` int NOT NULL,
  `path` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `component` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_active` int NOT NULL,
  `method` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `meta_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `meta_id` (`meta_id`),
  KEY `parent_id` (`parent_id`),
  CONSTRAINT `sys_menus_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `sys_menus` (`id`),
  CONSTRAINT `sys_menus_ibfk_2` FOREIGN KEY (`meta_id`) REFERENCES `sys_menumeta` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_roles
-- ----------------------------
DROP TABLE IF EXISTS `sys_roles`;
CREATE TABLE `sys_roles` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `code` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  UNIQUE KEY `ix_sys_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_setting
-- ----------------------------
DROP TABLE IF EXISTS `sys_setting`;
CREATE TABLE `sys_setting` (
  `id` char(32) NOT NULL,
  `name` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置的键名，命名要求：英文和下划线',
  `value` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '配置的值，不能有特殊字符',
  `is_active` tinyint(1) NOT NULL,
  `creator_id` varchar(0) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `modifier_id` varchar(0) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_time` datetime(6) NOT NULL,
  `updated_time` datetime(6) NOT NULL,
  `description` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ----------------------------
-- Table structure for sys_systemconfig
-- ----------------------------
DROP TABLE IF EXISTS `sys_systemconfig`;
CREATE TABLE `sys_systemconfig` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `value` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_active` int NOT NULL,
  `access` int NOT NULL,
  `key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `inherit` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_userinfo_roles
-- ----------------------------
DROP TABLE IF EXISTS `sys_userinfo_roles`;
CREATE TABLE `sys_userinfo_roles` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userinfo_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userrole_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `userinfo_id` (`userinfo_id`),
  KEY `userrole_id` (`userrole_id`),
  CONSTRAINT `sys_userinfo_roles_ibfk_1` FOREIGN KEY (`userinfo_id`) REFERENCES `sys_users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sys_userinfo_roles_ibfk_2` FOREIGN KEY (`userrole_id`) REFERENCES `sys_roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_userloginlog
-- ----------------------------
DROP TABLE IF EXISTS `sys_userloginlog`;
CREATE TABLE `sys_userloginlog` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` int NOT NULL,
  `ipaddress` varchar(39) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `browser` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `system` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `agent` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `login_type` int NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_userrole_menu
-- ----------------------------
DROP TABLE IF EXISTS `sys_userrole_menu`;
CREATE TABLE `sys_userrole_menu` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userrole_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `menu_id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `userrole_id` (`userrole_id`),
  KEY `menu_id` (`menu_id`),
  CONSTRAINT `sys_userrole_menu_ibfk_1` FOREIGN KEY (`userrole_id`) REFERENCES `sys_roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `sys_userrole_menu_ibfk_2` FOREIGN KEY (`menu_id`) REFERENCES `sys_menus` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sys_users
-- ----------------------------
DROP TABLE IF EXISTS `sys_users`;
CREATE TABLE `sys_users` (
  `id` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime DEFAULT NULL,
  `is_superuser` int NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` int NOT NULL,
  `is_active` int NOT NULL,
  `date_joined` datetime DEFAULT (now()),
  `mode_type` int NOT NULL,
  `avatar` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `nickname` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` int NOT NULL,
  `phone` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creator_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `modifier_id` varchar(150) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `dept_id` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_time` datetime DEFAULT (now()),
  `updated_time` datetime DEFAULT (now()),
  `description` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_sys_users_username` (`username`),
  KEY `dept_id` (`dept_id`),
  CONSTRAINT `sys_users_ibfk_1` FOREIGN KEY (`dept_id`) REFERENCES `sys_departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

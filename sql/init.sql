-- ============================================================
-- 爬虫+自动化办公 数据库脚本
-- 使用：mysql -uroot -p < sql/init.sql
-- ============================================================
CREATE DATABASE IF NOT EXISTS spider_office
  DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;

USE spider_office;

-- 语录表（XPath 爬虫存储）
CREATE TABLE IF NOT EXISTS `quotes` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
  `text`       TEXT         NOT NULL COMMENT '语录内容',
  `author`     VARCHAR(100) NOT NULL COMMENT '作者',
  `tags`       VARCHAR(255) DEFAULT '' COMMENT '标签，逗号分隔',
  `crawled_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_text` (`text`(191)),
  KEY `idx_author` (`author`)
) ENGINE = InnoDB COMMENT = '语录表';

-- 图书表（bs4 爬虫存储）
CREATE TABLE IF NOT EXISTS `books` (
  `id`         INT UNSIGNED  NOT NULL AUTO_INCREMENT COMMENT '主键',
  `title`      VARCHAR(255)  NOT NULL COMMENT '书名',
  `price`      DECIMAL(10,2) NOT NULL COMMENT '价格(英镑)',
  `in_stock`   TINYINT       NOT NULL DEFAULT 1 COMMENT '是否有货',
  `rating`     TINYINT       DEFAULT 0 COMMENT '评分 1-5',
  `crawled_at` DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_title` (`title`(191))
) ENGINE = InnoDB COMMENT = '图书表';

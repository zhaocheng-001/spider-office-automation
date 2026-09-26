# -*- coding: utf-8 -*-
"""MySQL 连接与建表工具（pymysql 原生操作，爬虫存储用）"""
import logging

import pymysql

from config import Config

logger = logging.getLogger("spider.db")


def get_connection():
    """获取 MySQL 连接"""
    return pymysql.connect(**Config.MYSQL)


def init_tables():
    """创建数据库和表（不存在才建）"""
    cfg = dict(Config.MYSQL)
    database = cfg.pop("database")
    conn = pymysql.connect(**cfg)
    with conn.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{database}` "
            "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci"
        )
        cur.execute(f"USE `{database}`")
        # 语录表（xpath 爬虫存这里）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS `quotes` (
              `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
              `text`       TEXT         NOT NULL COMMENT '语录内容',
              `author`     VARCHAR(100) NOT NULL COMMENT '作者',
              `tags`       VARCHAR(255) DEFAULT '' COMMENT '标签，逗号分隔',
              `crawled_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
              PRIMARY KEY (`id`),
              UNIQUE KEY `uk_text` (`text`(191)),
              KEY `idx_author` (`author`)
            ) ENGINE = InnoDB COMMENT = '语录表'
            """
        )
        # 图书表（bs4 爬虫存这里）
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS `books` (
              `id`           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
              `title`        VARCHAR(255)  NOT NULL COMMENT '书名',
              `price`        DECIMAL(10,2) NOT NULL COMMENT '价格(英镑)',
              `in_stock`     TINYINT       NOT NULL DEFAULT 1 COMMENT '是否有货',
              `rating`       TINYINT       DEFAULT 0 COMMENT '评分 1-5',
              `crawled_at`   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取时间',
              PRIMARY KEY (`id`),
              UNIQUE KEY `uk_title` (`title`(191))
            ) ENGINE = InnoDB COMMENT = '图书表'
            """
        )
    conn.commit()
    conn.close()
    logger.info("数据库 %s 初始化完成", database)

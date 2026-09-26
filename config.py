# -*- coding: utf-8 -*-
"""项目统一配置：MySQL、邮箱、爬虫行为参数，支持环境变量覆盖"""
import os


class Config:
    # ---------- MySQL ----------
    MYSQL = {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "12345"),
        "database": os.getenv("MYSQL_DB", "spider_office"),
        "charset": "utf8mb4",
        "autocommit": False,
    }

    # ---------- 爬虫行为 ----------
    REQUEST_DELAY = 1.0      # 每次请求间隔（秒），反爬基础
    REQUEST_TIMEOUT = 10     # 请求超时（秒）
    MAX_RETRIES = 3          # 失败重试次数

    # ---------- 邮箱（smtplib，QQ/163 均可）----------
    # SMTP 服务的授权码（不是邮箱登录密码！QQ邮箱：设置-账户-开启SMTP获取）
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.qq.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))       # 465=SSL, 587=TLS
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")          # 发件人邮箱
    SENDER_AUTH_CODE = os.getenv("SENDER_AUTH_CODE", "")  # 发件人授权码
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")      # 收件人邮箱

    # ---------- 报表输出 ----------
    REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

# -*- coding: utf-8 -*-
"""
smtplib 邮件推送：把生成的 Excel 报表作为附件发送
- 支持 QQ 邮箱 / 163 邮箱 SMTP（需要授权码，不是登录密码）
- 未配置发件账号时自动跳过并提示，不会让定时任务崩掉
配置方式（二选一）：
  1. 环境变量：SENDER_EMAIL / SENDER_AUTH_CODE / RECEIVER_EMAIL
  2. 直接改 config.py 里的默认值
"""
import logging
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from config import Config

logger = logging.getLogger("office.email")


def is_configured():
    """邮箱参数是否齐全"""
    return all([Config.SENDER_EMAIL, Config.SENDER_AUTH_CODE, Config.RECEIVER_EMAIL])


def build_message(subject, body, attachments=()):
    """构造带附件的邮件对象（MIMEMultipart）"""
    msg = MIMEMultipart()
    msg["From"] = formataddr(["爬虫报表机器人", Config.SENDER_EMAIL])
    msg["To"] = formataddr(["报表接收人", Config.RECEIVER_EMAIL])
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    for filepath in attachments:
        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            part = MIMEApplication(f.read())
        part.add_header("Content-Disposition", "attachment",
                        filename=("utf-8", "", filename))  # 中文附件名
        msg.attach(part)
    return msg


def send_email(subject, body, attachments=()):
    """
    发送邮件（SSL 465 端口）。返回 True/False。
    未配置账号时打日志直接返回，保证定时任务不中断。
    """
    if not is_configured():
        logger.warning(
            "邮箱未配置，跳过发送。请设置环境变量 SENDER_EMAIL / SENDER_AUTH_CODE / RECEIVER_EMAIL"
        )
        return False

    msg = build_message(subject, body, attachments)
    try:
        if Config.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=15)
            server.starttls()
        with server:
            server.login(Config.SENDER_EMAIL, Config.SENDER_AUTH_CODE)
            server.sendmail(Config.SENDER_EMAIL, [Config.RECEIVER_EMAIL], msg.as_string())
        logger.info("邮件发送成功：%s（附件 %s 个）", subject, len(attachments))
        return True
    except Exception as e:
        # 授权码错误、网络不通等都在这里捕获
        logger.error("邮件发送失败：%s", e)
        return False


def send_report_email(report_paths):
    """把报表文件作为附件推送的快捷方法"""
    if not report_paths:
        return send_email("爬虫日报", "今日未生成报表（数据库无数据）。")
    names = "、".join(os.path.basename(p) for p in report_paths)
    return send_email(
        subject="爬虫日报：报表已生成",
        body=f"今日共生成 {len(report_paths)} 张报表：{names}\n详见附件。",
        attachments=report_paths,
    )

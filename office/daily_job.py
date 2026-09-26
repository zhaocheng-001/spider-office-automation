# -*- coding: utf-8 -*-
"""
APScheduler 定时任务：爬数据 → 生成 Excel 报表 → 邮件推送，一条龙串联

用法：
  python -m office.daily_job          # 常驻运行，每天 09:30 自动执行
  python -m office.daily_job --now    # 立即执行一次，验证整条链路
"""
import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from office.email_sender import send_report_email
from office.excel_report import generate_all_reports
from spiders.book_spider import BookSpider
from spiders.quote_spider import QuoteSpider

logger = logging.getLogger("office.job")


def run_daily_task():
    """一次完整任务：爬取 → 报表 → 邮件（各环节独立捕获异常，互不拖垮）"""
    logger.info("========== 每日任务开始 ==========")

    # 1. 爬虫入库（分别捕获异常）
    for spider, kwargs in [(QuoteSpider, {"max_pages": 3}), (BookSpider, {"max_pages": 2})]:
        try:
            spider(**kwargs).run()
        except Exception as e:
            logger.error("爬虫 %s 执行失败：%s", spider.__name__, e)

    # 2. 批量生成 Excel 报表
    reports = []
    try:
        reports = generate_all_reports()
    except Exception as e:
        logger.error("报表生成失败：%s", e)

    # 3. 邮件推送（未配置邮箱会自动跳过）
    try:
        send_report_email(reports)
    except Exception as e:
        logger.error("邮件推送失败：%s", e)

    logger.info("========== 每日任务结束 ==========")


def main():
    if "--now" in sys.argv:
        run_daily_task()
        return

    # 常驻定时：每天 09:30 执行
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_task, CronTrigger(hour=9, minute=30),
                      id="daily_report", max_instances=1)
    logger.info("定时任务已启动：每天 09:30 执行（Ctrl+C 退出）")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已停止")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()

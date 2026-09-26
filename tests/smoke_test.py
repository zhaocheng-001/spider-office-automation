# -*- coding: utf-8 -*-
"""
冒烟测试：不依赖外网，验证 解析 / 入库 / 报表 / 邮件构造 / 定时任务注册 全链路
运行：python tests/smoke_test.py
（真实爬取需联网：python -m spiders.quote_spider）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup  # noqa: E402
from lxml import etree  # noqa: E402

passed = failed = 0


def check(name, fn):
    global passed, failed
    try:
        result = fn()
        passed += 1
        print(f"[PASS] {name} -> {result}")
    except Exception as e:
        failed += 1
        print(f"[FAIL] {name} -> {type(e).__name__}: {e}")


# ---------- 测试数据：本地 HTML 片段（模拟目标站页面结构） ----------
QUOTE_HTML = """
<html><body>
<div class="quote"><span class="text">“The world is not fair.”</span>
  <span><small class="author">Albert Einstein</small></span>
  <div class="tags"><a class="tag">life</a><a class="tag">truth</a></div></div>
<div class="quote"><span class="text">“Be yourself.”</span>
  <span><small class="author">Oscar Wilde</small></span>
  <div class="tags"><a class="tag">wisdom</a></div></div>
</body></html>
"""

BOOK_HTML = """
<html><body>
<article class="product_pod"><h3><a title="A Light in the Attic"></a></h3>
  <p class="price_color">£51.77</p>
  <p class="instock availability">In stock</p>
  <p class="star-rating Three"></p></article>
<article class="product_pod"><h3><a title="Tipping the Velvet"></a></h3>
  <p class="price_color">£53.74</p>
  <p class="instock availability">Out of stock</p>
  <p class="star-rating Five"></p></article>
</body></html>
"""


# ---------- 1. 解析测试 ----------
def test_xpath_parse():
    from spiders.quote_spider import QuoteSpider
    spider = QuoteSpider(delay=0)
    next_url = spider.parse(QUOTE_HTML)
    assert len(spider.items) == 2, f"应解析出 2 条，实际 {len(spider.items)}"
    assert spider.items[0]["author"] == "Albert Einstein"
    assert spider.items[0]["tags"] == "life,truth"
    assert next_url is None  # 没有下一页
    return f"{len(spider.items)} 条语录"


def test_bs4_parse():
    from spiders.book_spider import BookSpider
    spider = BookSpider(delay=0)
    spider.parse(BOOK_HTML)
    assert len(spider.items) == 2
    assert spider.items[0]["price"] == 51.77
    assert spider.items[0]["rating"] == 3
    assert spider.items[1]["in_stock"] == 0  # Out of stock
    return f"{len(spider.items)} 本图书"


def test_base_spider_headers():
    """UA 伪装：随机 UA 应来自 UA_POOL"""
    from spiders.base_spider import BaseSpider, UA_POOL
    spider = BaseSpider()
    for _ in range(10):
        ua = spider._headers()["User-Agent"]
        assert ua in UA_POOL
    return "10 次随机 UA 全部合法"


# ---------- 2. MySQL 入库测试 ----------
def test_mysql_roundtrip():
    from db import get_connection, init_tables
    from spiders.quote_spider import QuoteSpider
    init_tables()
    spider = QuoteSpider(delay=0)
    spider.parse(QUOTE_HTML)
    spider.save_to_mysql()

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM quotes WHERE author='Albert Einstein'")
        count_before = cur.fetchone()[0]
        # 再存一次，验证唯一键去重（数量不应增加）
        spider.save_to_mysql()
        cur.execute("SELECT COUNT(*) FROM quotes WHERE author='Albert Einstein'")
        count_after = cur.fetchone()[0]
    conn.close()
    assert count_before == count_after, f"去重失败：{count_before} -> {count_after}"
    return f"入库+去重 OK（重复入库后仍为 {count_after} 条）"


# ---------- 3. Excel 报表测试 ----------
def test_excel_roundtrip():
    from office.excel_report import read_excel, write_report
    path = os.path.join("reports", "_test", "测试报表.xlsx")
    write_report(
        headers=["作者", "语录数", "稿费"],
        rows=[["爱因斯坦", 2, 199.5], ["王尔德", 1, 88.8]],
        filepath=path, title="测试", money_cols=(2,),
    )
    headers, rows = read_excel(path)
    assert headers[0] == "作者" and len(rows) == 2
    return f"写入/读回 OK（{len(rows)} 行）"


# ---------- 4. 邮件构造测试（不真正发送） ----------
def test_email_build():
    from office.email_sender import build_message, is_configured
    configured = is_configured()
    msg = build_message(
        subject="测试邮件", body="正文",
        attachments=[os.path.join("reports", "_test", "测试报表.xlsx")],
    )
    assert "测试邮件" in msg["Subject"]
    assert msg.is_multipart()  # 带附件应为 multipart
    return f"邮件构造 OK（账号已配置={configured}）"


# ---------- 5. 定时任务注册测试 ----------
def test_scheduler():
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger
    from office.daily_job import run_daily_task
    sched = BlockingScheduler()
    sched.add_job(run_daily_task, CronTrigger(hour=9, minute=30), id="daily_report")
    jobs = sched.get_jobs()
    assert len(jobs) == 1
    return "定时任务注册 OK（每天 09:30）"


if __name__ == "__main__":
    check("XPath 解析语录", test_xpath_parse)
    check("bs4 解析图书", test_bs4_parse)
    check("UA 伪装", test_base_spider_headers)
    check("MySQL 入库+去重", test_mysql_roundtrip)
    check("Excel 写入/读回", test_excel_roundtrip)
    check("邮件构造", test_email_build)
    check("APScheduler 注册", test_scheduler)
    print(f"\n结果：{passed} 通过，{failed} 失败")
    sys.exit(1 if failed else 0)

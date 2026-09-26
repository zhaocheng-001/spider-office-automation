# -*- coding: utf-8 -*-
"""
示例爬虫 3：Selenium 基础 —— 抓 JavaScript 动态渲染页面
目标站：https://quotes.toscrape.com/js（页面内容由 JS 动态插入，requests 拿不到）

使用前提：
  1. 本机装有 Chrome 浏览器
  2. pip install selenium（4.6+ 自带 Selenium Manager，自动下载驱动，无需手动配 chromedriver）
运行：python -m spiders.selenium_spider
"""
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from db import get_connection

logger = logging.getLogger("spider.selenium")


def build_driver(headless=True):
    """创建 Chrome 驱动：无头模式 + 常规反检测参数"""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    return webdriver.Chrome(options=options)  # Selenium Manager 自动匹配驱动


class SeleniumSpider:
    """JS 动态页面爬虫：Selenium 等待渲染完成后用 CSS 选择器提取"""

    URL = "https://quotes.toscrape.com/js"

    def crawl(self, timeout=10):
        items = []
        driver = build_driver(headless=True)
        try:
            driver.get(self.URL)
            # 显式等待：直到页面上出现 quote 元素（JS 渲染完成）
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.quote"))
            )
            for box in driver.find_elements(By.CSS_SELECTOR, "div.quote"):
                text = box.find_element(By.CSS_SELECTOR, "span.text").text.strip("“”")
                author = box.find_element(By.CSS_SELECTOR, "small.author").text
                tags = [t.text for t in box.find_elements(By.CSS_SELECTOR, "a.tag")]
                items.append({"text": text, "author": author, "tags": ",".join(tags)})
            logger.info("[selenium] 抓取到 %s 条语录", len(items))
        finally:
            driver.quit()  # 一定要关闭浏览器进程
        return items

    def save_to_mysql(self, items):
        if not items:
            return 0
        sql = ("INSERT IGNORE INTO quotes (`text`, `author`, `tags`) "
               "VALUES (%(text)s, %(author)s, %(tags)s)")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                affected = cur.executemany(sql, items)
            conn.commit()
            logger.info("[selenium] 入库成功（新增 %s）", affected)
            return affected
        finally:
            conn.close()

    def run(self):
        return self.save_to_mysql(self.crawl())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    SeleniumSpider().run()

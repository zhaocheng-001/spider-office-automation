# -*- coding: utf-8 -*-
"""
示例爬虫 2：BeautifulSoup4 解析 + MySQL 存储
目标站：https://books.toscrape.com（练手专用图书商城静态站）
技术点：bs4 的 find / select 提取文本，评分文案转数字
"""
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from db import get_connection
from .base_spider import BaseSpider

logger = logging.getLogger("spider.book")

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BookSpider(BaseSpider):
    """图书爬虫：bs4 解析 → 存 MySQL books 表"""

    BASE_URL = "https://books.toscrape.com"

    def __init__(self, **kwargs):
        super().__init__(name="book", **kwargs)
        self.items = []
        self.current_url = self.BASE_URL  # 当前页地址，用于拼接相对翻页链接

    def parse(self, html):
        """bs4 提取：书名 / 价格 / 库存 / 评分"""
        soup = BeautifulSoup(html, "html.parser")
        for article in soup.select("article.product_pod"):
            title = article.h3.a.get("title", "").strip()
            price_text = article.select_one("p.price_color").get_text(strip=True)
            # 价格形如 £53.74，去掉货币符号转 float
            try:
                price = float(price_text.replace("£", "").replace("Â£", ""))
            except ValueError:
                logger.warning("[%s] 价格解析失败：%s", self.name, price_text)
                continue
            in_stock = article.select_one("p.instock.availability") is not None \
                and "In stock" in article.select_one("p.instock.availability").get_text()
            # 评分在 <p class="star-rating Three"> 里
            rating_class = article.select_one("p.star-rating").get("class", [])
            rating = RATING_MAP.get(rating_class[1], 0) if len(rating_class) > 1 else 0

            self.items.append(
                {"title": title, "price": price,
                 "in_stock": 1 if in_stock else 0, "rating": rating}
            )
        # 相对链接基于当前页地址拼接（第 1 页的 next 是 catalogue/page-2.html，
        # 第 2 页往后是 page-N.html，用 urljoin 统一处理两种情况）
        next_page = soup.select_one("li.next a")
        return urljoin(self.current_url, next_page["href"]) if next_page else None

    def save_to_mysql(self):
        if not self.items:
            logger.info("[%s] 没有可入库的数据", self.name)
            return 0
        sql = ("INSERT IGNORE INTO books (`title`, `price`, `in_stock`, `rating`) "
               "VALUES (%(title)s, %(price)s, %(in_stock)s, %(rating)s)")
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                affected = cur.executemany(sql, self.items)
            conn.commit()
            logger.info("[%s] 入库成功 %s 条（新增 %s）", self.name, len(self.items), affected)
            return affected
        except Exception as e:
            conn.rollback()
            logger.error("[%s] 入库失败：%s", self.name, e)
            return 0
        finally:
            conn.close()

    def run(self, max_pages=2):
        url = f"{self.BASE_URL}/catalogue/page-1.html"
        for page in range(1, max_pages + 1):
            logger.info("[%s] 抓取第 %s 页：%s", self.name, page, url)
            self.current_url = url
            resp = self.fetch(url)
            if resp is None:
                break
            url = self.parse(resp.text)
            if url is None:
                break
        return self.save_to_mysql()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    BookSpider(delay=1.0).run(max_pages=2)

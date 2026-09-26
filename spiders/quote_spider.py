# -*- coding: utf-8 -*-
"""
示例爬虫 1：XPath 解析 + MySQL 存储
目标站：https://quotes.toscrape.com（专门给练手用的静态网站，允许爬取）
技术点：l.etree XPath 提取文本、批量入库（INSERT IGNORE 去重）
"""
import logging

from lxml import etree

from db import get_connection
from .base_spider import BaseSpider

logger = logging.getLogger("spider.quote")


class QuoteSpider(BaseSpider):
    """名人语录爬虫：XPath 解析 → 存 MySQL quotes 表"""

    BASE_URL = "https://quotes.toscrape.com"

    def __init__(self, **kwargs):
        super().__init__(name="quote", **kwargs)
        self.items = []

    def parse(self, html):
        """XPath 提取：语录文本 / 作者 / 标签列表"""
        tree = etree.HTML(html)
        quotes = tree.xpath('//div[@class="quote"]')
        for q in quotes:
            text = "".join(q.xpath('./span[@class="text"]/text()')).strip("“”")
            author = "".join(q.xpath('./span/small[@class="author"]/text()')).strip()
            tags = q.xpath('./div[@class="tags"]/a[@class="tag"]/text()')
            if text and author:
                self.items.append(
                    {"text": text, "author": author, "tags": ",".join(tags)}
                )
        # 返回下一页链接（有则继续翻页）
        next_page = tree.xpath('//li[@class="next"]/a/@href')
        return f"{self.BASE_URL}{next_page[0]}" if next_page else None

    def save_to_mysql(self):
        """批量入库，text 唯一键去重（INSERT IGNORE）"""
        if not self.items:
            logger.info("[%s] 没有可入库的数据", self.name)
            return 0
        sql = ("INSERT IGNORE INTO quotes (`text`, `author`, `tags`) "
               "VALUES (%(text)s, %(author)s, %(tags)s)")
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

    def run(self, max_pages=3):
        """主流程：翻页抓取 → 解析 → 入库"""
        url = self.BASE_URL
        for page in range(1, max_pages + 1):
            logger.info("[%s] 抓取第 %s 页：%s", self.name, page, url)
            resp = self.fetch(url)
            if resp is None:
                break
            url = self.parse(resp.text)  # 解析并取下一页
            if url is None:
                logger.info("[%s] 没有下一页了", self.name)
                break
        return self.save_to_mysql()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    QuoteSpider(delay=1.0).run(max_pages=3)

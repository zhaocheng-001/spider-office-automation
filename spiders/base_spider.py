# -*- coding: utf-8 -*-
"""
通用静态爬虫基类：
- requests 封装：get/post、请求头 headers、随机 UA 伪装
- 状态码处理：2xx 通过、5xx 重试、4xx 记录日志
- 反爬基础：请求延时 + UA 池随机
- 异常捕获：网络异常统一捕获记录，不向外抛
子类只需实现 parse() 和 run()。
"""
import logging
import random
import time

import requests
from requests.exceptions import RequestException

logger = logging.getLogger("spider")

# 常见浏览器的 User-Agent 池（UA 伪装：每次请求随机换一个）
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]


class BaseSpider:
    """所有爬虫的基类，封装请求、反爬、重试逻辑"""

    SUCCESS_CODES = (200, 201)          # 视为成功的状态码
    RETRY_CODES = (500, 502, 503, 504)  # 服务端错误 → 重试

    def __init__(self, name="base", delay=1.0, timeout=10, max_retries=3):
        self.name = name
        self.delay = delay                 # 请求间隔（秒），反爬基础
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()  # Session 自动带 Cookie

    # ---------- 请求头 ----------
    def _headers(self, extra=None):
        """构造请求头：随机 UA + 可额外补充的字段（Referer、Cookie 等）"""
        headers = {"User-Agent": random.choice(UA_POOL)}
        if extra:
            headers.update(extra)
        return headers

    # ---------- 核心请求方法 ----------
    def fetch(self, url, method="get", params=None, data=None, json_body=None,
              extra_headers=None):
        """
        发送 GET/POST 请求，返回 Response 或 None。
        内置：延时 → 随机 UA → 状态码处理 → 异常捕获 → 指数重试。
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self.delay)  # 延时，避免请求过快被封
                resp = self.session.request(
                    method.upper(), url,
                    headers=self._headers(extra_headers),
                    params=params, data=data, json=json_body,
                    timeout=self.timeout,
                )
                # 状态码处理
                if resp.status_code in self.SUCCESS_CODES:
                    resp.encoding = "utf-8"
                    return resp
                if resp.status_code in self.RETRY_CODES and attempt < self.max_retries:
                    logger.warning("[%s] %s 返回 %s，第 %s 次重试",
                                   self.name, url, resp.status_code, attempt)
                    time.sleep(attempt * 2)  # 重试间隔递增
                    continue
                # 4xx 等不可重试的状态码：记日志后放弃
                logger.error("[%s] %s 状态码异常 %s，放弃请求",
                             self.name, url, resp.status_code)
                return None
            except RequestException as e:
                # 网络异常（超时、连接失败等）：捕获记录，重试
                logger.warning("[%s] %s 请求异常：%s（第 %s 次）",
                               self.name, url, e, attempt)
                time.sleep(attempt * 2)
        logger.error("[%s] %s 重试 %s 次仍失败", self.name, url, self.max_retries)
        return None

    # ---------- 子类必须实现 ----------
    def parse(self, resp):
        """解析响应内容，子类实现（xpath / bs4 / 正则均可）"""
        raise NotImplementedError

    def run(self):
        """爬取主流程，子类实现"""
        raise NotImplementedError

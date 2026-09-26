# 爬虫 + 自动化办公脚本

通用静态爬虫 + Excel 报表定时脚本：requests 爬取练习站 → XPath/bs4 解析入库 MySQL → openpyxl 批量生成报表 → APScheduler 定时执行 + smtplib 邮件推送，另附 Selenium 动态页面示例。

## 技术点对照

| 清单项 | 对应代码 |
| ---- | ---- |
| requests get/post、headers、状态码处理 | `spiders/base_spider.py` 的 `fetch()` |
| XPath / bs4 解析，爬静态页存 MySQL | `spiders/quote_spider.py`（XPath）、`spiders/book_spider.py`（bs4） |
| 反爬基础：延时、UA 伪装 | `BaseSpider._headers()` UA 池随机 + `delay` 间隔 + 失败指数重试 |
| Selenium 基础 | `spiders/selenium_spider.py`（抓 JS 动态页，显式等待） |
| 代码重构：封装爬虫类 + 异常捕获 | 所有爬虫继承 `BaseSpider`，网络异常/入库异常统一捕获 |
| openpyxl 读写 Excel、批量生成报表 | `office/excel_report.py` |
| APScheduler 定时 + smtplib 邮件推送 | `office/daily_job.py` + `office/email_sender.py` |

## 项目结构

```
spider-office-automation/
├── spiders/                 # 爬虫模块
│   ├── base_spider.py       #   爬虫基类：UA池/延时/重试/状态码处理/异常捕获
│   ├── quote_spider.py      #   XPath 爬虫 → MySQL quotes 表
│   ├── book_spider.py       #   bs4 爬虫 → MySQL books 表
│   └── selenium_spider.py   #   Selenium 动态页示例（JS 渲染）
├── office/                  # 自动化办公模块
│   ├── excel_report.py      #   openpyxl 报表：样式、¥格式、自适应列宽、批量生成
│   ├── email_sender.py      #   smtplib 邮件推送（附件、授权码、未配置自动跳过）
│   └── daily_job.py         #   APScheduler：爬取→报表→邮件 一条龙，每天 09:30
├── db.py                    # MySQL 连接与建表
├── config.py                # 配置：MySQL/邮箱/爬虫参数（支持环境变量）
├── sql/init.sql             # 建库建表脚本
├── tests/smoke_test.py      # 冒烟测试：解析/入库/报表/邮件构造 全链路
├── reports/                 # 报表输出目录（按日期分文件夹）
└── requirements.txt
```

## 快速开始

```bash
cd spider-office-automation
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

修改 `config.py` 中 MySQL 密码（默认 root/12345），然后：

```bash
# 1. 初始化数据库（spider_office 库 + quotes/books 表）
python -c "from db import init_tables; init_tables()"

# 2. 运行爬虫（requests + XPath，练手站 quotes.toscrape.com）
python -m spiders.quote_spider

# 3. bs4 爬虫（图书站）
python -m spiders.book_spider

# 4. Selenium 动态页示例（需本机装有 Chrome）
python -m spiders.selenium_spider

# 5. 立即执行一次「爬取→报表→邮件」完整链路
python -m office.daily_job --now

# 6. 启动常驻定时任务（每天 09:30 自动执行）
python -m office.daily_job
```

## 邮箱配置（推送报表用）

以 QQ 邮箱为例：设置 → 账户 → 开启 SMTP 服务 → 获取**授权码**，然后设置环境变量：

```bash
set SENDER_EMAIL=你的QQ号@qq.com
set SENDER_AUTH_CODE=smtp授权码
set RECEIVER_EMAIL=收件邮箱
```

未配置时定时任务照常执行，只是跳过发信环节。

## 数据来源说明

- `quotes.toscrape.com` / `books.toscrape.com`：Scrapy 官方提供的**爬虫练习站**，专供学习，允许抓取
- Selenium 示例抓取的 `/js` 页面内容由 JavaScript 动态渲染，`requests` 拿不到内容，正好演示两者的区别

## 反爬与合规

- 每次请求随机 User-Agent（5 个浏览器 UA 轮换）
- 请求间隔 1 秒 + 失败指数退避重试（2s/4s/6s）
- 只爬公开静态页面、控制频率，遵守 robots.txt 精神；商业用途请确认目标站点的爬取条款

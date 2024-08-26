#!/bin/env python3

# 多进程，一个进程负责每日定时抓取数据
# 一个进程提供 http 服务

import os
import logging
from multiprocessing import Process

from log import init_logging
init_logging()

from model import migrate_db, get_config
from crawler import Crawler
from server import start_server


def crawl():
    Crawler().run()


if __name__ == "__main__":
    cfg = get_config()
    migrate_db(cfg.db.engine)

    crawl_process = Process(target=crawl, daemon=True)
    crawl_process.start()

    try:
        start_server()
    except KeyboardInterrupt:
        logging.info("keyboard interrupt")
    except Exception as e:
        logging.error(e)

    if crawl_process.is_alive():
        logging.info("kill crawler process")
        crawl_process.kill()

    logging.info("bye!")


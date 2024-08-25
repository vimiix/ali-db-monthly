#!/bin/env python3

# 多进程，一个进程负责每日定时抓取数据
# 一个进程提供 http 服务

import os
import logging
from multiprocessing import Process

from log import init_logging
init_logging()

from model import Config, migrate_db
from crawler import Crawler
from server import start_server


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
DEV_CONFIG_NAME = os.path.join(PROJECT_DIR, "config.ini")
PROD_CONFIG_NAME = os.path.join(PROJECT_DIR, "config-prod.ini")


def crawl(cfg_file: str):
    Crawler(Config(cfg_file)).run()


if __name__ == "__main__":
    config_filename = (
        PROD_CONFIG_NAME if os.getenv("ENV_PRODUCTION") else DEV_CONFIG_NAME
    )

    cfg = Config(config_filename)
    migrate_db(cfg.db.engine)

    crawl_process = Process(target=crawl, args=(config_filename,), daemon=True)
    crawl_process.start()

    try:
        start_server(cfg.server)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)

    if crawl_process.is_alive():
        logging.info("kill crawler process")
        crawl_process.kill()

    logging.info("bye!")


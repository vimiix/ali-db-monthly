#!/bin/env python3

# 多进程，一个进程负责每日定时抓取数据
# 一个进程提供 http 服务

import os
import logging
from multiprocessing import Pool, Value

from model import Config
from crawler import Crawler


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
DEV_CONFIG_NAME = os.path.join(PROJECT_DIR, "config.ini")
PROD_CONFIG_NAME = os.path.join(PROJECT_DIR, "config-prod.ini")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(module)s:%(lineno)d] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def crawl(cfg_file: str):
    logging.info("Start crawler")
    Crawler(Config(cfg_file)).run()


def serve(cfg_file: str):
    logging.info("Start server")
    pass


if __name__ == "__main__":
    config_filename = (
        PROD_CONFIG_NAME if os.getenv("ENV_PRODUCTION") else DEV_CONFIG_NAME
    )

    p = Pool(2)
    p.apply_async(crawl, args=(config_filename,))
    p.apply_async(serve, args=(config_filename,))
    p.close()
    p.join()

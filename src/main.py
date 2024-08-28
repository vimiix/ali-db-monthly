#!/bin/env python3

import os
import threading
import logging
logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(module)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

from diskcache import Cache

from model import migrate_db, get_config
from crawler import Crawler
from server import start_server


if __name__ == "__main__":
    cfg = get_config()
    migrate_db(cfg.db.engine)
    cache = Cache(cfg.common.cache_dir)

    c = Crawler(cfg.db.engine, cache)
    crawler_thread = threading.Thread(target=c.run, daemon=True)
    crawler_thread.start()

    try:
        start_server(cache)
    except KeyboardInterrupt:
        logging.info("keyboard interrupt")
    except Exception as e:
        logging.error(e)

    logging.info("bye!")


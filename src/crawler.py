import schedule
import requests
from bs4 import BeautifulSoup
from sqlalchemy import select, Engine
from sqlalchemy.orm import sessionmaker
from diskcache import Cache

import time
import re
import logging
from datetime import date
from typing import List

from model import Config, Artical


BASE_URL = "http://mysql.taobao.org/monthly/"


class Crawler:

    def __init__(self, engine:Engine, cache: Cache) -> None:
        self.engine = engine
        self.cache = cache
        self.link_re = re.compile(r"/monthly/\d+/\d+")
        self.date_re = re.compile(r".*/(\d+)/(\d+)/(\d+)")

    def run(self) -> None:
        logging.info("start crawler")
        self.crawl()

        logging.info("schedule to crawl every day at 00:00")
        schedule.every().day.at("00:00").do(self.crawl)
        while True:
            try:
                schedule.run_pending()
                time.sleep(10)
            except KeyboardInterrupt:
                return
            except Exception as e:
                logging.error(e)

    def crawl(self) -> None:
        la = self._last_artical()
        if la:
            logging.info("last artical date: %s", la.create_date)
        else:
            logging.info("crawl all articals")
        self._update_after(la)

    def _update_after(self, last_artical: Artical):
        logging.info("updating articals")
        monthly_links = self._fetch_links(BASE_URL)
        if not monthly_links:
            logging.error("no monthly links found")
            return

        articals = []
        should_continue = True
        for link in monthly_links:
            if not should_continue:
                break

            links = self._fetch_links(link)
            links.reverse()
            for link in links:
                artical = self._parse_artical(link)
                if not artical:
                    continue

                if not last_artical:
                    articals.append(artical)
                    continue

                if artical.create_date > last_artical.create_date:
                    articals.append(artical)
                else:
                    # No need to continue crawling for old data
                    should_continue = False
                    break

        if not articals:
            logging.info("no new articals to update")
            return

        self._save_articals(articals)
        logging.info(f"Saved {len(articals)} articals")
        self.cache.clear()

    def _save_articals(self, articals: List[Artical]):
        with sessionmaker(self.engine)() as sess:
            sess.add_all(articals)
            sess.commit()

    def _parse_artical(self, url: str) -> Artical:
        resp = requests.get(url)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        block_div = soup.find("div", attrs={"class": "block"})
        if not block_div:
            logging.error("no block div found")
            return None

        logging.debug("Parsing artical: %s", url)
        title = block_div.find("h2").get_text(strip=True)
        author = block_div.find("p").get_text(strip=True)[len("Author:") :].strip()
        date_segs = self.date_re.findall(url)[0]
        create_date = date(int(date_segs[0]), int(date_segs[1]), int(date_segs[2]))
        tag = self._analyse_tag(title)
        return Artical(
            title=title, tag=tag, url=url, author=author, create_date=create_date
        )

    def _analyse_tag(self, title: str) -> str:
        lower_title = title.lower()
        if "polardb" in lower_title:
            return "PolarDB"
        elif (
            "mysql" in lower_title
            or "maria" in lower_title
            or "innodb" in lower_title
            or "tokudb" in lower_title
        ):
            return "MySQL"
        elif (
            "postgres" in lower_title or "pgsql" in lower_title or "gpdb" in lower_title
        ):
            return "PostgreSQL"
        elif "alisql" in lower_title:
            return "AliSQL"
        elif "mariadb" in lower_title:
            return "MySQL"
        elif "mongodb" in lower_title:
            return "MongoDB"
        elif "redis" in lower_title:
            return "Redis"
        elif "mssql" in lower_title or "sql server" in lower_title:
            return "SQL Server"
        return "common"

    def _fetch_links(self, url: str) -> List[str]:
        res = []
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.find_all("a", href=self.link_re)
        for link in links:
            res.append(BASE_URL + link["href"][len("/monthly/") :])
        return res

    def _last_artical(self) -> Artical:
        with sessionmaker(self.engine)() as sess:
            stmt = select(Artical).order_by(Artical.create_date.desc()).limit(1)
            res = sess.execute(stmt).scalars().first()
        return res

if __name__ == "__main__":
    cfg = Config("config.ini")
    Crawler(cfg).run()

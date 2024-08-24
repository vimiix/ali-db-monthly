import schedule
import requests
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.orm import Session

import re
import logging
from datetime import date
from typing import List

from model import Config, Artical


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(module)s:%(lineno)d] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


BASE_URL = "http://mysql.taobao.org/monthly/"


class Crawler:

    def __init__(self, cfg: Config) -> None:
        self.engine = cfg.db.engine
        self.link_re = re.compile(r"/monthly/\d+/\d+")
        self.date_re = re.compile(r".*/(\d+)/(\d+)/(\d+)")

    def run(self) -> None:
        self.crawl()

        while True:
            schedule.every().day.at("00:00").do(self.crawl)
            schedule.run_pending()

    def crawl(self) -> None:
        la = self._last_artical()
        logging.info("Last artical: %s", la)
        self._update_after(la)

    def _update_after(self, last_artical: Artical):
        logging.info("Updating articals")
        monthly_links = self._fetch_links(BASE_URL)
        if not monthly_links:
            logging.error("No monthly links found")
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
            logging.info("No new articals found")
            return

        self._save_articals(articals)
        logging.info(f"Saved {len(articals)} articals")

    def _save_articals(self, articals: List[Artical]):
        with Session(self.engine) as sess:
            sess.add_all(articals)
            sess.commit()

    def _parse_artical(self, url: str) -> Artical:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        block_div = soup.find("div", attrs={"class": "block"})
        if not block_div:
            logging.error("No block div found")
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
        with Session(self.engine) as sess:
            stmt = select(Artical).order_by(Artical.create_date.desc()).limit(1)
            res = sess.execute(stmt).scalars().first()
            return res

if __name__ == "__main__":
    cfg = Config("config.ini")
    Crawler(cfg).run()

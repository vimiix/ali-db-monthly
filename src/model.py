
import os
import logging
from configparser import ConfigParser
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Date

Base = declarative_base()


class Config:
    config_filename: str
    db: "Database"

    def __init__(self, config_filename) -> None:
        self.config_filename = config_filename
        if not os.path.exists(self.config_filename):
            raise FileNotFoundError(self.config_filename)

        parser = ConfigParser()
        parser.read(self.config_filename)
        self.db = Database(parser["database"])

class Database:
    host: str
    port: int
    user: str
    password: str
    db: str

    def __init__(self, dbcfg) -> None:
        self.host = dbcfg.get("host", "localhost")
        self.port = dbcfg.get("port", 3306)
        self.user = dbcfg.get("user", "root")
        self.password = dbcfg.get("password")
        self.db = dbcfg.get("dbname", "mysql")
        logging.info("create db engine")
        self.engine = create_engine(self.connect_string(),
                                    echo=dbcfg.getboolean("echo", False))
        self.migrate()

    def __repr__(self) -> str:
        return f"Database(host={self.host}, port={self.port}, user={self.user}, db={self.db})"

    def connect_string(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    def migrate(self):
        logging.info("migrate database")
        Base.metadata.create_all(self.engine)

class Artical(Base):
    __tablename__ = "t_articals"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    tag: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(200))
    author: Mapped[str] = mapped_column(String(100))
    create_date: Mapped[date] = mapped_column(Date)

    def __repr__(self) -> str:
        return f"Artical(id={self.id!r}, title={self.title!r}, tag={self.tag}, url={self.url}, author={self.author})"


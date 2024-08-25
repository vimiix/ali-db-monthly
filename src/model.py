
import os
import logging
from configparser import ConfigParser, SectionProxy
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Date

Base = declarative_base()


class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    db: str

    def __init__(self, dbcfg: SectionProxy) -> None:
        self.host = dbcfg.get("host", "localhost")
        self.port = dbcfg.get("port", 3306)
        self.user = dbcfg.get("user", "root")
        self.password = dbcfg.get("password")
        self.db = dbcfg.get("dbname", "mysql")
        self.echo = dbcfg.getboolean("echo", False)
        self._engine = None

    def __repr__(self) -> str:
        return f"DatabaseConfig(host={self.host}, port={self.port}, user={self.user}, db={self.db})"

    def connect_string(self) -> str:
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def engine(self) -> str:
        if self._engine is None:
            self._engine = create_engine(self.connect_string(), echo=self.echo)
        return self._engine


class ServerConfig:
    host: str
    port: int
    debug: bool

    def __init__(self, servercfg: SectionProxy) -> None:
        self.host = servercfg.get("listen_host", "127.0.0.1")
        self.port = servercfg.getint("port", 8080)
        self.debug = servercfg.getboolean("debug", False)

    def __repr__(self) -> str:
        return f"ServerConfig(host={self.host}, port={self.port})"

class Config:
    config_filename: str
    db: "DatabaseConfig"
    server: "ServerConfig"

    def __init__(self, config_filename) -> None:
        self.config_filename = config_filename
        if not os.path.exists(self.config_filename):
            raise FileNotFoundError(self.config_filename)

        parser = ConfigParser()
        parser.read(self.config_filename)
        self.db = DatabaseConfig(parser["database"])
        self.server = ServerConfig(parser["server"])

def migrate_db(engine):
    Base.metadata.create_all(engine)

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


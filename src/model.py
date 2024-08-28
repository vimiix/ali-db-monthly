import os
from configparser import ConfigParser, SectionProxy
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Date, Engine

Base = declarative_base()

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
DEV_CONFIG_NAME = os.path.join(PROJECT_DIR, "config.ini")
PROD_CONFIG_NAME = os.path.join(PROJECT_DIR, "config-prod.ini")


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
    def engine(self) -> Engine:
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


class CommonConfig:
    cache_dir: str

    def __init__(self, commoncfg: SectionProxy) -> None:
        self.cache_dir = commoncfg.get("cache_dir", "./cache")

    def __repr__(self) -> str:
        return f"CommonConfig(cache_dir={self.cache_file})"


class Config:
    config_filename: str
    common: "CommonConfig"
    db: "DatabaseConfig"
    server: "ServerConfig"

    def __init__(self, config_filename) -> None:
        self.config_filename = config_filename
        if not os.path.exists(self.config_filename):
            raise FileNotFoundError(self.config_filename)

        parser = ConfigParser()
        parser.read(self.config_filename)
        self.common = CommonConfig(parser["common"])
        self.db = DatabaseConfig(parser["database"])
        self.server = ServerConfig(parser["server"])


_default_cfg = None


def load_config() -> Config:
    config_filename = (
        PROD_CONFIG_NAME if os.getenv("ENV_PRODUCTION") else DEV_CONFIG_NAME
    )
    return Config(config_filename)


def get_config() -> Config:
    global _default_cfg
    if _default_cfg is None:
        _default_cfg = load_config()
    return _default_cfg


def migrate_db(engine):
    Base.metadata.create_all(engine)


tag_colors = [
    '#007bff',
    '#28a745',
    '#6c757d',
    '#ffc107',
    '#dc3545',
    '#17a2b8',
    '#1305ad',
    '#9b59b6',
    '#2874a6',
    '#e67e22',
]

def get_tag_color(tag: str) -> str:
    return tag_colors[abs(hash(tag)) % len(tag_colors)]


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

    def keys(self):
        return ["id", "title", "tag", "url", "author", "create_date"]

    def __getitem__(self, item):
        return getattr(self, item)

    def to_dict(self) -> dict:
        d = {key: getattr(self, key) for key in self.keys()}
        d['tag_color'] = get_tag_color(d['tag'])
        return d

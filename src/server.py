from flask import (
    Flask, request, jsonify,
    render_template,
)
from datetime import datetime
from gevent import pywsgi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
from diskcache import Cache

import logging
import math
from typing import List, Tuple

from model import Artical, get_config

app = Flask(__name__)
cfg = get_config()
server_cfg = cfg.server
cache = None

def toint(value, fallback: int) -> int:
    try:
        return int(value)
    except ValueError:
        return fallback


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/articals", methods=["GET"])
def articals():
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    tag = request.args.get("tag")
    if tag.lower() == "all":
        tag = None
    page = request.args.get("page", 1)

    articals, total = get_articals(start_date, end_date, tag, page)
    articals = [a.to_dict() for a in articals]
    return jsonify(articals=articals, total_pages=math.ceil(total / 10))

def get_articals(start_date: str, end_date:str, tag:str, page: int) -> Tuple[List[Artical], int]:
    cache_key = f"articals_{start_date}_{end_date}_{tag}_{page}"
    try:
        return cache[cache_key]
    except KeyError:
        pass
    logging.info("not found in cache: %s", cache_key)
    offset = (toint(page, 1) - 1) * 10
    limit = request.args.get("limit", 10)
    filters = []
    if start_date:
        filters.append(Artical.create_date >= start_date)
    if end_date:
        filters.append(Artical.create_date <= end_date)
    if tag:
        filters.append(Artical.tag == tag)
    with sessionmaker(cfg.db.engine)() as sess:
        stmt = (
            select(Artical)
            .order_by(Artical.create_date.desc())
            .filter(*filters)
            .offset(offset)
            .limit(toint(limit, 10))
        )
        articals = sess.execute(stmt).scalars().all()
        total = sess.execute(select(func.count(Artical.id)).filter(*filters)).scalar()

    cache.set(cache_key, (articals, total))
    return (articals, total)


def get_tags():
    cache_key = "/api/tags"
    try:
        return cache[cache_key]
    except KeyError:
        pass
    logging.info("not found in cache: %s", cache_key)
    with sessionmaker(cfg.db.engine)() as sess:
        stmt = select(Artical.tag).distinct().order_by(Artical.tag)
        tags = sess.execute(stmt).scalars().all()
    cache.set(cache_key, tags)
    return tags

@app.route("/api/tags", methods=["GET"])
def tags():
    return jsonify(tags=get_tags())


class Handler(pywsgi.WSGIHandler):

    def log_request(self):
        now = datetime.now().replace(microsecond=0)
        length = self.response_length or '-'
        if self.time_finish:
            delta = '%.6f' % (self.time_finish - self.time_start)
        else:
            delta = '-'

        client_address = self.client_address[0] if isinstance(self.client_address, tuple) else self.client_address

        x_forwarded_for = self.headers.get('X-Forwarded-For')
        if x_forwarded_for:
            client_address = x_forwarded_for.split(',')[0]
        return '%s - - [%s] "%s" %s %s %s' % (
            client_address or '-',
            now,
            self.requestline or '',
            (self._orig_status or self.status or '000').split()[0],
            length,
            delta)

def start_server(_cache: Cache):
    global cache
    cache = _cache
    logging.info("start http server at http://%s:%s", server_cfg.host, server_cfg.port)
    server = pywsgi.WSGIServer(
        (server_cfg.host, server_cfg.port), app,
        log=logging.getLogger(), handler_class=Handler
    )
    server.serve_forever()


if __name__ == "__main__":
    app.run(debug=True)

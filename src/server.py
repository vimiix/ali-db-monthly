from flask import (
    Flask, request, jsonify,
    render_template
)
from flask_cors import CORS
from gevent import pywsgi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func

import logging
import math

from model import Artical, get_config

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
cfg = get_config()
server_cfg = cfg.server
session = sessionmaker(cfg.db.engine)

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
    offset = (toint(page, 1) - 1) * 10
    limit = request.args.get("limit", 10)
    filters = []
    if start_date:
        filters.append(Artical.create_date >= start_date)
    if end_date:
        filters.append(Artical.create_date <= end_date)
    if tag:
        filters.append(Artical.tag == tag)

    with session() as sess:
        stmt = (
            select(Artical)
            .order_by(Artical.create_date.desc())
            .filter(*filters)
            .offset(offset)
            .limit(toint(limit, 10))
        )
        articals = sess.execute(stmt).scalars().all()
        total = sess.execute(select(func.count(Artical.id)).filter(*filters)).scalar()

    articals = [a.to_dict() for a in articals]
    return jsonify(articals=articals, total_pages=math.ceil(total / 10))


@app.route("/api/tags", methods=["GET"])
def tags():
    with session() as sess:
        stmt = select(Artical.tag).distinct().order_by(Artical.tag)
        tags = sess.execute(stmt).scalars().all()
    return jsonify(tags=tags)


def start_server():
    logging.info("start http server at http://%s:%s", server_cfg.host, server_cfg.port)
    server = pywsgi.WSGIServer(
        (server_cfg.host, server_cfg.port), app, log=logging.getLogger()
    )
    server.serve_forever()


if __name__ == "__main__":
    app.run(debug=True)

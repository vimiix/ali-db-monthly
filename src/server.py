
from flask import Flask
from gevent import pywsgi
from werkzeug.serving import WSGIRequestHandler

import logging

from model import ServerConfig

class CustomRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        getattr(logging, type)(message % args)

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Hello World!</h1>"


def start_server(cfg: ServerConfig):
    app.debug = cfg.debug
    logging.info("start http server at http://%s:%s", cfg.host, cfg.port)
    server = pywsgi.WSGIServer((cfg.host, cfg.port), app, log=logging.getLogger())
    server.serve_forever()


if __name__ == "__main__":
    app.run(debug=True)

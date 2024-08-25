
import logging

def init_logging(process: str=""):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(module)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
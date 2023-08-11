"""Subway App"""
import logging
from threading import Thread
from startup import feed_loader, create_default_app
from helper_functions import instantiate_logger

instantiate_logger(logging.getLogger())
app = create_default_app(100)

if __name__ == "__main__":
    threads = [
        Thread(target=feed_loader),
        Thread(target=app.run, kwargs={"host": "127.0.0.1", "port": 80}),
    ]
    for thread in threads:
        thread.start()

    app.run("0.0.0.0", 80, True)

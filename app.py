"""Subway App"""
import os
from threading import Thread
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from flask_apps import FlaskApp, FEED, HOST, PORT
from test import feed_loader


def create_app(key: str, proxies: int = 10) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None."""
    _app = Flask(__name__)
    flask_app = FlaskApp(_app, FEED, key)
    _app = flask_app.app
    # _app.wsgi_app = ProxyFix(
    #     _app.wsgi_app,
    #     x_for=proxies,
    #     x_proto=proxies,
    #     x_host=proxies,
    #     x_prefix=proxies,
    # )
    return _app


def set_env(env_dict: dict[str, str] = None) -> None:
    """Set environment variables.

    Args:
        env_dict (dict[str, str], optional): Dictionary of environment variables. Defaults to None.
    """
    env_dict = env_dict or {
        "SUBWAY": "0,1",
        "RAPID_TRANSIT": "0,1,4",
        "COMMUTER_RAIL": "2",
        "BUS": "3",
        "FERRY": "4",
        "ALL_ROUTES": "0,1,2,3,4",
        "LIST_KEYS": "SUBWAY,RAPID_TRANSIT,COMMUTER_RAIL,BUS,FERRY,ALL_ROUTES",
    }
    for key, value in env_dict.items():
        os.environ[key] = value


set_env()
app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(
    create_app("SUBWAY").wsgi_app,
    {
        f"/{key.lower()}": create_app(key).wsgi_app
        for key in os.environ["LIST_KEYS"].split(",")
    },
)

# SW_APP = create_app("SUBWAY")
# RT_APP = create_app("RAPID_TRANSIT")
# CR_APP = create_app("COMMUTER_RAIL")
# BUS_APP = create_app("BUS")
# FRR_APP = create_app("FERRY")
# ALL_APP = create_app("ALL_ROUTES")


if __name__ == "__main__":
    # threads = [
    #     Thread(target=app.run, kwargs={"host": "127.0.0.1", "port": PORT + i})
    #     for i, app in enumerate([SW_APP, RT_APP, CR_APP, BUS_APP, FRR_APP, ALL_APP])
    # ]
    # for thread in threads + [Thread(target=feed_loader)]:
    #     thread.start()
    threads = [
        Thread(target=feed_loader),
        Thread(target=app.run, kwargs={"host": "127.0.0.1", "port": 80}),
    ]
    for thread in threads:
        thread.start()

"""Subway App"""
import os
from threading import Thread
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_apps import FlaskApp, FEED, HOST, PORT


def create_app(key: str = None) -> Flask:
    """Create app for a given key

    Args:
        key (str, optional): Key for the app. Defaults to None."""

    key = key or os.environ.get("ROUTE_KEY")
    app = FlaskApp(Flask(__name__), FEED, key).app
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    return app


SW_APP = create_app("SUBWAY")
RT_APP = create_app("RAPID_TRANSIT")
CR_APP = create_app("COMMUTER_RAIL")
BUS_APP = create_app("BUS")
FRR_APP = create_app("FERRY")
ALL_APP = create_app("ALL")


if __name__ == "__main__":
    threads = [
        Thread(target=app.run, kwargs={"host": HOST, "port": PORT + i})
        for i, app in enumerate([SW_APP, RT_APP, CR_APP, BUS_APP, FRR_APP, ALL_APP])
    ]
    for thread in threads:
        thread.start()

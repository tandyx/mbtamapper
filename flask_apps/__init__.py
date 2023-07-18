"""init"""
# pylint: disable=unused-import
from dotenv import load_dotenv
from .all_route_flask import flask_app as all_app
from .ferry_route_flask import flask_app as ferry_app
from .rapid_routes import flask_app as rapid_app
from .subway_route import flask_app as subway_app
from .cr_app_flask import flask_app as cr_app
from .bus_route_flask import flask_app as bus_app

load_dotenv()

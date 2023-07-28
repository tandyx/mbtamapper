"""init"""
# pylint: disable=unused-import
from dotenv import load_dotenv
from .flask_app import FlaskApp
from .executables import FEED, HOST

load_dotenv()

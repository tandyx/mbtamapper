"""Flask app for the feed app."""
# pylint: disable=unused-import
from dotenv import load_dotenv
from .flask_app import FlaskApp
from .flask_app import feed

load_dotenv()

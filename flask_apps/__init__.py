"""init"""
# pylint: disable=unused-import
from dotenv import load_dotenv
from .flask_app import FlaskApp
from .blueprint import BluePrintApp

load_dotenv()

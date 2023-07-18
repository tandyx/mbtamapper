# pylint: disable=unused-import
from dotenv import load_dotenv
from .all_app import KEY as ALL_KEY, app as all_app
from .ferry_app import KEY as FERRY_KEY, app as ferry_app
from .rapid_app import KEY as RAPID_KEY, app as rapid_app
from .subway_app import KEY as SUBWAY_KEY, app as subway_app
from .cr_app import KEY as CR_KEY, app as cr_app
from .bus_app import KEY as BUS_KEY, app as bus_app

load_dotenv()

"""initialize and import all gtfs_schedule business objects"""

# pylint: disable=unused-import
import typing as t

from .agency import Agency
from .alert import Alert
from .base import Base
from .calendar import Calendar
from .calendar_attribute import CalendarAttribute
from .calendar_date import CalendarDate
from .facility import Facility
from .facility_property import FacilityProperty
from .linked_datasets import LinkedDataset
from .multi_route_trip import MultiRouteTrip
from .prediction import Prediction
from .route import Route
from .shape import Shape
from .shape_point import ShapePoint
from .stop import Stop
from .stop_time import StopTime
from .transfer import Transfer
from .trip import Trip
from .vehicle import Vehicle


RealtimeOrms = t.Type[Alert | Vehicle | Prediction]
ScheduleOrms = t.Type[
    Agency
    | Calendar
    | CalendarAttribute
    | CalendarDate
    | Facility
    | FacilityProperty
    | LinkedDataset
    | MultiRouteTrip
    | Route
    | Shape
    | ShapePoint
    | Stop
    | StopTime
    | Transfer
    | Trip
]

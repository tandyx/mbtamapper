from gtfs_loader import Feed
from gtfs_schedule import Stop, Route, Trip, StopTime, Shape
from sqlalchemy import select
from geojson import FeatureCollection, Feature, Point, LineString, dump


feed = Feed("https://cdn.mbta.com/MBTA_GTFS.zip", "2")
shapes = feed.session.execute(feed.queries.parent_stops_query).all()

shapes[0][0].as_dict()

print()

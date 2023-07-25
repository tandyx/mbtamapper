"""test"""
import requests
from google.transit.gtfs_realtime_pb2 import FeedMessage


def main() -> None:
    """main"""
    feed = FeedMessage()
    response = requests.get("https://cdn.mbta.com/realtime/Alerts.pb", timeout=10)
    feed.ParseFromString(response.content)
    print()


if __name__ == "__main__":
    main()

import datetime

from src.models.Coordinate import Coordinate
from src.time_helpers import parse_to_utc_datetime


class PointInTime:

    def __init__(self, data: dict):
        self._raw_data = data
        self.coordinate: Coordinate = Coordinate(data.get('point'))
        self.timestamp_utc: datetime.datetime = parse_to_utc_datetime(data.get('time'))

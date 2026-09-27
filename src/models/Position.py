import datetime

from src.models.Coordinate import Coordinate


class Position:

    def __init__(self, position: dict):
        self._raw_position = position.get('position', dict())
        self.coordinate: Coordinate = Coordinate(self._raw_position.get('LatLng', ','))
        self.accuracy_m: float = 0
        self.altitude_m: float = 0
        self.source: str = 'UNKNOWN'
        self.timestamp_utc: datetime.datetime
        self.speed_mps: float = 0.0

        self.accuracy_m = self._raw_position.get('accuracyMeters')
        self.altitude_m = self._raw_position.get('altitudeMeters', None)
        self.source = self._raw_position.get('source', 'UNKNOWN')
        timestamp_str = self._raw_position.get('timestamp', None)
        if timestamp_str:
            self.timestamp_utc = datetime.datetime.fromisoformat(timestamp_str)
            self.timestamp_utc = self.timestamp_utc.astimezone(datetime.timezone.utc)

        self.speed_mps = self._raw_position.get('speedMetersPerSecond', 0.0)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'({self.coordinate}) @ {self.timestamp_utc.isoformat()}'

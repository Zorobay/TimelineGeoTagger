import abc
import datetime
import enum
from abc import abstractmethod

from src.models.Coordinate import Coordinate
from src.models.PointInTime import PointInTime
from src.time_helpers import parse_to_utc_datetime, diff_in_seconds


class TransportationType(enum.StrEnum):
    UNKNOWN = "UNKNOWN_ACTIVITY_TYPE"

    # on foot / human-powered
    WALKING = "WALKING"
    RUNNING = "RUNNING"
    HIKING = "HIKING"
    CYCLING = "CYCLING"
    IN_WHEELCHAIR = "IN_WHEELCHAIR"
    SKIING = "SKIING"
    SNOWBOARDING = "SNOWBOARDING"
    HORSEBACK_RIDING = "HORSEBACK_RIDING"

    # road
    IN_PASSENGER_VEHICLE = "IN_PASSENGER_VEHICLE"
    IN_VEHICLE = "IN_VEHICLE"
    IN_TAXI = "IN_TAXI"
    IN_BUS = "IN_BUS"
    MOTORCYCLING = "MOTORCYCLING"

    # rail / cable
    IN_TRAIN = "IN_TRAIN"
    IN_SUBWAY = "IN_SUBWAY"
    IN_TRAM = "IN_TRAM"
    IN_CABLECAR = "IN_CABLECAR"
    IN_FUNICULAR = "IN_FUNICULAR"
    IN_GONDOLA_LIFT = "IN_GONDOLA_LIFT"

    # water
    IN_FERRY = "IN_FERRY"
    BOATING = "BOATING"
    SAILING = "SAILING"
    KAYAKING = "KAYAKING"
    ROWING = "ROWING"
    SURFING = "SURFING"
    SWIMMING = "SWIMMING"

    # air
    FLYING = "FLYING"


class SemanticSegment(abc.ABC):

    def __init__(self, data: dict):
        self._raw_data = data
        self.start_time_utc: datetime.datetime
        self.end_time_utc: datetime.datetime

        self.start_time_utc = parse_to_utc_datetime(data.get('startTime'))
        self.end_time_utc = parse_to_utc_datetime(data.get('endTime'))

    @abstractmethod
    def sort_key(self, timestamp: datetime.datetime) -> float:
        """Returns the minimum difference in seconds between 'timestamp' and any internal timestamps"""
        return min(diff_in_seconds(timestamp, self.start_time_utc), diff_in_seconds(timestamp, self.end_time_utc))

    @abstractmethod
    def get_best_coordinate(self, timestamp: datetime.datetime) -> Coordinate:
        """Returns the coordinate that best matches in time with 'timestamp'"""


class PathSegment(SemanticSegment):

    def __init__(self, data: dict):
        super().__init__(data)

        self.points: list[PointInTime] = [PointInTime(pit) for pit in data.get('timelinePath', [])]

    def sort_key(self, timestamp: datetime.datetime) -> float:
        return min([diff_in_seconds(timestamp, p.timestamp_utc) for p in self.points])

    def get_best_coordinate(self, timestamp: datetime.datetime) -> Coordinate:
        sorted_points = sorted(self.points, key=lambda p: diff_in_seconds(timestamp, p.timestamp_utc))
        return sorted_points[0].coordinate


class VisitSegment(SemanticSegment):

    def __init__(self, data: dict):
        super().__init__(data)

        self.hierarchy_level: int
        """0 = top-level visit. Higher values are nested visits, such as a shop inside a mall."""
        self.stationary_probability: float
        """Confidence that you were stationary somewhere (0.91 = fairly sure)."""
        self.place_id: str
        """Google Places ID of the best-matching place."""
        self.place_probability: float
        """Confidence that this specific place is correct."""
        self.coordinate: Coordinate
        """Coordinate of the matching place"""

        visit = data.get('visit')
        self.hierarchy_level = visit.get('hierarchyLevel')
        self.stationary_probability = visit.get('probability')
        top_candidate = visit.get('topCandidate')
        self.place_id = top_candidate.get('placeId')
        self.place_probability = top_candidate.get('probability')
        self.coordinate = Coordinate(top_candidate.get('placeLocation').get('latLng'))

    def maps_url(self) -> str:
        return f"https://www.google.com/maps/search/?api=1&query=place&query_place_id={self.place_id}"

    def sort_key(self, timestamp: datetime.datetime) -> float:
        return super().sort_key(timestamp)

    def get_best_coordinate(self, timestamp: datetime.datetime) -> Coordinate:
        return self.coordinate


class ActivitySegment(SemanticSegment):

    def __init__(self, data: dict):
        super().__init__(data)

        self.start_coordinate: Coordinate
        self.end_coordinate: Coordinate
        self.distance_m: float
        """Distance covered in meters"""
        self.type: TransportationType = TransportationType.UNKNOWN
        """Google's guess at mode of transport"""
        self.probability: float
        """Confidence in the transportation type guess"""

        activity = data.get('activity')
        self.start_coordinate = Coordinate(activity.get('start').get('latLng'))
        self.end_coordinate = Coordinate(activity.get('end').get('latLng'))
        self.distance_m = float(activity.get('distanceMeters'))
        top_candidate = activity.get('topCandidate')
        self.type = TransportationType(top_candidate.get('type'))
        self.probability = float(top_candidate.get('probability'))

    def sort_key(self, timestamp: datetime.datetime) -> float:
        return super().sort_key(timestamp)

    def get_best_coordinate(self, timestamp: datetime.datetime) -> Coordinate:
        start_diff = diff_in_seconds(timestamp, self.start_time_utc)
        end_diff = diff_in_seconds(timestamp, self.end_time_utc)
        if start_diff < end_diff:
            return self.start_coordinate
        return self.end_coordinate

import datetime

from src.models.Coordinate import Coordinate
from src.models.Position import Position
from src.models.SemanticSegment import PathSegment, VisitSegment, ActivitySegment
from src.time_helpers import diff_in_seconds


class TimelineData:

    def __init__(self, timeline_data: dict):
        self._raw_data = timeline_data
        self.positions: list[Position] = []
        self.path_segments: list[PathSegment] = []
        self.visit_segments: list[VisitSegment] = []
        self.activity_segments: list[ActivitySegment] = []

        self.positions = [Position(s) for s in self._raw_data.get('rawSignals', []) if
                          'position' in s and
                          s.get('position').get('timestamp') and
                          s.get('position').get('LatLng')]

        self.path_segments = [PathSegment(s) for s in self._raw_data.get('semanticSegments', []) if 'timelinePath' in s]
        self.visit_segments = [VisitSegment(s) for s in self._raw_data.get('semanticSegments', []) if 'visit' in s]
        self.activity_segments = [ActivitySegment(s) for s in self._raw_data.get('semanticSegments', []) if
                                  'activity' in s]

        # TODO sort to enable binary search

    def total_count(self) -> int:
        return len(self.positions) + len(self.path_segments) + len(self.visit_segments) + len(self.activity_segments)

    def match(self, timestamp: datetime.datetime, max_time_delta: int) -> Coordinate | None:
        matches = []
        for position in self.positions:
            if diff_in_seconds(position.timestamp_utc, timestamp) < max_time_delta:
                matches.append(position)

        for visit_segment in self.visit_segments:
            if (diff_in_seconds(visit_segment.start_time_utc, timestamp) < max_time_delta or
                    diff_in_seconds(visit_segment.end_time_utc, timestamp) < max_time_delta):
                matches.append(visit_segment)

        for activity_segment in self.activity_segments:
            if diff_in_seconds(activity_segment.start_time_utc, timestamp) < max_time_delta:
                matches.append(activity_segment)
            if diff_in_seconds(activity_segment.end_time_utc, timestamp) < max_time_delta:
                matches.append(activity_segment)

        sorted_matches = sorted(matches, key=lambda x: x.sort_key(timestamp))
        if sorted_matches:
            return sorted_matches[0].get_best_coordinate(timestamp)
        return None

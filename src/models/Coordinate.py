from src.geo_helpers import parse_lat_long


class Coordinate:

    def __init__(self, coordinate_str: str):
        self._raw_coordinate_str = coordinate_str
        self.lat: float
        self.long: float

        self.lat, self.long = parse_lat_long(coordinate_str)

    @classmethod
    def empty(cls) -> 'Coordinate':
        coordinate = Coordinate('0,0')
        coordinate.lat = None
        coordinate.long = None
        return coordinate

    def is_empty(self) -> bool:
        return not bool(self.lat) and not bool(self.long)

    def __str__(self) -> str:
        return f'{self.lat},{self.long}'

    def __repr__(self) -> str:
        return self.__str__()

    def get_maps_url(self) -> str:
        return f'https://www.google.com/maps/search/?api=1&query={self.lat},{self.long}'

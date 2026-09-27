import datetime
import logging
from pathlib import Path

from exiftool import ExifToolHelper

from src.constants import GOOGLE_COORDINATE_SYSTEM
from src.models.Coordinate import Coordinate
from src.time_helpers import is_within_range, parse_to_utc_datetime

logger = logging.getLogger(__name__)

EXIF_DATETIME_ORIGINAL = 'EXIF:DateTimeOriginal'
EXIT_OFFSET_TIME_ORIGINAL = 'EXIF:OffsetTimeOriginal'
VIDEO_MEDIA_CREATED = 'QuickTime:CreateDate'
KEYS_CREATION_DATE = 'Keys:CreationDate'
XML_CREATION_DATE = 'XML:CreationDateValue'
GPS_TAGS_LATITUDE = ['EXIF:GPSLatitude', 'XMP:GPSLatitude']
GPS_TAGS_LONGITUDE = ['EXIF:GPSLongitude', 'XMP:GPSLongitude']
GPS_TAGS_ALTITUDE = ['EXIF:GPSAltitude']
EXIF_GPS_TAGS = ['EXIF:GPSLatitude', 'EXIF:GPSLatitudeRef', 'EXIF:GPSLongitude', 'EXIF:GPSLongitudeRef',
                 'EXIF:GPSAltitude', 'EXIF:GPSAltitudeRef']
XMP_GPS_TAGS = ['XMP:GPSLatitude', 'XMP:GPSLongitude', ]
GPS_TAGS = EXIF_GPS_TAGS + XMP_GPS_TAGS + ['QuickTime:GPSCoordinates', 'Composite:GPSLatitude', 'Composite:GPSPosition']
DATE_CREATED_TAGS = [EXIF_DATETIME_ORIGINAL, EXIT_OFFSET_TIME_ORIGINAL, VIDEO_MEDIA_CREATED, KEYS_CREATION_DATE,
                     XML_CREATION_DATE]
TAGS = DATE_CREATED_TAGS + GPS_TAGS

WRITE_TAGS_PARAMS = ["-overwrite_original"]


def _get_coordinate(tags: dict) -> Coordinate:
    coordinate = Coordinate.empty()
    for gps_tag in GPS_TAGS_LATITUDE:
        if latitude := tags.get(gps_tag, None):
            coordinate.lat = latitude
            break

    for gps_tag in GPS_TAGS_LONGITUDE:
        if longitude := tags.get(gps_tag, None):
            coordinate.long = longitude
            break

    return coordinate


def _get_datetime_original(tags: dict) -> datetime.datetime | None:
    if EXIF_DATETIME_ORIGINAL in tags:
        offset = tags.get(EXIT_OFFSET_TIME_ORIGINAL)
        return parse_to_utc_datetime(f'{tags.get(EXIF_DATETIME_ORIGINAL)}{offset if offset else ''}')
    if KEYS_CREATION_DATE in tags:  # Written by iPhone, includes timezone
        return parse_to_utc_datetime(f'{tags.get(KEYS_CREATION_DATE)}')
    if XML_CREATION_DATE in tags:  # Sometimes embedded by Sony cameras in video, can include timezone
        return parse_to_utc_datetime(f'{tags.get(XML_CREATION_DATE)}')
    elif VIDEO_MEDIA_CREATED in tags:
        return parse_to_utc_datetime(f'{tags.get(VIDEO_MEDIA_CREATED)}')
    return None


class MetadataAndTags:

    def __init__(self, eth: ExifToolHelper, photo_path: Path):
        self._eth = eth
        self._path_str = str(photo_path)
        metadata: dict = eth.get_metadata(self._path_str)[0]
        tags: dict = eth.get_tags(self._path_str, tags=TAGS)[0]
        self.date_modified_utc: datetime.datetime = parse_to_utc_datetime(metadata.get('File:FileModifyDate'))
        self.date_created_utc: datetime.datetime = parse_to_utc_datetime(metadata.get('File:FileCreateDate'))
        self.datetime_original_utc: datetime.datetime = _get_datetime_original(tags)
        self.camera_brand: str = metadata.get('EXIF:Make')
        self.camera_model: str = metadata.get('EXIF:Model')

        self.coordinate: Coordinate = _get_coordinate(tags)

    def has_coordinate(self) -> bool:
        return not self.coordinate.is_empty()

    def get_timestamp_utc(self, start_date: datetime.datetime = None,
                          end_date: datetime.datetime = None) -> datetime.datetime | None:
        if is_within_range(self.datetime_original_utc, start_date, end_date):
            return self.datetime_original_utc
        if is_within_range(self.date_created_utc, start_date, end_date):
            return self.date_created_utc
        return None

    def write_coordinate(self, coordinate: Coordinate) -> None:
        # Note: negative latitude denotes Southern Hemisphere and negative longitude denotes Western Hemisphere
        # EXIF metadata stores positive coordinates with the *Ref tag denoting which hemisphere they're located in.

        lat_ref = 'N' if coordinate.lat >= 0 else 'S'
        long_ref = 'E' if coordinate.long >= 0 else 'W'
        gps_tags = {'GPSLatitude*': abs(coordinate.lat), 'GPSLatitudeRef*': lat_ref,
                    'GPSLongitude': abs(coordinate.long), 'GPSLongitudeRef': long_ref,
                    'GPSMapDatum': GOOGLE_COORDINATE_SYSTEM}
        self._eth.set_tags(self._path_str, gps_tags, params=WRITE_TAGS_PARAMS)

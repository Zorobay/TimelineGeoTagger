import datetime
import logging
from datetime import timedelta

from src import constants
from src.constants import UTC_TIMEZONE
from src.exceptions.NonFatalException import NonFatalException

logger = logging.getLogger('')


def offset_to_timezone(offset: float) -> datetime.timezone:
    return datetime.timezone(timedelta(hours=offset))


def parse_to_utc_datetime(timestamp_str: str) -> datetime.datetime:
    iso_format = timestamp_str[:10].replace(':', '-') + timestamp_str[10:]
    
    try:
        timestamp = datetime.datetime.fromisoformat(iso_format)
    except ValueError as e:
        logger.error(f'File contains invalid date {iso_format} which could not be parsed: {e}')
        raise NonFatalException()

    if not timestamp.tzinfo:
        timestamp = timestamp.replace(tzinfo=constants.default_tz)
    return timestamp.astimezone(UTC_TIMEZONE)


def is_within_range(dt: datetime.datetime, start_date: datetime.datetime | None = None,
                    end_date: datetime.datetime | None = None) -> bool:
    after_start_date = dt >= start_date if start_date else True
    before_end_date = dt <= end_date if end_date else True
    return after_start_date and before_end_date


def diff_in_seconds(d1: datetime.datetime, d2: datetime.datetime) -> float:
    return abs((d1 - d2).total_seconds())

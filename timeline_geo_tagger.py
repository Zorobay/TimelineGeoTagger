import datetime
import json
import logging
from pathlib import Path

import click
import exiftool
from exiftool.exceptions import ExifToolExecuteError

from src import constants
from src.constants import UTC_TIMEZONE
from src.exceptions.NonFatalException import NonFatalException
from src.models.MetadataAndTags import MetadataAndTags
from src.models.Results import Results
from src.models.TimelineData import TimelineData
from src.time_helpers import offset_to_timezone

logger = logging.getLogger('')


def write_results(results: Results) -> None:
    logger.info('\n====== DONE! ======')
    logger.info(f'\tProcessed {results.total()} files.')
    logger.info(f'\tWrite OK: {results.write_ok}')
    logger.info(f'\tSkipped: {results.skipped}')
    logger.info(f'\tNo matching coordinate: {results.no_match}')
    logger.info(f'\tError: {results.error}')


def get_files(path: Path, suffixes: list[str]) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob('*') if p.suffix.lower() in suffixes)


@click.command()
@click.argument("timeline_path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("files_path", type=click.Path(exists=True, file_okay=True, path_type=Path))
@click.option('-o', '--overwrite', default=False, type=bool)
@click.option('-d', '--dry-run', default=False, type=bool)
@click.option('-s', '--start-date', default=None, type=click.DateTime(),
              help='If known, the earliest datetime the pictures could have been taken, in UTC time.')
@click.option('-e', '--end-date', default=None, type=click.DateTime(),
              help='If known, the latest datetime the pictures could have been taken, in UTC time.')
@click.option('-td', '--max-time-delta', default=4 * 60 * 60, type=int,
              help="The maximum allowed difference in seconds between the medias timestamp and a matching coordinate's timestamp")
@click.option('-tz', '--time-zone-offset-hint', default=None, type=float,
              help='When media is missing timezone, this will be used as the assumed timezone offset.')
@click.option('--suffixes', default=['.jpg', '.jpeg', '.heic', '.arw', '.mp4', '.mov'], type=list[str],
              help='Suffixes (filetypes) to read and write to.')
def run(timeline_path: Path, files_path: Path, overwrite: bool, dry_run: bool, start_date: datetime.datetime,
        end_date: datetime.datetime, max_time_delta: int, time_zone_offset_hint: float, suffixes: list[str]):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', encoding='utf-8', level=logging.DEBUG)
    constants.default_tz = offset_to_timezone(time_zone_offset_hint) if time_zone_offset_hint else None

    start_date = start_date.replace(tzinfo=UTC_TIMEZONE) if start_date else start_date
    end_date = end_date.replace(tzinfo=UTC_TIMEZONE) if end_date else end_date

    with open(timeline_path, 'r', encoding='utf-8') as timeline:
        json_data = json.load(timeline)
        timeline = TimelineData(json_data)
        logger.info(f'Done parsing {timeline.total_count()} elements from {timeline_path}')

    results = Results()
    files = get_files(files_path, suffixes)
    num_files = len(files)
    for i, file in enumerate(files):
        with exiftool.ExifToolHelper() as eth:
            try:
                metadata_tags = MetadataAndTags(eth, file)
            except NonFatalException:
                results.incr_error()
                continue
                
            media_timestamp = metadata_tags.get_timestamp_utc(start_date, end_date)
            if not media_timestamp:
                logger.warning(f'[{i + 1} of {num_files}] Could not extract an appropriate date for {file}')
                continue

            if not overwrite and metadata_tags.has_coordinate():
                logger.info(f'[{i + 1} of {num_files}] Skipping {file} which already has geospatial data.')
                results.incr_skipped()
                continue

            matching_coordinate = timeline.match(media_timestamp, max_time_delta)
            if not matching_coordinate:
                logger.warning(
                    f'[{i + 1} of {num_files}] Could not find matching coordinate for timestamp {media_timestamp} for file {file}')
                results.incr_no_match()
                continue

            if dry_run:
                logger.info(
                    f'[{i + 1} of {num_files}] [Dry Run] Would write coordinate ({matching_coordinate}) metadata to {file}')
                continue

            try:
                metadata_tags.write_coordinate(matching_coordinate)
                results.incr_write_ok()
                logger.info(f'[{i + 1} of {num_files}] Wrote coordinate ({matching_coordinate}) metadata to {file}')
            except ExifToolExecuteError as e:
                logger.error(f'[{i + 1} of {num_files}] Failed to write metadata to {file}. {e.stderr}')
                results.incr_error()

    write_results(results)


if __name__ == '__main__':
    run()

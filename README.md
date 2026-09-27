# Timeline Geo Tagger

A script to automatically geotag images from your exported **Google Timeline** data.

## Usage

```powershell
poetry run python main.py TIMELINE_PATH FILES_PATH [OPTIONS]
```

| Argument        | Description                                                                         |
|-----------------|-------------------------------------------------------------------------------------|
| `TIMELINE_PATH` | Path to `Timeline.json`                                                             |
| `FILES_PATH`    | Folder containing the media or the path to a single media. Subfolders are included. |

### Options

| Option                                 | Default                           | Description                                                                                                                    |
|----------------------------------------|-----------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| `-o`, `--overwrite BOOL`               | `false`                           | Also write to files that already have coordinates.                                                                             |
| `-d`, `--dry-run BOOL`                 | `false`                           | Only report what would be written. No files are changed.                                                                       |
| `-s`, `--start-date DATETIME`          | none                              | Earliest time the media can have been taken, in **UTC**.                                                                       |
| `-e`, `--end-date DATETIME`            | none                              | Latest time the media can have been taken, in **UTC**.                                                                         |
| `-td`, `--max-time-delta SECONDS`      | `14400` (4 h)                     | Largest allowed gap between a file's timestamp and the matched Timeline position.                                              |
| `-tz`, `--time-zone-offset-hint HOURS` | none                              | UTC offset to assume for files that have no time zone in their metadata, e.g. `9` for Japan or `-4` for New York (summertime). |
| `--suffixes`                           | `.jpg .jpeg .heic .arw .mp4 .mov` | File types to process.                                                                                                         |

`--overwrite` and `--dry-run` take a value, for example `-d true`.

Dates accept the formats `YYYY-MM-DD`, `YYYY-MM-DDTHH:MM:SS` and `YYYY-MM-DD HH:MM:SS`.

## Examples

Test run on a trip folder. Nothing is written:

```powershell
poetry run python main.py "C:\Users\<user>\Downloads\Timeline.json" "\\nas\photo\Japan 2024" -d true
```

Tag a trip where the camera has no time zone set, only accepting dates within the trip:

```powershell
poetry run python main.py Timeline.json "\\nas\photo\Japan 2024" -tz 9 -s 2024-09-10 -e 2024-10-05
```

Re-tag everything, replacing existing coordinates, with at most 30 minutes between photo and position:

```powershell
poetry run python main.py Timeline.json "\\nas\photo\Japan 2024" -o true -td 1800
```

## Requirements
* Python 3.11 or newer
* [ExifTool](https://exiftool.org) on your `PATH`
* [Poetry](https://python-poetry.org/) package manager

```powershell
choco install exiftool
poetry install
```

## Exporting your Timeline

The Timeline is stored on your phone, so the export is made there.

- **Android:** Settings → Location → Location services → Timeline → **Export Timeline data**
- **iPhone:** Google Maps → profile picture → Your Timeline → ⋯ → Location & privacy settings → **Export Timeline data**
  Copy the resulting `Timeline.json` to your computer.
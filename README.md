EXIF data fixer for Google Photos takeouts.

## What is photo-fixer

Photo-fixer is a simple tool that embeds EXIF metadata from `supplemental-metadata.json` JSON files from a Google Photos takeout in the original photo/video.

## What photo-fixer does

- 📂 Recursively finds images and videos and matches them with their corresponding JSON metadata files from a Google Takeout folder
- 📅 Extracts the photo taken date (`DateTimeOriginal`), GPS position and camera make and model from the JSON metadata
- 🏷️ Embeds the metadata into the original image and video files

---

## Requirements

- **Pyton 3** - https://www.python.org/downloads/

Then install the Python packages:
- **pyexiv2** - install with `pip install pyexiv2`
- **pyexiftool** - install with `pip install pyexiftool`

## Quick start

1. Download `main.py` to your computer
2. Run the file with
```bash
py main.py "/path/to/export/root/folder"
```
where the first program argument is the path to a Google Takeout folder (or any folder containing images/videos and JSON files).

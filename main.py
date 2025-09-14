#!/usr/bin/env python3

# pip install -U pyexiftool

# ExifTool:
## Windows: winget install OliverBetz.ExifTool
## MacOS: brew install exiftool
## Linux:
### Ubuntu/Debian: sudo apt install exiftool
### CentOS/RHEL/Fedora: sudo yum install perl-Image-ExifTool or sudo dnf install perl-Image-ExifTool

# Run with py main.py "./path/to/export/folder"

import sys
import os
import json
import datetime
from os import walk
from exiftool import ExifTool

DTO_KEY = 'Exif.Photo.DateTimeOriginal'

class FileItem:
  def __init__(self, name, path, is_video):
    self.name = name
    self.path = path
    self.is_video = is_video


def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

def deg_to_dms(deg):
  d = int(deg)
  m = int((deg - d) * 60)
  s = int((((deg - d) * 60 - m) * 60) * 100) / 100
  return str(d) + " " + str(m) + " " + str(s)

def get_exif_exiftool(taken_time, latitude, longitude, altitude, camera_make, camera_model):
  # https://sylikc.github.io/pyexiftool/examples.html
  # https://exiftool.org/TagNames/GPS.html
  # https://exiftool.org/TagNames/XMP.html
  arr = []
  has_loc = latitude != 0.0 and longitude != 0.0
  if (taken_time is not None):
    arr.append('-DateTimeOriginal=' + utc_to_local(datetime.datetime.fromtimestamp(int(taken_time), datetime.UTC)).strftime("%Y:%m:%d %H:%M:%S"))
  if (latitude is not None and has_loc):
    arr.append('-GPSLatitude=' + str(latitude))
    arr.append('-GPSLatitudeRef=' + ('N' if latitude >= 0  else 'S'))
  if (longitude is not None and has_loc):
    arr.append('-GPSLongitude=' + str(longitude))
    arr.append('-GPSLongitudeRef=' + ('E' if longitude >= 0  else 'W'))
  if (altitude is not None and has_loc):
    arr.append('-GPSAltitude=' + str(altitude))
  if (camera_make is not None):
    arr.append('-Make=' + camera_make)
  if (camera_model is not None):
    arr.append('-Model=' + camera_model)
  return arr

def write_metadata(file, json_file, et):
  f = open(json_file.path, encoding='utf-8')
  data = json.load(f)
  f.close()
  
  #creation_time = data.get('creationTime', {}).get('timestamp')
  taken_time = data.get('photoTakenTime', {}).get('timestamp')
  latitude = data.get('geoData', {}).get('latitude')
  longitude = data.get('geoData', {}).get('longitude')
  altitude = data.get('geoData', {}).get('altitude')
  camera_make = data.get('cameraMake')
  camera_model = data.get('cameraModel')
  
  try:
    tags = get_exif_exiftool(taken_time, latitude, longitude, altitude, camera_make, camera_model)
    et.execute("-P", "-overwrite_original", *tags, file.path)
    print(et.last_stdout, et.last_stderr)
  except Exception as e:
    print(file.path)
    print("Error:", e)
    return

if len(sys.argv) < 2:
    print("Error: You must specify a folder path")
    exit(1)

extensions_image = {
  ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".tiff", ".gif", ".avif", ".jxl", ".jfif",
  ".raw", "cr2", ".nef", ".orf", "sr2", ".arw", ".dng", ".pef", ".raf", "rw2", ".srw", "3fr", ".erf",
  "k25", ".kdc", ".mef", ".mos", ".mrw", ".nrw", ".srf", "x3f", ".svg", ".ico", ".psd", ".ai", ".eps",
}
extensions_video = {
  "mp4", ".mov", ".mkv", ".avi", ".webm", "3gp", "m4v", ".mpg", ".mpeg", ".mts", "m2ts", ".ts", ".flv",
  "f4v", ".wmv", ".asf", ".rm", ".rmvb", ".vob", ".ogv", ".mxf", ".dv", ".divx", ".xvid"
}

with ExifTool() as et:
  path = sys.argv[1]
  for (dirpath, dirnames, filenames) in walk(path, topdown=True):
    print("Find files in:", dirpath)
    files = []
    json_files = []
    for file in filenames:
      filename, file_extension = os.path.splitext(file)
      if (file_extension == ".json"):
        json_files.append(FileItem(file, os.path.join(dirpath, file), False))
      elif (file_extension.lower() in extensions_image):
        files.append(FileItem(file, os.path.join(dirpath, file), False))
      elif (file_extension.lower() in extensions_video):
        files.append(FileItem(file, os.path.join(dirpath, file), True))

    print("Files:", len(files), "JSON:", len(json_files))

    file_count = len(files)
    if (file_count == 0):
      continue
    for i, file in enumerate(files):
      for json_file in json_files:
        if (json_file.name.startswith(file.name) and json_file.name.split(file.name, 2)[1].count(".") == 2):
          #print("\033[K", end="\r")
          print(i + 1,"/", file_count, file.name)
          write_metadata(file, json_file, et)
    print()

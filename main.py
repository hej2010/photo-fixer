#!/usr/bin/env python3

# pip install -U pyexiv2
# pip install -U pyexiftool

# ExifTool:
## Windows: winget install OliverBetz.ExifTool
## MacOS: brew install exiftool
## Linux:
### Ubuntu/Debian: sudo apt install exiftool
### CentOS/RHEL/Fedora: sudo yum install perl-Image-ExifTool or sudo dnf install perl-Image-ExifTool

# Run with py main.py "/path/to/export/root/folder"

import sys
import os
import json
import time
import signal
import datetime
import threading
import concurrent.futures
from os import walk
from pyexiv2 import Image as ImgMeta
from exiftool import ExifToolHelper

class FileItem:
  def __init__(self, name, path, is_video):
    self.name = name
    self.path = path
    self.is_video = is_video

def deg_to_dms(deg):
  d = int(deg)
  m = int((deg - d) * 60)
  s = int(((deg - d) * 60 - m) * 60)
  return ((d, 1), (m, 1), (s, 1))

def get_exif_exiv2(taken_time, latitude, longitude, altitude, camera_make, camera_model):
  new_exif = {} # https://exiv2.org/tags.html
  if (taken_time is not None):
    new_exif['Exif.Image.DateTimeOriginal'] = datetime.datetime.fromtimestamp(int(taken_time), datetime.UTC).strftime("%Y:%m:%d %H:%M:%S")
  if (latitude is not None):
    new_exif['Exif.GPSInfo.GPSLatitude'] = deg_to_dms(latitude)
  if (longitude is not None):
    new_exif['Exif.GPSInfo.GPSLongitude'] = deg_to_dms(longitude)
  if (altitude is not None):
    new_exif['Exif.GPSInfo.GPSAltitude'] = altitude
  if (camera_make is not None):
    new_exif['Exif.Image.Make'] = camera_make
  if (camera_model is not None):
    new_exif['Exif.Image.Model'] = camera_model
  return new_exif

def get_exif_exiftool(taken_time, latitude, longitude, altitude, camera_make, camera_model):
  new_exif = {}
  if (taken_time is not None):
    new_exif['DateTimeOriginal'] = datetime.datetime.fromtimestamp(int(taken_time), datetime.UTC).strftime("%Y:%m:%d %H:%M:%S")
  if (latitude is not None):
    new_exif['GPSLatitude'] = deg_to_dms(latitude)
  if (longitude is not None):
    new_exif['GPSLongitude'] = deg_to_dms(longitude)
  if (altitude is not None):
    new_exif['GPSAltitude'] = altitude
  if (camera_make is not None):
    new_exif['Make'] = camera_make
  if (camera_model is not None):
    new_exif['Model'] = camera_model
  return new_exif

exit_event = threading.Event()

def signal_handler(signum, frame):
  exit_event.set()
  print("Exiting...", flush=True)

signal.signal(signal.SIGINT, signal_handler)

counter = 0
lock = threading.Lock()

def write_metadata(file, json_file, file_count):
  global counter
  if exit_event.is_set():
    return
  try:
    f = open(json_file.path)
    data = json.load(f)
    f.close()
    
    if exit_event.is_set():
      return
    #creation_time = data.get('creationTime', {}).get('timestamp')
    taken_time = data.get('photoTakenTime', {}).get('timestamp')
    latitude = data.get('geoData', {}).get('latitude')
    longitude = data.get('geoData', {}).get('longitude')
    altitude = data.get('geoData', {}).get('altitude')
    camera_make = data.get('cameraMake')
    camera_model = data.get('cameraModel')

    if (file.is_video == True):
      try:
        with ExifToolHelper() as et:
          et.set_tags(
            file.path,
            tags=get_exif_exiftool(taken_time, latitude, longitude, altitude, camera_make, camera_model),
            params=["-P", "-overwrite_original"] # preserve modification date and overwrite original
        )
      except Exception as e:
        print(file.path)
        print("Error:", e)
        print()
    else:
      try: # try exiv2 first
        with ImgMeta(file.path) as img_meta:
          img_meta.modify_exif(get_exif_exiv2(taken_time, latitude, longitude, altitude, camera_make, camera_model))
      except Exception as e:
        if exit_event.is_set():
          return
        try: # if it fails, try ExifTool
          with ExifToolHelper() as et:
              et.set_tags(
                file.path,
                tags=get_exif_exiftool(taken_time, latitude, longitude, altitude, camera_make, camera_model),
                params=["-P", "-overwrite_original"]
              )
        except Exception as e2:
          print(file.path)
          print("Error:", e)
          print()
  except Exception as ex:
    print(file.path)
    print("Error:", e)
  if exit_event.is_set():
    return
  with lock:
    counter += 1
    print(counter,"/", file_count, file.name,"                          ", end='\r')

if __name__ == "__main__":
  start = time.time()
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
  
  path = sys.argv[1]
  for (dirpath, dirnames, filenames) in walk(path, topdown=True):
    if exit_event.is_set():
      break
    print("Find files in:", dirpath)
    files = []
    json_files = []
    futures = []
    counter = 0
    for file in filenames:
      filename, file_extension = os.path.splitext(file)
      if (file_extension == ".json"):
        json_files.append(FileItem(file, os.path.join(dirpath, file), False))
      elif (file_extension.lower() in extensions_image):
        files.append(FileItem(file, os.path.join(dirpath, file), False))
      elif (file_extension.lower() in extensions_video):
        files.append(FileItem(file, os.path.join(dirpath, file), True))
    
    print("Files:", len(files), ", JSON:", len(json_files))
    file_count = len(files)
    
    if (file_count == 0):
      continue

    pool = concurrent.futures.ThreadPoolExecutor(max_workers=8)
    for i, file in enumerate(files):
      for json_file in json_files:
        if (json_file.name.startswith(file.name) and json_file.name.split(file.name, 2)[1].count(".") == 2):
          futures.append(pool.submit(write_metadata, file, json_file, file_count))
          break
    for future in concurrent.futures.as_completed(futures):
      if exit_event.is_set():
        for f in futures:
          if not f.done():
            f.cancel()
        pool.shutdown(wait=True)
    print()
  print("--- %s seconds ---" % (time.time() - start))

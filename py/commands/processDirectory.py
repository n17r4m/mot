"""

Aim is to have a single command detect + track an experiment



"""


import config
from lib.Database import Database

import commands.detectTrack as detect

# import commands.track as track
# import commands.draw as draw
# import commands.export as export

import time
import os
import gc
import shutil
from uuid import UUID
from dateutil.parser import parse as dateparse


async def main(args):
    """
    Args:
    - a directory to be recursively searched for videos to process
    
    """
    if len(args) < 1:
        print("""path/to/videos/""")
    else:
        print(await processDirectory(*args))


async def vacuum(db):
    print("Vacuuming...")
    vacuum_start = time.time()
    tables = ["track", "particle", "frame", "segment"]
    for t in tables:
        # print(" `->", t)
        await db.vacuum(t)
    # print(" '-> took", time.time() - vacuum_start, "s")


async def processDirectory(video_directory, date, export_directory):
    # Outer loop: search directory
    if not os.path.isdir(video_directory):
        print("Invalid video_directory")
        return
    if not os.path.isdir(export_directory):
        os.mkdir(export_directory)

    ext = ".avi"

    db = Database()

    # https://stackoverflow.com/questions/29206384/python-folder-names-in-the-directory
    videos = []
    for root, dirs, files in os.walk(video_directory, topdown=False, followlinks=True):
        for name in files:
            if name.endswith(ext):
                videos.append((root, name))

    # Inner loop: detect, track, draw, export
    process_start = time.time()

    seen_dirs = []

    for root, name in videos:

        video_start = time.time()
        parent_dir = video_directory.split("/")[-2]
        folders = root.split("/")
        index = folders.index(parent_dir)

        video_export_directory = "/".join([export_directory] + folders[index:])

        if video_export_directory in seen_dirs:
            pass
            # continue
        seen_dirs.append(video_export_directory)

        if not os.path.isdir(video_export_directory):
            os.makedirs(video_export_directory)

        video_file = os.path.join(root, name)
        trailing_numbers = 7  # MSBOT-01155{0000022}

        exp_name = folders[index + 1] + " " + name[: -len(ext)][:-trailing_numbers]
        exp_notes = ""

        await vacuum(db)

        print("Processing " + video_file + ", Notes: " + exp_notes)

        # print(" `-> Detecting...")
        # detect_start = time.time()
        experiment_uuid = await detect.detect_video(video_file, date, name, exp_notes)
        # print("  `-> took", time.time() - detect_start, "s")

        # await vacuum(db)
        """
        print(" `-> Tracking...")
        track_start = time.time()
        tracking_uuid = await track.track_experiment(detection_uuid)
        print("  `-> took", time.time() - track_start, "s")

        # print("Drawing...")
        # await draw.draw_tracks([tracking_uuid])
        """
        # print(" `-> Exporting...")
        # export_start = time.time()
        # await export.exportSyncrude2018(tracking_uuid, video_export_directory)
        # print("  `-> took", time.time() - export_start, "s")

        print("Processing video took " + str(time.time() - video_start) + " seconds.")

        # manually trigger garbage collection
        print("Collecting Garbage...")

        gc.collect()

    print("Processing all took " + str(time.time() - process_start) + " seconds")


import config
import os

import multiprocessing
import fcntl
import threading
import queue
import subprocess
import shlex
import asyncio


from skimage import io
from skimage.draw import line_aa as line
import numpy as np

from PIL import Image, ImageDraw

from lib.Database import Database
from mpyx.Video import Video
from uuid import UUID

async def main(args):
    
    if len(args) == 0: print("What you want to draw? [tracks|detections]")
        
    else:
        if   args[0] == "tracks":     await draw_tracks(args[1:])
        elif args[0] == "detections": await draw_detections(args[1:])
        else:                         print("Invalid draw sub-command")


async def draw_tracks(args):
    
    experiment_uuid = args[0]
    experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
    db = Database()
    
    print("Starting compressor.")
    frame_bytes = multiprocessing.Queue(5)
    #NOTE: Not enough memory if this is launched after we load the video.
    compressor = VideoStreamCompressor(frame_bytes, experiment_dir, "tracking.mp4", width=2336, height=1728, fps=300, pix_format="rgb24" )
    compressor.start()
    
    
    print("Opening extraction video")
    
    video = Video(os.path.join(experiment_dir, "extraction.mp4"), gray=False)
    raw = video.reader
    
    print("Drawing Tracks onto video.")
    # note: frame["number"] may not match frame number from loaded video if only a subset was detected.
    curr_frame = None
    prev_frame = None
    count = 0
    frame_count = 0
    curr_segment = None
    prev_segment = None


    q = """
        SELECT segment, number
        FROM segment
        WHERE experiment = '{experiment}'
        ORDER BY number ASC
        """
    s = q.format(experiment=experiment_uuid)
    async for segment in db.query(s):
    
        q = """
            SELECT f3.number as fn,
                   t1.location as l1, 
                   t2.location as l2
            FROM frame f1, frame f2, frame f3, track t1, track t2
            WHERE f1.segment = '{segment}'
            AND f2.segment = '{segment}'
            AND f3.segment = '{segment}'
            AND f1.number = f2.number - 1
            AND t1.frame = f1.frame
            AND t2.frame = f2.frame
            AND t1.particle = t2.particle
            ORDER BY fn ASC;
            """
        s = q.format(segment=segment["segment"])
        async for track in db.query(s):
            curr_frame = track['fn']
            count += 1
            
            if curr_frame != prev_frame:
                if not prev_frame is None:
                    frame_bytes.put(im.tobytes())
                    frame_count += 1
                    if prev_frame % 10 == 0:
                        print("frame {frame}, drew {count} tracks"
                              .format(frame = prev_frame, count = count))
                    # print("{frame}".format(frame=prev_frame), end=' ')
                    count = 0
                
                # Add in missing frames
                while frame_count < curr_frame:
                    raw_image = video.frame(frame_count)
                    im = Image.fromarray(raw_image)
                    frame_bytes.put(im.tobytes())
                    print("frame {frame} added".format(frame=frame_count))
                    frame_count += 1
                
                prev_frame = curr_frame
                raw_image = video.frame(prev_frame)
                im = Image.fromarray(raw_image)
                draw = ImageDraw.Draw(im) 
    
            p1 = (int(round(track["l1"].x)), int(round(track["l1"].y)))
            p2 = (int(round(track["l2"].x)), int(round(track["l2"].y)))
            draw.line([p1, p2], (0,255,0), 3)
            
    print("Generation complete.")
    frame_bytes.put(None)
    compressor.join()
    print("Done.")

def draw_detections(args):
    print("Not implemented")


class VideoStreamCompressor(multiprocessing.Process):
    def __init__(self, queue, experiment_dir, fname, width=2336, height=1729, fps=300., rate=24., pix_format="gray"):
        super(VideoStreamCompressor, self).__init__()
        self.queue = queue
        self.edir = experiment_dir
        self.fname = fname
        self.stop_event = multiprocessing.Event()
        self.cmd = ''.join(('ffmpeg',
          ' -f rawvideo -pix_fmt {}'.format(pix_format),
          ' -video_size {}x{}'.format(width,height),
          ' -framerate {}'.format(fps),
          ' -i -',
          ' -c:v libx264 -crf 15 -preset fast',
          ' -pix_fmt yuv420p',
          ' -filter:v "setpts={}*PTS'.format(fps/rate),
          ', crop={}:{}:0:0"'.format(width, height-1) if height % 2 else '"',
          ' -r 24',
          ' -movflags +faststart',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        fcntl.fcntl(proc.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        with open("{}.log".format(os.path.join(self.edir, self.fname)), 'wb', 0) as log_file:
            while True:
                try:
                    log_file.write(proc.stdout.read())
                except:
                    pass
                
                if self.stopped():
                    return self.close(proc)
                else:
                    frame_bytes = self.queue.get()
                    if frame_bytes is None:
                        return self.close(proc)
                    else:
                        try:
                            proc.stdin.write(frame_bytes)
                        except BrokenPipeError:
                            print('uh oh, file probably exists, can\'t overwrite')

                        
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()

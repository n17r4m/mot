
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
from lib.Video import Video
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
    compressor = VideoStreamCompressor(frame_bytes, experiment_dir, "tracking.mp4", width=2336-400, height=1728, fps=300, pix_format="rgb24" )
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
        SELECT f3.number as fn, f3.frame, l1, l2, f3.segment as seg
        FROM frame f3
        JOIN LATERAL(
            SELECT f2.number, l1, l2
            FROM frame f2
            JOIN LATERAL (
                SELECT t1.location as l1, t2.location as l2
                FROM track t1, track t2, frame f1
                WHERE t1.particle = t2.particle
                AND t1.frame = f1.frame
                AND t2.frame = f2.frame
                AND f1.number = f2.number - 1
                AND f1.segment = f2.segment
            ) A ON TRUE
            WHERE f2.segment = f3.segment
        ) B ON TRUE
        WHERE experiment = $1
        ORDER BY fn ASC 
        """
    async for track in db.query(q, UUID(experiment_uuid)):
        curr_segment = track['seg']
        curr_frame = track['fn']
        count += 1
        
        if curr_frame != prev_frame:
            if not prev_frame is None:
                frame_bytes.put(im.tobytes())
                frame_count += 1
                print("frame {frame}, drew {count} tracks"
                      .format(frame = prev_frame, count = count))
                # print("{frame}".format(frame=prev_frame), end=' ')
                count = 0
            
            # Add in missing frames
            while frame_count < curr_frame:
                raw_image = video.frame(frame_count)
                im = Image.fromarray(raw_image)
                frame_bytes.put(im.tobytes())
                print("a{frame}".format(frame=frame_count), end=' ')
                frame_count += 1
            
            prev_frame = curr_frame
            raw_image = video.frame(prev_frame)
            im = Image.fromarray(raw_image)
            draw = ImageDraw.Draw(im) 
    
        if curr_segment != prev_segment:
            if not prev_segment is None:
                pass
                # frame_bytes.put(np.zeros_like(raw[prev_frame]).tobytes())
            prev_segment = curr_segment


        p1 = (int(round(track["l1"].x)), int(round(track["l1"].y)))
        p2 = (int(round(track["l2"].x)), int(round(track["l2"].y)))
        draw.line([p1, p2], (0,255,0), 3)
        # rr, cc, val = line(
        #     int(round(track["l1"].y)), int(round(track["l1"].x)), 
        #     int(round(track["l2"].y)), int(round(track["l2"].x)))
        
        # raw[curr_frame, rr, cc, 0] = val*255
        # raw[curr_frame, rr+1, cc, 0] = val*255
        # raw[curr_frame, rr, cc+1, 0] = val*255
        # raw[curr_frame, rr-1, cc, 0] = val*255
        # raw[curr_frame, rr, cc-1, 0] = val*255
        

    # while frame_bytes.qsize() > 4:
    #     await asyncio.sleep(1)
    
    print("Generation complete.")
    
    '''
    print("Waiting for compression to finish.")
    counter=0
    for frame in raw:
        frame_bytes.put(frame.astype('uint8').tobytes())
        print(counter)
        counter+=1
        print('q',frame_bytes.qsize())
        while frame_bytes.qsize() > 8:
            await asyncio.sleep(1)
    frame_bytes.put(None)
    '''
    print("Done.")
    frame_bytes.put(None)
    compressor.join()
        

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

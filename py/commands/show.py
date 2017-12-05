import config
from skimage import io
from lib.Database import Database
from base64 import b64decode
from PIL import Image
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
import io
import os
import multiprocessing
import subprocess
import shlex
import fcntl
from mpyx.Video import Video

async def main(args):
    
    if len(args) == 0: print("What you want to show? [frame]")
        
    else:
        if   args[0] == "frame":      await show_frame(args[1:])
        elif args[0] == "segment":    await show_segment(args[1:])
        else:                         print("Invalid show sub-command")


async def show_frame(args):
    '''
    args: experiment_uuid frame_number file
    '''
    
    if len(args) < 3: print("Please supply \"experiment frame_number file\"")
    else:
        db = Database()
        experiment_uuid = args[0]
        frame_number = int(args[1])
        file = args[2]
        
        experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
        
        async for record in db.query("""
            SELECT frame
            FROM frame
            WHERE experiment = $1 AND Frame.number = $2""", experiment_uuid, frame_number):
            
            print("Found frame", record['frame'])
            
            im = Image.open(os.path.join(experiment_dir, str(record['frame']), file))
            # im.save('show_frame_test.png')
            im = np.array(im)
            
            plt.gray()
            plt.imshow(im.squeeze())
            plt.show()
            
async def show_segment(args):
    '''
    args: experiment_uuid segment_number
    '''
    
    if len(args) < 2: print("Please supply \"experiment segment_number\"")
    else:
        db = Database()
        experiment_uuid = args[0]
        segment_number = int(args[1])
        experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
        
        print("Starting compressor.")
        frame_bytes = multiprocessing.Queue(10)
        compressor = VideoStreamCompressor(frame_bytes, 
                                           experiment_dir, 
                                           "segmentTmp.mp4", 
                                           width=2336, 
                                           height=1728, 
                                           fps=24, 
                                           pix_format="rgb24" )
        compressor.start()
       
        video = Video(os.path.join(experiment_dir, "extraction.mp4"))
        
        async for record in db.query("""
            SELECT frame, frame.number as num
            FROM frame, segment
            WHERE segment.experiment = $1 
            AND segment.segment = frame.segment
            AND segment.number = $2
            ORDER BY frame.number
            """, experiment_uuid, segment_number):
            

            frame_bytes.put(video.frame(record['num']).tobytes())
            print('frame', record["num"])
        
        print("Done.")
        frame_bytes.put(None)
        compressor.join()
        
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
        
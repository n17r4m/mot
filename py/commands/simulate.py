from uuid import UUID, uuid4
import config
import os

async def main(args):
    if len(args) == 0: print("What you want to simulate? [experiment|video]")
        
    else:
        if   args[0] == "experiment":  print(await simulation(*args[1:]))
        elif args[0] == "video":       print(await create_video(*args[1:]))
        else:                          print("Invalid simulate sub-command")

    


async def simulation(model = "linear", profile = "simple", frames = 150, width = 2336, height = 1729, segment_size = 10):
    from lib.Simulation import Simulation
    return await Simulation(model, profile, frames, width, height, segment_size).go()
    



async def create_video(experiment_uuid, bg_file = "bg.png", out_file = "visualization.mp4"):
    from skimage.io import imread
    from lib.Visualize import FrameIter, VisFrame
    from lib.Compress import VideoStream
    
    experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
    
    if not os.path.isdir(experiment_dir):
        os.mkdir(experiment_dir)
    # if we just made the directory, the background will not be in the experiment directory... kg
    bg = imread(os.path.join(experiment_dir, bg_file), as_grey=True).astype("float64").squeeze() / 255. / 255.
    height, width = bg.shape
    
    fname = os.path.join(experiment_dir, out_file)
    
    envs = [{"CUDA_VISIBLE_DEVICES": str(g)} for g in range(config.GPUs)]
    
    
    (   FrameIter(UUID(experiment_uuid))
        .sequence()
        .split([VisFrame(bg, env=e) for e in envs])
        .order()
        .into(VideoStream(experiment_dir, fname, width=width, height=height))
        
    ).execute()
    
    
    






    
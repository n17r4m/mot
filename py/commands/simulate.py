from uuid import UUID, uuid4
import config
import os

async def main(args):
    if len(args) == 0: print("What you want to simulate? [experiment|video]")
        
    else:
        if   args[0] == "experiment":  print(await simulation(*args[1:]))
        elif args[0] == "video":       print(await create_video(*args[1:]))
        elif args[0] == "corruption":  print(await corruption(*args[1:]))
        elif args[0] == "linescanExp": print(await linescan(*args[1:]))
        elif args[0] == "linescanImg": print(await create_linescan(*args[1:]))
        else:                          print("Invalid simulate sub-command")


async def corruption(model = "go_faster", profile = "monotonic", method="simulation3Corrupt", frames = 500, width = 2336, height = 1729, segment_size = 10):
    from lib.Corruption import Corruption
    from lib.Simulation import Simulation
    experiment = await Simulation(model, profile, frames, width, height, segment_size, method).go()
    return await Corruption(experiment, "linear", "simple", frames, width, height, segment_size).go()


async def simulation(model = "go_faster", profile = "monotonic", frames = 500, width = 2336, height = 1729, segment_size = 10):
    from lib.Simulation import Simulation
    return await Simulation(model, profile, frames, width, height, segment_size).go()
    
async def linescan(model = "linear", profile = "simple", frames = 1, width = 4000, time = 10):
    from lib.LineScanSim import Simulation
    return await Simulation(model, profile, frames, width, time).go()


async def create_video(experiment_uuid, bg_file = "bg.png", out_file = "extraction.mp4"):
    from skimage.io import imread
    from lib.Visualize import FrameIter, VisFrame
    from mpyx.Compress import VideoStream
    from mpyx.F import EZ, SequenceStart, SequenceEnd
    import numpy as np
    
    experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
    
    if not os.path.isdir(experiment_dir):
        os.mkdir(experiment_dir)
        
    try:
        bg = imread(os.path.join(experiment_dir, bg_file), as_grey=True).astype("float64").squeeze() / 255.
        print('bg loaded:', np.min(bg), np.max(bg))
    except:
        # if we just made the directory, the background will not be in the experiment directory... kg
        try:
            bg = imread(os.path.join(config.experiment_dir, "bg.png"), as_grey=True).astype("float64").squeeze() 
            print('bg loaded2:', np.min(bg), np.max(bg))
        except Exception as e:
            raise Exception("Cannot read /experiments/{}/bg.png or /experiments/bg.png".format(experiment_uuid))
            
    height, width = bg.shape
    fname = os.path.join(experiment_dir, out_file)
    envs = [{"CUDA_VISIBLE_DEVICES": str(g)} for g in range(config.GPUs)]
    
    # (   FrameIter(UUID(experiment_uuid)).sequence("frame")
    #     .into([VisFrame(bg, env=e) for e in envs]).order("frame")
    #     .into(VideoStream(experiment_dir, fname, width=width, height=height))
    #     .execute())
    
    
    EZ( 
        FrameIter(UUID(experiment_uuid)),
        VisFrame(bg, env=envs[0]),
        VideoStream(experiment_dir, fname, width=width, height=height)
    ).start()
    
    
    
        # VideoStream(experiment_dir, fname, width=width, height=height)
    
    
    
async def create_linescan(experiment_uuid, bg_file = "bg.png", out_file = "linescan.png"):
    from lib.models.Classifier import Classifier
    from lib.Database import Database
    
    from skimage.io import imsave, imread
    from skimage.transform import resize
    from skimage.filters import threshold_otsu as threshold
    from skimage.filters import gaussian as blur
    
    import numpy as np
    
    os.environ["CUDA_VISIBLE_DEVICES"]="3"
    
    # Lines / second
    SCAN_RATE = 400
    
    experiment_dir = os.path.join(config.experiment_dir, experiment_uuid)
    
    if not os.path.isdir(experiment_dir):
        os.mkdir(experiment_dir)
        
    fname = os.path.join(experiment_dir, out_file)
    
    CC = Classifier().load()
    #  TODO: Compute the required height (function of experiment time and scan rate)
    height, width = 1000000, 100000
    db = Database()
    
    latents = []
    locations = []
    velocities = []
    frame_uuid = None
    s = "SELECT frame from frame where experiment = '{experiment}'"
    q = s.format(experiment=experiment_uuid)
    async for frame in db.query(q):
        frame_uuid = frame["frame"]
        
    s = "SELECT latent, location, perimeter from Track LEFT JOIN Particle USING(particle) WHERE frame = '{frame}'"
    q = s.format(frame=frame_uuid)
    
    async for particle in db.query(q):
        locations.append(particle["location"])
        latents.append([float(i) for i in particle["latent"][1:-1].split(',')])
        velocities.append(particle["perimeter"])
    
    locations = np.array(locations)
    latents = np.array(latents)
    velocities = np.array(velocities)
    
    # Let's just hack in a velocity parameter
    # by overriding the perimeter
    
    #todo: ensure maximum batchsize does not exceed capacity of GPU
    csize  = config.crop_size
    crops = CC.decoder.predict(np.array(latents))
    
    min_time = np.min(locations[:,1])
    max_time = np.max(locations[:,1])
    min_x = np.min(locations[:,0])
    max_x = np.max(locations[:,0])
    height = int((max_time) * SCAN_RATE)
    width = int(max_x)
    # TODO: add padding to frame for particles at boundary
    
    bg = imread(os.path.join(config.experiment_dir, "bg.png"), as_grey=True).astype("float64").squeeze() 
    bg = bg[500:5001,:]
    
    bg = resize(bg, (1,width))
    
    frame_data = np.tile(bg, (height,1))
    

    
    
    for particle in zip(locations, crops, velocities):
        # Y-position will be a function of velocity, time and scan rate
        x, y = particle[0]
        y = y * SCAN_RATE
        velocity = particle[2]
        
        pHeight = int(np.abs(csize * (SCAN_RATE / velocity)))
        # print("pHeight: "+str(pHeight))
        y1, y2, x1, x2 = y, y + pHeight, x, x + csize
        y1, y2, x1, x2 = [int(round(z)) for z in [y1, y2, x1, x2]]
        crop = CC.deproc(particle[1]) / 255.
        crop[crop > threshold(crop)] = 1             # Is this required?
        # crop = np.clip(crop.squeeze(), 0, 1)         # how about this?
        edge = 2
        crop = crop[edge:-edge, edge:-edge] # remove most of the nasty edge effects from the decoder
        # print("crop1 shape"+str(crop.shape))
        crop = resize(crop, [pHeight, csize], order=0)
        
        
        # print("frame shape"+str(frame_data.shape))
        # print("crop2 shape"+str(crop.shape))
        shape_buf = frame_data[y1:y2, x1:x2].shape
        # print("shape buf: "+str(shape_buf))
        blur_sigma = np.random.choice([1,2,3,4,5], 1)[0]
        frame_data[y1:y2, x1:x2] *= blur(crop, blur_sigma)[:shape_buf[0], :shape_buf[1]]
    
    print("frame shape: "+str(frame_data.shape))
    print("frame stats: "+str(np.min(frame_data))+' '+str(np.mean(frame_data))+' '+str(np.max(frame_data)))
    # Add some fines-like noise
    row,col= frame_data.shape
    mean = 25       # how much noise to add # BUG: anyting other than 0 breaks the imsave... WHY~?!?!?
    var = 30       # how much variance in the noise # BUG: anyting greater than 16 breaks the imsave... WHY~?!?!?
    
    sigma = var**0.5
    gauss = np.random.normal(mean, sigma, (row,col))
    
    print("gauss shape: "+str(gauss.shape))
    print("gauss stats: "+str(np.min(gauss))+' '+str(np.mean(gauss))+' '+str(np.max(gauss)))
    
    gauss = (100.0 - gauss)/100.0

    gauss = np.clip(gauss, 0.0, 1.0)

    print("gauss shape: "+str(gauss.shape))
    print("gauss stats: "+str(np.min(gauss))+' '+str(np.mean(gauss))+' '+str(np.max(gauss)))
    
    frame_data = frame_data * gauss
    
    print("frame shape: "+str(frame_data.shape))
    print("frame stats: "+str(np.min(frame_data))+' '+str(np.mean(frame_data))+' '+str(np.max(frame_data)))
    
    frame_data = np.clip((frame_data * 255.), 0, 255).astype("uint8")
    
    print("frame shape: "+str(frame_data.shape))
    print("frame stats: "+str(np.min(frame_data))+' '+str(np.mean(frame_data))+' '+str(np.max(frame_data)))
    print("frame type: "+str(type(frame_data)))
    print("element type: "+str(type(frame_data[0,0])))
    imsave(fname, frame_data)




    
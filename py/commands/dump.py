
from skimage import io

async def main(args):
    
    if len(args) == 0: print("What you want to dump? [frame|video]")
        
    else:
        if   args[0] == "frame":      dump_frame(args[1:])
        elif args[0] == "video":      dump_video(args[1:])
        else:                         print("Invalid grab sub-command")




async def dump_frame(args):
    
    if len(args) < 2: print("Please supply \"experiment frame_number out_file.png\"")
    else:
        db = Database()
        experiment = args[0]
        frame_number = int(args[1])
        outfile = int(args[2])
        
        async for record in db.query("""
            SELECT image, data, shape, dtype 
            FROM Image
            LEFT JOIN Frame USING (image)
            LEFT JOIN Experiment USING (experiment)
            WHERE experiment = $1 AND Frame.number = $2""", experiment, frame_number):
            
            
            print("Found", record["image"], record["shape"], record["dtype"])
            
            im = np.fromstring(b64decode(record["data"]), record["dtype"]).reshape(record["shape"])
            io.imsave(outfile, im.squeeze())


                

async def dump_video(args):

    if len(args) < 2: print("Please supply \"experiment out_file.mp4\"")
    else:
        db = Database()
        experiment = args[0]
        outfile = args[1]
        
        async for record in db.query("""
            SELECT video, data, shape, mime
            FROM Video
            LEFT JOIN Experiment USING (video)
            WHERE experiment = $1""", experiment):
            
            
            print("Found", record["video"], record["shape"], record["mime"])
            vid = b64decode(record["data"])
            
            with io.open(outfile, "wb") as out:
                out.write(vid)
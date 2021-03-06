

from skimage import io

async def main(args):
    
    if len(args) == 0: print("What you want to grab? [frame|background]")
        
    else:
        if   args[0] == "frame":      grab_frame(args[1:])
        if   args[0] == "extraction": grab_extraction(args[1:])
        elif args[0] == "background": grab_background(args[1:])
        else:                         print("Invalid grab sub-command")


def grab_frame(args):
    
    from lib.Video import Video
    
    if len(args) < 3: print("Please supply \"video frame_number image_file\"")
    else:
        video = Video(args[0])
        frame = video.frame(int(args[1]))
        io.imsave(args[2], frame.squeeze())

def grab_extraction(args):
    
    from lib.Video import Video
    
    if len(args) < 3: print("Please supply \"video frame_number image_file\"")
    else:
        video = Video(args[0])
        frame = video.normal_frame(int(args[1]))
        io.imsave(args[2], frame.squeeze())

def grab_background(args):
    
    from pyyx.Video import Video
    
    if len(args) < 2: print("Please supply \"video image_file\"")
    else:
        bg = Video(args[0]).extract_background()
        io.imsave(args[1], bg.squeeze())
    

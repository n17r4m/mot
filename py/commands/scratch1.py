

import time
from mpyx.Process import F
import numpy as np


async def main(args):

    file = "/mnt/SIA/BU-2017-07-27/MSBOT-010330000001.avi"
    
    #xmpfile = XMPFiles( file_path=file )
    #xmp = xmpfile.get_xmp()
    x = dirty_parse_xmp(file)
    print(x)
    
    
    """
    class BurstReader(F):
        def setup(self, file = "./ex.avi"):
            self.fp = open(file, 'rb')
        
            print(self.fp.read(1024))
            
            
            self.stop()
        
        
        def teardown(self):
            self.fp.close()
    
    
    
    
    BurstReader(file).execute()
    """
    
def dirty_parse_xmp(path):

    # Find the XMP data in the file
    xmp_data = ''
    xmp_started = False
    with open(path, 'rb') as infile:
        xmp_data = infile.read()
            
    xmp_open_tag = xmp_data.find(b'<x:xmpmeta')
    xmp_close_tag = xmp_data.find(b'</x:xmpmeta>')
    xmp_str = xmp_data[xmp_open_tag:xmp_close_tag + 12]

    print(xmp_open_tag, xmp_close_tag, len(xmp_data))

    # Pass just the XMP data to libxmp as a string
    #meta = libxmp.XMPMeta()
    #meta.parse_from_str(xmp_str)
    #return libxmp.utils.object_to_dict(meta)
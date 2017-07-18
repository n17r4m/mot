import os
import cv2
import shutil

crop_dir = "./crops"
done_dir = "./classified"

crops = os.listdir(crop_dir)

jn = os.path.join

print len(crops), "crops"

def classify_as(c, file):
    #change first letter.
    new = list(file)
    new[0] = c
    new = ''.join(new)
    shutil.move(jn(crop_dir, file), jn(done_dir, new))


for crop_file in crops:
    crop = cv2.imread(jn(crop_dir, crop_file))
    
    cv2.imshow("show", crop)
    key = cv2.waitKey(0)
    
    if key is 81: # left arrow    (sand)
        classify_as("s", crop_file) 
    elif key is 82: # up arrow    (drop)
        classify_as("d", crop_file)
    elif key is 83: # right arrow (bubble)
        classify_as("b", crop_file)
    elif key is 84: # down arrow  (unknown)
        classify_as("u", crop_file)
    elif key is 32: # spacebar    (skip)
        pass
    else:           # anykey      (quit)
        break 


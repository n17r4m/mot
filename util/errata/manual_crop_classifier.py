import os
import cv2
import shutil

crop_dir = "./crops"
done_dir = "./classified"

crops = os.listdir(crop_dir)

jn = os.path.join

print len(crops), "crops"

def classify_as(category, file):
    shutil.move(jn(crop_dir, file), jn(done_dir, category, file))


for crop_file in crops:
    crop = cv2.imread(jn(crop_dir, crop_file))
    
    cv2.imshow("show", crop)
    key = cv2.waitKey(0)
    
    if key is 81: # left arrow    
        classify_as("sand", crop_file) 
    elif key is 82: # up arrow    
        classify_as("bitumen", crop_file)
    elif key is 83: # right arrow 
        classify_as("bubble", crop_file)
    elif key is 84: # down arrow 
        classify_as("unknown", crop_file)
    elif key is 32: # spacebar   
        classify_as("undefined", crop_file)
    else:           # anykey      (quit)
        break 


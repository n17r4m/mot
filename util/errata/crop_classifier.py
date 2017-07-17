import os
import cv2

crop_dir = "./crops"

crops = os.listdir(crop_dir)

print len(crops), "crops"


for crop_file in crops:
    crop = cv2.imread(os.path.join(crop_dir, crop_file))
    
    cv2.imshow("show", crop)
    key = cv2.waitKey(0)
    
    print key


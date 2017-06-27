import sys
import cv2

if len(sys.argv) <= 1:
    print("Please view source.")
else:
    
    
    vc = cv2.VideoCapture(str(sys.argv[1]))
    # No error on first read
    ret, frame = vc.read()
    print ret, frame.shape
    # Error on all other reads
    ret, frame = vc.read()
    print ret, frame.shape
    # more reads are ok,
    ret, frame = vc.read()
    print ret, frame.shape

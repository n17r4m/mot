#
#
# This file contains a mix of helpers and code that was used
# early in the project. Mostly used for the disp_ helpers now.
#
#
import cv2
import matplotlib.pyplot as plt

import numpy as np

### display one image (convenience)
def disp_one(img):
    MIN=0
    MAX=256
    return plt.imshow(img, cmap = 'gray', interpolation='nearest',
                    vmin=MIN, vmax=MAX)

### display two images (convenience)
def disp_two(img1, img2, axis='off'):
    plt.subplot(121)
    plt.axis(axis)
    disp_one(img1)
    plt.subplot(122)
    plt.axis(axis)
    return disp_one(img2)

### display three images (convenience)
def disp_three(img1, img2, img3, axis='off'):
    plt.subplot(131)
    plt.axis(axis)
    plot1 = disp_one(img1)
    plt.subplot(132)
    plt.axis(axis)
    plot2 = disp_one(img2)
    plt.subplot(133)
    plt.axis(axis)
    plot3 = disp_one(img3)
    return plot1, plot2, plot3

### display four images (convenience)
def disp_four(img1, img2, img3, img4, axis='off'):
    plt.subplot(221)
    plt.axis(axis)
    plot1 = disp_one(img1)
    plt.subplot(222)
    plt.axis(axis)
    plot2 = disp_one(img2)
    plt.subplot(223)
    plt.axis(axis)
    plot3 = disp_one(img3)
    plt.subplot(224)
    plt.axis(axis)
    plot4 = disp_one(img4)
    return plot1, plot2, plot3, plot4

### display a sequence of images
def disp_seq(images, hz=1, axis='off'):
    # Note: Max ~1.5 FPS on my lappy
    plot = None
    for img in images:
        if plot is None:
            plot = disp_one(img)
            plt.axis(axis)
        else:
            plot.set_data(img)
        if hz == 0:
            plt.draw()
            while(plt.waitforbuttonpress()!=True):
                pass
        else:
            plt.pause(1.0/hz)

### display and compare two sequences of images
def disp_seq_compare(images1, images2=None, hz=1, axis='off'):
    # Note: Max ~1.5 FPS on my lappy
    plot = None
    for i in range(len(images1)):
        if plot is None:
            plt.subplot(121)
            plot1 = disp_one(images1[i])
            plt.axis(axis)
            plt.subplot(122)        
            if images2 is None:
                plt.hist(images1[i].ravel(), bins=256, normed=True, range=(0,255))
            else:
                plot2 = disp_one(images2[i])
            plt.axis(axis)
        else:
            plt.subplot(121)
            plot1.set_data(images1[i])
            plt.subplot(122)
            if images2 is None:
                plt.hist(images1[i].ravel(), bins=256, normed=True, range=(0,255))
            else:
                plot2.set_data(images2[i])
        if hz == 0:
            plt.draw()
            while(plt.waitforbuttonpress()!=True):
                pass
        else:
            plt.pause(1.0/hz)   

### Given images and regions, return
### a copy of images with regions drawn
def draw_regions(images, regions):
    N = len(images)
    out = []

    for i in range(N):
        buf = cv2.cvtColor(images[i], cv2.COLOR_GRAY2RGB)

        for pt1,pt2,area in regions[i]:
            cv2.rectangle(buf,pt1,pt2,(0,255,0),2)

        out.append(buf)

    return out

def draw_vectors(images, vectors, scale=1):  
    N = len(images)
    out = []

    for i in range(N-1):
        buf = cv2.cvtColor(images[i], cv2.COLOR_GRAY2RGB)

        for centre, delta in vectors[i]:
            cv2.arrowedLine(buf, tuple(centre), tuple(centre+scale*delta), (0,255,0),1)

        out.append(buf)

    return out

def draw_components(images, component_data, mask=None, circle=False):
    N = len(images)
    out = []

    for i in range(N):
        if (len(images[i].shape)==3):
            buf = images[i].copy()
        else:
            buf = cv2.cvtColor(images[i], cv2.COLOR_GRAY2RGB)

        M = component_data['num'][i]
        for j in range(M):

            if mask is not None and not mask[i][j]:
                continue

            if not circle:
                L, T, W, H, A = component_data['comp'][i][j]
                pt1 = (L,T)
                pt2 = (L+W,T+H)
                cv2.rectangle(buf,pt1,pt2,(0,255,0),2)
            else:
                centre = component_data['cent'][i][j]
                centre = int(centre[0]), int(centre[1])
                cv2.circle(buf, centre, 3, (0,255,0), -1)
        out.append(buf)

    return out

def draw_repeatability(images, component_data, mask, stats, deltas):
    # Get number of frames
    N = len(component_data['num'])

    ### Build Ground Truth, aka filtered frame 0
    f0_data = {'num': [component_data['num'][0]],
               'img': [component_data['img'][0]],
               'comp': [component_data['comp'][0]],
               'cent': [component_data['cent'][0]]}

    component_data_mask = mask
    M = len(component_data_mask[0])
   
    out = []

    # For every frame
    for j in range(N):
        if (len(images[j].shape)==3):
            buf = images[j].copy()
        else:
            buf = cv2.cvtColor(images[j], cv2.COLOR_GRAY2RGB)

        idx = 0
        for i in range(M):
            # Skip if didn't pass filter test
            if component_data_mask[0][i] is False:
                continue

            # Skip the background for now...
            if i == 0:
                continue

            if j != 0:
                score = stats[j-1][idx]

            l, t, w, h, a = component_data['comp'][0][i]
            pt1 = (l,t)
            pt2 = (l+w,t+h)

            # # Rectangle around ground truth detection
            # cv2.rectangle(buf,
            #               pt1,
            #               pt2,
            #               ((1-score)*255, 0, score*255),
            #               2)

            # Circle around expected area
            if j != 0:
                delta = deltas[j-1][idx]
            else:
                delta = [0,0]

            dx, dy = delta[0], delta[1]

            centre = component_data['cent'][0][i]
            centre = int(centre[0]+dx), int(centre[1]+dy)

            if j != 0:
                cv2.circle(buf, centre, 7, ((score)*255, 0, (1-score)*255), 3)
            else:                
                cv2.circle(buf, centre, 8, (0, 255, 0, 4))
                        
            idx += 1

        out.append(buf)

    return out

### returns an array with element wise max of A and B
def maximum (A, B):
    BisBigger = A-B
    BisBigger = np.where(BisBigger < 0, 1, 0)
    return A - A * BisBigger + B * BisBigger

### Compute the average value of a list of images
def average(images):
    MAX=255
    shape = images[0].shape
    area = shape[0] * shape[1]
    avg_bg = np.zeros(shape)

    N = len(images)
    for i in images:
            avg_bg += i * 1.0 / N

    avg_bg /= np.max(avg_bg)
    avg_bg = avg_bg*MAX

    return np.sum(avg_bg)/area

def Ix(img):
    pass
    return cv2.Sobel(img, cv2.CV_64F, 1,0)

def Iy(img):
    pass
    return cv2.Sobel(img, cv2.CV_64F, 0,1)

def img_gradients(img):
    pass
    return (Ix(img), Iy(img))


def img_diff(img1, img2, threshold=5, boost=False, absolute=False):
    MIN=0
    MAX=255
    diff = np.float64(img2)-np.float64(img1)

    if absolute:
        diff = np.uint8(np.abs(diff))

    diff[diff<threshold] = MIN

    if boost:
        diff[diff!=MIN] = MAX

    return diff

### Computes the average image over a video,
### and also the maximum image over a video.
def extract_background(video):
    cols = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    rows = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    shape = (int(rows), int(cols))

    avg_bg = np.zeros(shape)
    max_bg = np.zeros(shape)

    N = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)

    for i in range(N):
        video.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = video.read()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            avg_bg += frame * 1.0 / N
            max_bg = maximum(max_bg, frame)

        else:
            print "Error reading video frame " + str(i) + " ..."

        if i%100==0:
            print 'processed frame ' + str(i) + ' of ' + str(N-1)

    return np.uint8(avg_bg), np.uint8(max_bg)

### Given a list of images, returns a list of images
### whose backgrounds have been subtracted, leaving
### only foreground
def extract_foreground(images, background):
    N = len(images)
    out = []
    out2 = []

    images_avg = average(images)

    for i in range(N):
        i_avg = average([images[i]])
        bias = images_avg - i_avg
        foreground = adaptive_subtraction(images[i], background, bias)
        foreground2 = 255-cv2.absdiff(images[i], background)
        out.append(foreground)
        out2.append(foreground2)
    return out, out2

def extract_contour(images):
    N = len(images)

    out = []

    for i in range(N):
        contour = laplacian(images[i], bw=False)
        out.append(contour)

    return out

def extract_regions(images):
    N = len(images)

    out = []

    for i in range(N):

        out.append(floodfill(images[i]))
        # print 'regions extracted for image ' + str(i) + ' of ' + str(N-1)

    return out

def extract_fg_mask(images, threshold):
    N = len(images)

    out = []
    out2 = []
    out3 = []

    for i in range(N):
        _,buf = cv2.threshold(images[i], threshold, 255, cv2.THRESH_BINARY_INV)
        buf2 = cv2.adaptiveThreshold(images[i], 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 17, 15)
        _,buf3 = cv2.threshold(images[i],0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
        out.append(buf)
        out2.append(buf2)
        out3.append(buf3)
    return out, out2, out3

def extract_opticFlow_vectors(images, regions):
    N = len(images)

    out = []

    for i in range(N-1):
        frame = []
        grads = img_gradients(images[i])

        f0 = images[i]
        f1 = images[i+1]

        for pt1, pt2, area in regions[i]:
            y, x = np.array(pt2) - np.array(pt1)
            delta, error = optic_flow(f0, f1, grads, (pt1, pt2, area))
            delta = np.array(np.round(delta), dtype=int)

            if error <= 2.0:
                centre = np.array(pt1, dtype=int) + np.array([y/2.0, x/2.0], dtype=int)
                frame.append((centre, delta))

        out.append(frame)

    return out

def extract_component_data(images):
    '''

    num: number of components
    img: labelled imae
    comp: component stats
    cent: centroid data
    '''
    N = len(images)

    out = {'num': [],
           'img': [],
           'comp': [],
           'cent': []}

    for i in range(N):
        num, img, comp, cent  = cv2.connectedComponentsWithStats(images[i])

        out['num'].append(num)
        out['img'].append(img)
        out['comp'].append(comp)
        out['cent'].append(cent)

        print 'regions extracted for image ' + str(i) + ' of ' + str(N-1)

    return out

def component_mask(component_data, min_area=10, max_area=20000):
    '''

    Slow, but correct

    Returns a dictionary with 

    num: number of components ... int
    img: labelled image ... np.array
    comp: component stats ... list of tuples
    cent: centroid data ... list of *check docs...tuples?*
    '''
    # Init our output data structure
    out = []

    removed_total = 0
    kept_total = 0

    # Number of frames
    N = len(component_data['num'])

    for i in range(N):

        # Number of components in frame i
        M = component_data['num'][i]

        buf = []

        for j in range(M):

            # Stats for component j
            L, T, W, H, A = component_data['comp'][i][j]
            pt1 = (L,T)
            pt2 = (L+W,T+H)

            x, y = np.array(pt2) - np.array(pt1)

            if A < min_area or A > max_area:

                buf.append(False)
                removed_total += 1
                continue

            kept_total += 1
            buf.append(True)

        out.append(buf)


    # print "removed " + str(removed_total)
    # print "kept " + str(kept_total)

    return out

def remove_noise(regions):
    N = len(regions)

    out = []

    removed = 0
    kept = 0

    for i in range(N):

        temp = []

        for pt1,pt2,area in regions[i]:

            x, y = np.array(pt2) - np.array(pt1)

            ### Ignore large things
            if x>200 or y>200:
                removed += 1
                continue

            ### Ignore small things
            if x<3 or y<3:
                removed += 1
                continue

            kept += 1
            temp.append((pt1,pt2,area))

        out.append(temp)

    print "removed " + str(removed)
    print "kept " + str(kept)
    return out

### Load a burst from raw_video into a list
def load_burst(video, burst_number, burst_len=10):
    start_idx = burst_len*burst_number
    video.set(cv2.CAP_PROP_POS_FRAMES, start_idx)

    out = []

    for i in range(burst_len):
        ret, frame = video.read()

        if ret:            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            out.append(frame)
        else:
            print "Error reading video frame " + str(i) + " ..."

    return out

### load a video from file, read frames into list
def load_video(filename):
    video = cv2.VideoCapture(filename)
    video.set(cv2.CAP_PROP_POS_FRAMES, 0)
    N = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    out = []

    for i in range(N):
        ret, frame = video.read()

        if ret:            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            out.append(frame)
        else:
            print "Error reading video frame " + i + " ..."

    return out

def load_img(path):
    pass
    if cv2.__version__ == '3.2.0':
        return cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    else:
        return cv2.imread(path, cv2.CV_LOAD_IMAGE_GRAYSCALE)
 

def save_video(images, filename, verbose=False, hz=1):
    if len(images[0].shape) == 2:
        height, width = images[0].shape
        shape = (width, height)        
    elif len(images[0].shape) == 3:
        height, width, _ = images[0].shape
        shape = (width, height)

    # fourcc = cv2.VideoWriter_fourcc()
    # This is what works on my system ...
    fourcc = 33

    if len(images[0].shape) == 2:    
        out = cv2.VideoWriter(filename+'.mp4', fourcc, hz, shape, False)
    elif len(images[0].shape) == 3:
        out = cv2.VideoWriter(filename+'.mp4', fourcc, hz, shape, True)
    N = len(images)

    for i in range(N):
        frame = images[i]
        out.write(frame)

    if verbose:
        print 'video saved ...'



def find_limits(img,pos,seen):
    '''
    To be called by floodfill. 
    Given an image, a position to test, and a processed mask
    returns the min/max in both the x/y axis of a
    contiguous region   
    '''
    # Constants
    BG = 0
    FG = 255

    # Inits
    shape = (img.shape[0], img.shape[1])
    area = 0

    left, right, top, bottom = 0, shape[0]-1, 0, shape[1]-1
    x_min, x_max, y_min, y_max = right, left, bottom, top

    # Cute four sides check
    edges = [0,1,0,-1,0]

    stack1=[]

    # Set start conditions
    stack1.append(pos)

    while(len(stack1)>0):
        pos = stack1.pop()
        # print 'pos: '+str(pos)
        ### Process Current ###
        # Case: Foreground
        if img[pos] == FG:
            img[pos] = 128
            area+=1
            if pos[0] < x_min: x_min = pos[0]
            if pos[0] > x_max: x_max = pos[0]
            if pos[1] < y_min: y_min = pos[1]
            if pos[1] > y_max: y_max = pos[1]
        # Case: Background
        pass

        ### Process neighbours ###
        for i,j in zip(edges[:-1],edges[1:]):
            
            neighbour = (pos[0]+i, pos[1]+j)

            # Check limits
            if neighbour[0] < left or neighbour[0] > right:
                continue
            if neighbour[1] < top or neighbour[1] > bottom:
                continue

            # Check if processed already
            if seen[neighbour]:
                continue

            # Don't leave the region
            if img[neighbour] == BG:
                continue
            # print 'region stack append'
            stack1.append(neighbour)
            seen[neighbour]=True

    # print (x_min, x_max, y_min, y_max)
    # Note: subtract 1 for non-padded image limits
    return (y_min-1, x_min-1), (y_max, x_max), area

def floodfill(img):
    # Set limits

    # Constants
    BG = 0
    FG = 255

    # Inits
    shape = (img.shape[0]+2, img.shape[1]+2)
    img_padded = np.zeros(shape)
    img_padded[1:-1,1:-1] = img
    seen = np.full(shape, False, dtype=bool)

    left, right, top, bottom = 0, shape[0]-1, 0, shape[1]-1

    # Cute four sides check
    edges = [0,1,0,-1,0]
    regions=[]
    stack=[]

    # Set start conditions
    seed = (0,0)
    stack.append(seed)
    
    # debug 
    count = 0
    count2= 0
    while(len(stack)>0):
        pos = stack.pop()

        ### Process Current ###
        # Case: Background
        if img_padded[pos] == BG:
            img_padded[pos] = 192
            pass

        # Case: New foreground region
        else:
            count +=1
            regions.append(find_limits(img_padded, pos, seen))

        ### Process neighbours ###
        for i,j in zip(edges[:-1],edges[1:]):

            neighbour = (pos[0]+i, pos[1]+j)

            # Check limits
            if neighbour[0] < left or neighbour[0] > right:
                continue
            if neighbour[1] < top or neighbour[1] > bottom:
                continue

            # Check if processed already
            if seen[neighbour]:
                continue
            # print 'bg stack stack append'
            count2 += 1
            stack.append(neighbour)
            seen[neighbour] = True

    return regions



def overlap_over_area(idx, slice0, slice1):
    mask = slice0.copy()
    # disp_seq_compare([slice0], [slice1], 0)
    mask[mask != idx] = 0

    a = float(np.count_nonzero(mask))

    mask = mask*slice1

    ooa = np.count_nonzero(mask) / a

    return ooa, a

def measure_repeatability(images, component_data, mask):
    '''
    Given a list of images, with the assumption that there is little to
    no motion in the sequence, assesses the repeatability of a detector.

    A ground truth is created using frame f0 and all components meeting 
    a filter criteria (eg. area > 50). In each subsequent frame, the overlap
    area divided by the original area gives us a % score for a given object.

    '''
    # Get image boundaries
    shape = images[0].shape
    left, right, top, bottom = 0, shape[1]-1, 0, shape[0]-1

    # Get number of frames
    N = len(component_data['num'])

    ### Build Ground Truth, aka filtered frame 0
    f0_data = {'num': [component_data['num'][0]],
               'img': [component_data['img'][0]],
               'comp': [component_data['comp'][0]],
               'cent': [component_data['cent'][0]]}

    component_data_mask = mask

    out = []
    delta_out = []
    match_errors = []
    ### Compute scores  
    # Number of regions in filtered data
    M = len(component_data_mask[0])

    # Ground truth labeled image
    img0 = component_data['img'][0]
    tracks = {}

    # For every frame after f0
    for j in range(1,N):
        imgj = component_data['img'][j]
        buf = []
        delta_buf = []
        match_errors_buf = []
        for i in range(M):
            # Skip if didn't pass filter test
            if component_data_mask[0][i] is False:
                continue

            # Skip the background for now...
            if i == 0:
                continue

            l, t, w, h, a = component_data['comp'][0][i]


            ### TEMPLATE MATCHING SECTION
            search_delta = 1*max(w,h)
            match_threshold = 0.20
            if t-search_delta < top: t_s = top
            else: t_s = t-search_delta

            if t_s+(h+3*search_delta) > bottom: h_s = bottom-t+1
            else: h_s = h+3*search_delta

            if l-search_delta < left: l_s = left
            else: l_s = l-search_delta

            if l_s+w+3*search_delta > right: w_s = right-l+1
            else: w_s = w+3*search_delta

            match_src = images[j][t_s:t_s+h_s, l_s:l_s+w_s]
            match_template = images[0][t:t+h, l:l+w]

            if not i%200 and False:
                disp_seq_compare([match_src], [match_template],0)

            # print (t,h,l,w), (t_s,h_s,l_s,w_s)
            match_result = cv2.matchTemplate(match_src, match_template, cv2.TM_SQDIFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(match_result)

            dx, dy = l_s-l+min_loc[0], t_s-t+min_loc[1]

            if min_val > match_threshold:
                component_data_mask[0][i] = False
                continue

            match_errors_buf.append(min_val)
            
            delta_buf.append((dx, dy))


            ### END TEMPLATE MATCHING
            slice0 = img0[t:t+h, l:l+w]
            sliceN = imgj[t+dy:t+h+dy, l+dx:l+w+dx]

            ooa, a_comp  = overlap_over_area(i ,slice0, sliceN)

            if a != a_comp:
                print a, a_comp
                print "the computed area does not equal the built in area"
            
            buf.append(ooa)

            if i not in tracks:
                tracks[i] = []

            id_index = imgj[t+dy+h/2, l+dx+w/2]
            tracks[i].append(id_index)

            if min_val > 0.05:
                tracks[i] = [-1]

        out.append(buf)
        delta_out.append(delta_buf)
        match_errors.append(match_errors_buf)

    return out, delta_out, match_errors, tracks


### Computes the laplacian over an image, using some
### gaussian filters for noise reduction and region merging.
def laplacian(img, threshold=0.23, bw=True):
    MAX=255
    MIN=0
    in_filt_size = 3
    out_filt_size = 3

    output = np.float64(img.copy())

    # Low pass filter
    output = cv2.GaussianBlur(output,(in_filt_size,in_filt_size),0) 

    # Compute laplacian
    output = cv2.Laplacian(output,cv2.CV_64F)

    # Remove outside half of laplacian
    # conjecture: provides better separation of nearby regions
    output[output<0] = 0

    # Low pass filter
    # This helps join nearby regions
    output = cv2.GaussianBlur(output,(out_filt_size,out_filt_size),0)

    # kill outliers and scale to [0,1]
    rng = np.percentile(output, 99.9)
    output = output/rng
    output[output>1] = 1

    # Threshold
    output[output<threshold] = MIN

    # Convert to 8-bit grayscale
    output = np.uint8(255*output)

    if bw:
        output[output>0] = MAX

    return output

### Subtraction, but with rescaling based on range,
### defined as the intensity of the background at 
### a given position.
def adaptive_subtraction(img, background, threshold=15):
    output = np.float64(img) - np.float64(background-threshold)
    rng = np.float64(background-threshold)
    rng[rng<40] = 40
    output = 255.0 * (output/(rng))
    output += 255.0
    output[output>255] = 255

    return np.uint8(output)

def optic_flow(img0, img1, grads, region):
    pt1_0, pt2_0, area = np.array(region)

    pt1_0 = np.array(pt1_0)
    pt2_0 = np.array(pt2_0)
    ### Set limits
    left, right, top, bottom = 0, img0.shape[0]-1, 0, img0.shape[1]-1

    # ### Expand Bbox 
    # y, x = (np.array(pt2_0) - np.array(pt1_0)) / 10
    # print x, y
    # pt1_0 -= np.array([y, x], dtype=np.int)
    # pt2_0 += np.array([y, x], dtype=np.int)

    # ### ensure limits ok
    # if pt1_0[0] < top:
    #   offset = - pt1_0[0]
    #   pt1_0[0] += offset
    #   pt2_0[0] += offset
    # if pt1_0[1] < left:
    #   offset = - pt1_0[1]
    #   pt1_0[1] += offset
    #   pt2_0[1] += offset

    # if pt2_0[0] > bottom: 
    #   offset = bottom - pt2_0[0]
    #   pt1_0[0] += offset
    #   pt2_0[0] += offset
    # if pt2_0[1] > right: 
    #   offset = right - pt2_0[1]
    #   pt1_0[1] += offset
    #   pt2_0[1] += offset

    pt1_b, pt2_b = pt1_0.copy(), pt2_0.copy()

    bias = np.array([0,-35])
    # pt1_b += bias
    # pt2_b += bias

    pt1, pt2 = pt1_b.copy(), pt2_b.copy()



    template = np.float64( img0[pt1_0[1]:pt2_0[1], pt1_0[0]:pt2_0[0]] )
    proposal = np.float64( img1[pt1[1]:pt2[1],pt1[0]:pt2[0]] )

    # print template.shape, proposal.shape

    # plt.close('all')
    # plot = None
    # plot1, plot2, plot3, plot4 = comp_four(template, 
    #                                       proposal,
    #                                       img_diff(template, proposal, boost=True, absolute=False, threshold=40),
    #                                       np.abs(proposal - template))
    # while(plt.waitforbuttonpress()!=True):
    #   pass

    threshold = 2.0
    error = np.sqrt(np.sum((proposal - template)**2)) / np.float(area)

    delta = np.array([0.0, 0.0])
    itr = 0

    while error > threshold and itr < 50:
        # print "error: " + str(error)
        itr += 1

        Ix = grads[0][pt1[1]:pt2[1],pt1[0]:pt2[0]].ravel()
        Iy = grads[1][pt1[1]:pt2[1],pt1[0]:pt2[0]].ravel()
        b = img_diff(template, proposal, boost=True, absolute=False, threshold=40).ravel()

        Ix = Ix[np.where(b>0)]
        Iy = Iy[np.where(b>0)]
        b = b[np.where(b>0)]

        if b.shape[0] == 0:
            # print "exit on no diff..."
            return delta, error

        A = np.column_stack((Ix, Iy))

        cond_A = np.linalg.cond(A)

        if cond_A > 5 or cond_A < 0.25:
            # print "exit on cond..."
            return delta, error

        s = -np.linalg.lstsq(A, b)[0]

        delta += s
        pt1 = pt1_b + delta
        pt2 = pt2_b + delta

        ### ensure limits ok
        if pt1[0] < top:
            offset = - pt1[0]
            pt1[0] += offset
            pt2[0] += offset
        if pt1[1] < left:
            offset = - pt1[1]
            pt1[1] += offset
            pt2[1] += offset

        if pt2[0] > bottom: 
            offset = bottom - pt2[0]
            pt1[0] += offset
            pt2[0] += offset
        if pt2[1] > right: 
            offset = right - pt2[1]
            pt1[1] += offset
            pt2[1] += offset

        proposal = np.array(img1[pt1[1]:pt2[1],pt1[0]:pt2[0]], dtype=np.float64)
        # print proposal.shape
        error = np.sqrt(np.sum((proposal - template)**2)) / area

    #   plt.subplot(222)
    #   plot2.set_data(proposal)
    #   plt.draw()
    #   plt.subplot(223)
    #   plot3.set_data(img_diff(template, proposal, boost=True, absolute=False, threshold=40))
    #   plt.draw()
    #   plt.subplot(224)
    #   plot4.set_data(np.abs(proposal - template))
    #   plt.draw()
    #   while(plt.waitforbuttonpress()!=True):
    #       pass
    #   print delta, round(error, 2)

    # print "found match with error: " + str(round(error,2))
    # print delta
    if itr == 50:
        delta = np.array([0.0, 0.0])
    return delta, error


def paint(bg, sprite):
    alpha = np.float64(sprite[:,:,3])

    alpha_blur = np.float64(cv2.blur(alpha, (3,3)))
    alpha_blur = np.float64(cv2.GaussianBlur(alpha, (3,3), 2))
    alpha_blur /= 255.0

    alpha = sprite[:,:,0] * alpha_blur
    alpha /= 255.0
        


    shape = sprite.shape
    color = np.zeros((shape[0], shape[1]))
    beta = bg[500:500+shape[0], 500:500+shape[1],0]

    step1 = alpha
    step2 = (beta * alpha) 
    beta = step1 + beta * (1 - alpha_blur)
    # color = cv2.bilateralFilter(np.float32(color), 5, 20, 20)

    # beta = beta[:,:] * (1.0-alpha)

    return beta, step1, step2

def load_as_4channel(img):
    tmp = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    shape = tmp.shape
    shape = (shape[0], shape[1], 4)
    img = np.ones(shape)

    for i in range(3):
        img[:,:,i] = tmp

    return np.uint8(img)


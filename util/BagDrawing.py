import cv2

def drawCentroids(bag, frame, frame_no):
	centroids = bag.query('select x,y from assoc where frame == ' + str(frame_no))
	frame = frame.copy()

	if len(frame.shape) == 2:
		frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

	for x,y in centroids:
		x, y = int(round(x)), int(round(y))
		cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)

	return frame


def drawTrack(bag, frames, pid, start_frame, end_frame):
	out = [i.copy() for i in frames]

	if len(out[0].shape) == 2:
		out = [cv2.cvtColor(i, cv2.COLOR_GRAY2RGB) for i in out]

	res = bag.query('select a1.frame, a1.x, a1.y, a2.x, a2.y from assoc a1, assoc a2 where a1.frame == a2.frame-1 and a1.particle == a2.particle and a1.particle == ' +str(pid))

	n = end_frame - start_frame

	for frame, x1, y1, x2, y2 in res:
		i = frame - start_frame
		x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

		for j in range(0, end_frame-start_frame):			
			cv2.line(out[j], 
					 (x1, y1), 
					 (x2, y2),  
					 (255-i*255/n, 0, i*255/n), 
					 3)

	return out

def drawTracks(bag, frames, start_frame, end_frame, highlightParticles={}):
	out = [i.copy() for i in frames]

	if len(out[0].shape) == 2:
		out = [cv2.cvtColor(i, cv2.COLOR_GRAY2RGB) for i in out]

	res = bag.query('select a1.particle, a1.frame, a1.x, a1.y, a2.x, a2.y from assoc a1, assoc a2 where a1.frame == a2.frame-1 and a1.particle == a2.particle and a1.frame >= ' + str(start_frame) + ' and a1.frame < ' + str(end_frame))

	n = end_frame - start_frame

	for pid, frame, x1, y1, x2, y2 in res:
		i = frame - start_frame
		x1, y1, x2, y2 = int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2))

		for j in range(end_frame - start_frame):
			if pid in highlightParticles:
				cv2.line(out[j], 
						 (x1, y1), 
						 (x2, y2),  
						 (0, 255-i*255/n, i*255/n), 
						 3)				
			else:	
				cv2.line(out[j], 
						 (x1, y1), 
						 (x2, y2),  
						 (255-i*255/n, 0, i*255/n), 
						 3)

	return out






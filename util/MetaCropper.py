'''
MetaCropper gives the ability to work with multiple croppers and generate semi-random batches of 
crops
'''
from Cropper import Cropper
import numpy as np
import cv2
import json

class MetaCropper(object):
	def __init__(self, batch_size=1024, max_crops=10000000):
		self.croppers = []
		self.video_paths = []
		self.bag_paths = []

		self.training_crops_info = []
		self.validation_crops_info = []

		self.frames = None

		self.validation_step = 0
		self.training_step = 0

		self.training_steps = None
		self.validation_steps = None

		self.batch_size = batch_size
		self.max_crops = max_crops

	def save(self, filename, n):

		all_opts = []
		for c in self.croppers:
			all_opts.append(c.opts)

		save = {'cropper_opts': all_opts,
				'video_paths': self.video_paths,
				'bag_paths': self.bag_paths,
				'training_crops_info': self.training_crops_info[:n].tolist(),
				'training_steps': self.training_steps,
				'training_step': self.training_step,
				'validation_crops_info': self.validation_crops_info[:n].tolist(),
				'validation_steps': self.validation_steps,
				'validation_step': self.validation_step,
				'batch_size': self.batch_size,
				'max_crops': self.max_crops}

		with open(filename, 'w') as fp:
			json.dump(save, fp)
		# np.save(filename, save)

	def load(self, filename):
		# save = np.load(filename)
		with open(filename, 'r') as fp:
			save = json.load(fp)

		for i in range(len(save['video_paths'])):
			c = Cropper(save['video_paths'][i], save['bag_paths'][i], save['cropper_opts'][i])
			self.addCropper(c)

		self.training_crops_info = np.array(save['training_crops_info'])
		self.training_steps = save['training_steps']
		self.training_step = save['training_step']

		self.validation_crops_info = np.array(save['validation_crops_info'])
		self.validation_steps = save['validation_steps']
		self.validation_step = save['validation_step']

		self.batch_size = save['batch_size']
		self.max_crops = save['max_crops']


	def addCropper(self, cropper):
		self.video_paths.append(cropper.fgrabber.video_path)
		self.croppers.append(cropper)
		self.bag_paths.append(cropper.bag_path)

	def prepareFrames(self):
		self.getAllFrames()
		self.shuffleFrames()
		self.splitFrames()

	def getFrames(self, bag):
	    res = bag.query('SELECT DISTINCT a.frame FROM assoc a where a.frame%11')
	    return np.array(res, dtype=int)

	def getAllFrames(self):
		'''
		Get frames from all croppers' databags.
		'''
		frames = []
		index = 0

		for cropper in self.croppers:
			bag = cropper.bag
			buf = self.getFrames(bag)
			indexes = np.empty((buf.shape[0],1), dtype=int)
			indexes.fill(index)
			buf = np.concatenate((buf, indexes), 1)
			frames.extend(buf)
			index += 1

		self.frames = np.array(frames)

	def shuffleFrames(self):
		pass
		np.random.shuffle(self.frames)

	def splitFrames(self, proportion=0.8):
		'''
		Split all frames into a training set and a validation set.

		proportion is the % of data to be assigned to training
		'''
		self.proportion = proportion
		split = int(proportion * len(self.frames))
		self.training_frames = self.frames[:split]
		self.validation_frames = self.frames[split:]		

	def getCropsInfoInFrame(self, cropper, frame):
		info = []
		res = cropper.bag.query('SELECT particle FROM assoc a WHERE frame=='+str(frame))
		info = np.array([i[0] for i in res], dtype=int)
		
		return info.reshape(info.shape[0],1)

	def getAllCropsInfo(self):
		self.getCropsInfo('training')
		self.getCropsInfo('validation')
		
		n = len(self.training_crops_info)
		m = len(self.validation_crops_info)
		
		total_crops = n + m

		if total_crops > self.max_crops:
			proportion = float(self.max_crops) / total_crops
			n = int(proportion * n)

			m = int(proportion * m)


		n = (n/self.batch_size) * self.batch_size
		m = (m/self.batch_size) * self.batch_size

		self.training_crops_info = self.training_crops_info[:n]
		self.training_steps = len(self.training_crops_info) / self.batch_size
		
		self.validation_crops_info = self.validation_crops_info[:m]
		self.validation_steps = len(self.validation_crops_info) / self.batch_size

	def getCropsInfo(self, frame_set):
		'''
		arguments:
		frame_set can be 'training' or 'validation'

		returns:
		info is of the form [(cropper_index, frame_index, particle_index),...]
		'''
		info = []
		
		if frame_set == 'training':
			frames = self.training_frames
		elif frame_set == 'validation':
			frames = self.validation_frames

		for j in range(len(frames)):
			cropper_index = frames[j][1]
			frame = frames[j][0]
			buf = self.getCropsInfoInFrame(self.croppers[cropper_index], frame)
			indexes = np.full((buf.shape[0], 2), (cropper_index, frame))
			buf = np.concatenate((indexes, buf), 1)
			info.extend(buf)
			j += 1

		info = np.array(info)

		if frame_set == 'training':
			self.training_crops_info = info
			
		elif frame_set == 'validation':
			self.validation_crops_info = info
		
		return info

	def getCrop(self, cropper, frame, particle_index):
		crop = cropper.isolate(frame, particle_index)        
		crop = cv2.resize(crop, (cropper.size, cropper.size), interpolation = cv2.INTER_CUBIC)
		crop = np.float32(crop)

		return crop

	def yieldCrops(self, frame_set):
		if frame_set == 'training':
			info = self.training_crops_info
			m = self.training_steps
		elif frame_set == 'validation':
			info = self.validation_crops_info
			m = self.validation_steps

		j=0
		while True:
			j=j%m
			crops = []
			batch_info = info[j*self.batch_size:j*self.batch_size+self.batch_size]

			for cropper_index, frame_index, particle_index in batch_info:
				cropper = self.croppers[cropper_index]			
				crops.append(self.getCrop(cropper, frame_index, particle_index))

			crops = np.stack(crops)
			crops = crops.astype('float32') / 255.

			crops = crops.reshape((len(crops), np.prod(crops.shape[1:])))
			
			j+=1

			yield (crops, crops)

	def getCrops(self, frame_set, reshape=True):
		'''
		arguments:
		frame_set can be 'training' or 'validation'

		returns:
		crops of (batch_size, img_dim1*img_dim2*...)
		'''
		crops = []
		
		if frame_set == 'training':
			info = self.training_crops_info
			j = self.training_step
			m = self.training_steps
		elif frame_set == 'validation':
			info = self.validation_crops_info
			j = self.validation_step
			m = self.validation_steps

		batch_info = info[((j%m)*self.batch_size):((j%m)*self.batch_size)+self.batch_size]

		for cropper_index, frame_index, particle_index in batch_info:
			cropper = self.croppers[cropper_index]			
			crops.append(self.getCrop(cropper, frame_index, particle_index))

		if frame_set == 'training':
			self.training_step = j+1
		elif frame_set == 'validation':
			self.validation_step = j+1

		crops = np.stack(crops)
		crops = crops.astype('float32') / 255.

		if reshape:
			crops = crops.reshape((len(crops), np.prod(crops.shape[1:])))
		return crops
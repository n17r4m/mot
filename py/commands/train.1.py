"""
A command that should enable the user to train a learning model.ArithmeticError

First designed for DeepVelocity...

Todo:
DeepVelocity
    - will need a data generator
    - will need a trainer
"""

import config

import numpy as np
import os
import atexit
import time
import asyncio
import multiprocessing
import traceback
from uuid import UUID
from skimage import io

from lib.Database import Database
from lib.models.DeepVelocity import DeepVelocity

dataGenerator = None

async def main(args):
    global dataGenerator
    if len(args) == 0: 
        print("What you want to train? [DeepVelocity|...]")
    else:
        return await train(args)

async def train(args):
    try:
        if args[0] == "DeepVelocity":
            return await train_DeepVelocity(args)
    except Exception as e:
        print("Uh oh. Something went wrong")
        traceback.print_exc()
    finally:
        dataGenerator.close()
    print('Fin')


async def train_DeepVelocity(args):
    DV = DeepVelocity(lr=0.0003)
    model = DV.probabilityNetwork
    # model = DummyModel()
    dataGenerator = DVDataGen()

    if args[1] == "view":
        DV.load("DVProbNetwork.h5")
        await DVViewer(model=model,
                       dataGenerator=dataGenerator)
    else:
        await trainer(args[1:], 
                      model=model,
                      dataGenerator=dataGenerator)
        # DV.save('DVProbNetwork.h5')
        
        
async def DVViewer(model, dataGenerator):
    pass
    dataGenerator = dataGenerator
    await dataGenerator.setup()
    
    dataBatch = await dataGenerator.trainBatch()
    
    dataBatch.denormalize("frame", 
                          dataGenerator.frameMean, 
                          dataGenerator.frameStd)
    dataBatch.denormalize("location", 
                          dataGenerator.locationMean, 
                          dataGenerator.locationStd)  
                        
    scale = 0.001
    
    for dataInput, dataOutput in dataBatch:
        if dataOutput[0][0] == 0.0:
            print("negative example found...")
            continue
        loc1, lat1, f1, loc2, lat2, f2 = dataInput
        
        
        SIZE = 101
        for scale in [0.00001,0.0001,0.001,0.01,0.1,1.0]:
            visData = DataBatch()
            for i in range(SIZE):
                for j in range(SIZE):
                    x1, y1 = loc1
                    dx = (i-SIZE//2) / scale
                    dy = (j-SIZE//2) / scale
                    
                    loc2 = (x1+dx, y1+dy)
                    
                    dataInput[3] = loc2
                    
                    visData.addInput(dataInput)
                    
            visData.toNumpy()
            
            visData.normalize("frame", 
                              dataGenerator.frameMean, 
                              dataGenerator.frameStd)
            visData.normalize("location", 
                              dataGenerator.locationMean, 
                              dataGenerator.locationStd)
            
            probs = model.predict(visData.getInput())[:,0]
            
            screenBuf = np.zeros((SIZE, SIZE))
            count = 0
            
            for i in range(SIZE):
                for j in range(SIZE):
                    screenBuf[j,i] = probs[count]
                    count += 1
            
            io.imsave('screenBuf{scale}.png'.format(scale=scale), screenBuf)
            np.save('screenBuf', screenBuf)
        
        break
        
async def trainer(args, model, dataGenerator):
    '''
    Args: epochs, batchSize
    
    Feature Requests:
    - save the best model weights as training progresses
    
    '''
    epochs = int(args[0])
    batchSize = int(args[1])
    
    dataGenerator = dataGenerator
    await dataGenerator.setup(batchSize=batchSize,
                              epochs=epochs)
    
    model = model
    
    trainingLosses = []
    testLosses = []

    modelMetrics = model.metrics_names
    numMetrics = len(modelMetrics)
    print("Begin Training...")
    for epoch in range(epochs):
        # Train Section
        batchLosses = []
        epochStart = time.time()
        
        for batchNum in range(dataGenerator.numTrainBatch):
            if not epoch and batchNum==1:
                print("First batch", time.time()-epochStart)
                batchStart = time.time()
            if not epoch and batchNum==2:
                print("Second batch", time.time()-batchStart)
                
            dataBatch = await dataGenerator.trainBatch()
            batchStart = time.time()
            batchLoss = model.train_on_batch(dataBatch.getInput(), dataBatch.getOutput())
            batchLosses.append(batchLoss)
            # print(batchNum, batchLoss, time.time()-batchStart)
            
        epochLoss = np.mean(batchLosses, axis=0)
        trainingLosses.append(epochLoss)
        
        model.save("DVProbNetwork.h5")
        
        # Printing section
        trainTime = time.time() - epochStart
        metricMsg = '{0}: {1}'
        metricMsgs = [metricMsg.format(modelMetrics[i], epochLoss[i]) for i in range(numMetrics)]
        metrics = ', '.join(metricMsgs)
        
        trainingMessage = "Training loss - epoch {epoch} - {time} s - {metrics}"
        print(trainingMessage.format(epoch=epoch+1,
                                     time=trainTime,
                                     metrics=metrics))
        
        # Test Section
        batchLosses = []
        epochStart = time.time()
        
        for batchNum in range(dataGenerator.numTestBatch):
            dataBatch = await dataGenerator.testBatch()
            batchLoss = model.test_on_batch(dataBatch.getInput(), dataBatch.getOutput())
            batchLosses.append(batchLoss)

        epochLoss = np.mean(batchLosses, axis=0)
        testLosses.append(epochLoss)
        
        # Printing section
        testTime = time.time() - epochStart
        metricMsg = '{0}: {1}'
        metricMsgs = [metricMsg.format(modelMetrics[i], epochLoss[i]) for i in range(numMetrics)]
        metrics = ', '.join(metricMsgs)
        
        testMessage = "Test loss     - epoch {epoch} - {time} s - {metrics}"
        print(testMessage.format(epoch=epoch+1,
                                     time=testTime,
                                     metrics=metrics))
    
    print("Done")
    
class DataBatch():
    def __init__(self):
        self.data = dict()
        
        self.data["frame"] = {"A": [], "B": []}
        self.data["latent"] = {"A": [], "B": []}
        self.data["location"] = {"A": [], "B": []}
        self.data["output"] = []
        self.current = 0
    
    def combine(self, dataBatch):
        '''
        combines two databatches using the randomMasks method
        '''
        self.randomMasks()
        self.data["frame"]["A"][self.mask["frame"]["A"]] = dataBatch.data["frame"]["A"][self.mask["frame"]["A"]]
        self.data["frame"]["B"][self.mask["frame"]["B"]] = dataBatch.data["frame"]["B"][self.mask["frame"]["B"]]
        self.data["latent"]["A"][self.mask["latent"]["A"]] = dataBatch.data["latent"]["A"][self.mask["latent"]["A"]]
        self.data["latent"]["B"][self.mask["latent"]["B"]] = dataBatch.data["latent"]["B"][self.mask["latent"]["B"]]
        self.data["location"]["A"][self.mask["location"]["A"]] = dataBatch.data["location"]["A"][self.mask["location"]["A"]]
        self.data["location"]["B"][self.mask["location"]["B"]] = dataBatch.data["location"]["B"][self.mask["location"]["B"]]
        self.data["output"][self.mask["output"]] = dataBatch.data["output"][self.mask["output"]]
    
    def randomMasks(self):
        self.mask = dict()
        
        self.mask["frame"] = {"A": [], "B": []}
        self.mask["latent"] = {"A": [], "B": []}
        self.mask["location"] = {"A": [], "B": []}
        self.mask["output"] = []        
        
        frameProb = 0.9
        latentProb = 0.5
        locationProb = 0.5
        
        split = len(self) // 2
        
        self.mask["frame"]["A"] = np.random.random(len(self.data["frame"]["A"]))
        self.mask["frame"]["B"] = np.random.random(len(self.data["frame"]["B"]))
        self.mask["latent"]["A"] = np.random.random(len(self.data["latent"]["A"]))
        self.mask["latent"]["B"] = np.random.random(len(self.data["latent"]["B"]))
        self.mask["location"]["A"] = np.random.random(len(self.data["location"]["A"]))
        self.mask["location"]["B"] = np.random.random(len(self.data["location"]["B"]))
        
        self.mask["frame"]["A"][self.mask["frame"]["A"]>=frameProb] = 1
        self.mask["frame"]["A"][self.mask["frame"]["A"]<frameProb] = 0
        self.mask["frame"]["B"][self.mask["frame"]["B"]>=frameProb] = 1
        self.mask["frame"]["B"][self.mask["frame"]["B"]<frameProb] = 0
        self.mask["latent"]["A"][self.mask["latent"]["A"]>=latentProb] = 1
        self.mask["latent"]["A"][self.mask["latent"]["A"]<latentProb] = 0
        self.mask["latent"]["B"][self.mask["latent"]["B"]>=latentProb] = 1
        self.mask["latent"]["B"][self.mask["latent"]["B"]<latentProb] = 0
        self.mask["location"]["A"][self.mask["location"]["A"]>=locationProb] = 1
        self.mask["location"]["A"][self.mask["location"]["A"]<locationProb] = 0
        self.mask["location"]["B"][self.mask["location"]["B"]>=locationProb] = 1
        self.mask["location"]["B"][self.mask["location"]["B"]<locationProb] = 0
        
        self.mask["frame"]["A"] = np.array(self.mask["frame"]["A"], dtype=bool)
        self.mask["frame"]["B"] = np.array(self.mask["frame"]["B"], dtype=bool)
        self.mask["latent"]["A"] = np.array(self.mask["latent"]["A"], dtype=bool)
        self.mask["latent"]["B"] = np.array(self.mask["latent"]["B"], dtype=bool)
        self.mask["location"]["A"] = np.array(self.mask["location"]["A"], dtype=bool)
        self.mask["location"]["B"] = np.array(self.mask["location"]["B"], dtype=bool)
        
        self.mask["frame"]["A"][:split] = False
        self.mask["frame"]["B"][:split] = False
        self.mask["latent"]["A"][:split] = False
        self.mask["latent"]["B"][:split] = False
        self.mask["location"]["A"][:split] = False
        self.mask["location"]["B"][:split] = False
        
        self.mask["output"] = np.zeros(len(self.data["output"]), dtype=bool)
        self.mask["output"][split:] = True
        
    def join(self, dataBatch):
        self.data["frame"]["A"].extend(dataBatch.data["frame"]["A"])
        self.data["frame"]["B"].extend(dataBatch.data["frame"]["B"])
        self.data["latent"]["A"].extend(dataBatch.data["latent"]["A"])
        self.data["latent"]["B"].extend(dataBatch.data["latent"]["B"])
        self.data["location"]["A"].extend(dataBatch.data["location"]["A"])
        self.data["location"]["B"].extend(dataBatch.data["location"]["B"])
        self.data["output"].extend(dataBatch.data["output"])
        
    def toNumpy(self):
        self.data["frame"]["A"] = np.array(self.data["frame"]["A"], dtype=float)
        self.data["frame"]["B"] = np.array(self.data["frame"]["B"], dtype=float)
        self.data["latent"]["A"] = np.array(self.data["latent"]["A"])
        self.data["latent"]["B"] = np.array(self.data["latent"]["B"])
        self.data["location"]["A"] = np.array(self.data["location"]["A"])
        self.data["location"]["B"] = np.array(self.data["location"]["B"])
        self.data["output"] = np.array(self.data["output"])

    def shuffle(self):
        rng_state = np.random.get_state()
        
        for k,v in self.data.items():
            if isinstance(v, dict):
                for _k, _v in v.items():
                    np.random.shuffle(_v)
                    np.random.set_state(rng_state)
            else:
                np.random.shuffle(v)
                np.random.set_state(rng_state)
            
    def normalize(self, feature, mean, std):
        self.data[feature]["A"] -= mean
        self.data[feature]["A"] /= std
        self.data[feature]["B"] -= mean
        self.data[feature]["B"] /= std
        
    def denormalize(self, feature, mean, std):
        self.data[feature]["A"] *= std
        self.data[feature]["A"] += mean
        self.data[feature]["B"] *= std
        self.data[feature]["B"] += mean
                
    def addInput(self, A):
        '''
        eng = [locationA, latentA, frameA,
               locationB, latentB, frameB]
        '''
        self.addLocation(A[0], A[3])
        self.addLatent(A[1], A[4])
        self.addFrame(A[2], A[5])
        
    def getInput(self, start=None, end=None):
        engA = [self.data["location"]["A"][start:end],
                self.data["latent"]["A"][start:end],
                self.data["frame"]["A"][start:end]]
        
        engB = [self.data["location"]["B"][start:end],
                self.data["latent"]["B"][start:end],
                self.data["frame"]["B"][start:end]]
                
        return engA + engB
        
    def getOutput(self, start=None, end=None):
        return self.data["output"][start:end]
    
    def addOutput(self, A):
        self.data["output"].append(A)
        
    def addLocation(self, A, B):
        self.data["location"]["A"].append(A)
        self.data["location"]["B"].append(B)
        
    def addLatent(self, A, B):
        self.data["latent"]["A"].append(A)
        self.data["latent"]["B"].append(B)
    
    def addFrame(self, A, B):
        self.data["frame"]["A"].append(A)
        self.data["frame"]["B"].append(B)
        
    def setOutput(self, A):
        self.data["output"] = A
        
    def __len__(self):
        return len(self.data["output"])
        
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.current > len(self):
            raise StopIteration
        else:
            self.current += 1
            
            dataInputs = self.getInput(self.current-1, self.current)
            dataInput = [i[0] for i in dataInputs]
            dataOutput = self.getOutput(self.current-1, self.current)
            
            return (dataInput, dataOutput)
        
class DVDataGen(object):
    
    def __init__(self):
        self.numDataPoints = None
        self.numTrainBatch = None
        self.numTestBatch = None
        self.splitPercent = 0.8
        self.method =  "tracking%"
        
        self.db = Database()
    
        self.processors = []
        
    def _split(self):
        '''
        Convert a percentage split into a uuid split.Convert
        
        Since all data in database is given a unique UUID
        and because uuids are distributed randomly, we'll
        split the data using uuid.
        '''
        num = 0xFFFFFFFF * self.splitPercent
        trail = '-0000-0000-0000-000000000000'
        lead = '{:08x}'.format(int(num))
        self.split = lead + trail
        
    async def setup(self, batchSize=128, epochs=5):
        self.batchSize = batchSize
        self.epochs = epochs
        print("running DVDataGen setup")
        
        await self._numDataPoints()
        print("number of datapoints computed", self.numDataPoints)
        
        self._split()
        print("split computed")
        
        self.numTrainBatch = int((self.splitPercent*self.numDataPoints) / self.batchSize)
        print("num training batches computed", self.numTrainBatch)
        
        self.numTestBatch = int(((1.0-self.splitPercent)*self.numDataPoints) / self.batchSize)
        print("num test batches computed", self.numTestBatch)
        print("fitting dataset sample")
        
        await self._fit()
        print("frame mean/std", self.frameMean, self.frameStd)
        print("loc mean/std", self.locationMean, self.locationStd)
        
        self.dbTrainQueryQueue = multiprocessing.Queue()
        self.dbTrainResultQueue = multiprocessing.Queue(1000)
        self.trainBatchQueue = multiprocessing.Queue(10)
    
        self.dbTestQueryQueue = multiprocessing.Queue()
        self.dbTestResultQueue = multiprocessing.Queue(1000)
        self.testBatchQueue = multiprocessing.Queue(10)
        
        self.dbTrainNegQueryQueue = multiprocessing.Queue()
        self.dbTrainNegResultQueue = multiprocessing.Queue(1000)
        self.trainNegBatchQueue = multiprocessing.Queue(10)
    
        self.dbTestNegQueryQueue = multiprocessing.Queue()
        self.dbTestNegResultQueue = multiprocessing.Queue(1000)
        self.testNegBatchQueue = multiprocessing.Queue(10)        
    
        for _ in range(epochs):
            q = self._trainBatchQuery()
            self.dbTrainQueryQueue.put(q)
            q = self._testBatchQuery()
            self.dbTestQueryQueue.put(q)
            
            q = self._trainNegBatchQuery()
            self.dbTrainNegQueryQueue.put(q)
            q = self._testNegBatchQuery()
            self.dbTestNegQueryQueue.put(q)            
            
        self.dbTrainQueryQueue.put(None)
        self.dbTestQueryQueue.put(None)
        self.dbTrainNegQueryQueue.put(None)
        self.dbTestNegQueryQueue.put(None)        

        self.trainQueryProcessor = DVQueryProcessor(self.dbTrainQueryQueue,
                                                    self.dbTrainResultQueue)
                                               
        self.trainQueryProcessor.start()
        self.processors.append(self.trainQueryProcessor)
        
        self.trainResultProcessor = DVResultProcessor(self.dbTrainResultQueue, 
                                                      self.trainBatchQueue,
                                                      self.batchSize,
                                                      [1.0, 0.0])
        self.trainResultProcessor.start()
        self.processors.append(self.trainResultProcessor)
        
        self.testQueryProcessor = DVQueryProcessor(self.dbTestQueryQueue,
                                                   self.dbTestResultQueue)
                                               
        self.testQueryProcessor.start()
        self.processors.append(self.testQueryProcessor)
         
        self.testResultProcessor = DVResultProcessor(self.dbTestResultQueue, 
                                                     self.testBatchQueue,
                                                     self.batchSize,
                                                     [1.0, 0.0])
        self.testResultProcessor.start()
        self.processors.append(self.testResultProcessor)
        
        self.trainNegQueryProcessor = DVQueryProcessor(self.dbTrainNegQueryQueue,
                                                    self.dbTrainNegResultQueue)
                                               
        self.trainNegQueryProcessor.start()
        self.processors.append(self.trainNegQueryProcessor)
        
        self.trainNegResultProcessor = DVResultProcessor(self.dbTrainNegResultQueue, 
                                                      self.trainNegBatchQueue,
                                                      self.batchSize,
                                                      [0.0, 1.0])
        self.trainNegResultProcessor.start()
        self.processors.append(self.trainNegResultProcessor)
        
        self.testNegQueryProcessor = DVQueryProcessor(self.dbTestNegQueryQueue,
                                                   self.dbTestNegResultQueue)
                                               
        self.testNegQueryProcessor.start()
        self.processors.append(self.testNegQueryProcessor)
        
        self.testNegResultProcessor = DVResultProcessor(self.dbTestNegResultQueue, 
                                                     self.testNegBatchQueue,
                                                     self.batchSize,
                                                     [0.0, 1.0])
        self.testNegResultProcessor.start() 
        self.processors.append(self.testNegResultProcessor)
        
    def _trainNegBatchQuery(self):
        q = """
            SELECT f1.experiment as experiment1,
                   f2.experiment as experiment2,
                   f1.frame as frame1, 
                   f2.frame as frame2, 
                   t1.track as track1,
                   t2.track as track2,
                   t1.latent as lat1,
                   t2.latent as lat2,
                   t1.location as loc1,
                   t2.location as loc2
            FROM track t1, track t2, frame f1, frame f2, experiment
            WHERE t1.particle = t2.particle
            AND t1.frame = f1.frame
            AND t2.frame = f2.frame
            AND f1.number = f2.number-1
            AND t1.track < '{split}'
            AND f1.experiment = experiment.experiment
            AND UPPER(experiment.method) LIKE  UPPER('{method}')
            ORDER BY random()
            """
        s = q.format(split=self.split,
                     limit=self.numDataPoints,
                     method=self.method)
        return s
        
    def _trainBatchQuery(self):
        q = """
            SELECT f1.experiment as experiment1,
                   f2.experiment as experiment2,
                   f1.frame as frame1, 
                   f2.frame as frame2, 
                   t1.track as track1,
                   t2.track as track2,
                   t1.latent as lat1,
                   t2.latent as lat2,
                   t1.location as loc1,
                   t2.location as loc2
            FROM track t1, track t2, frame f1, frame f2, experiment
            WHERE t1.particle = t2.particle
            AND t1.frame = f1.frame
            AND t2.frame = f2.frame
            AND f1.number = f2.number-1
            AND t1.track < '{split}'
            AND f1.experiment = experiment.experiment
            AND UPPER(experiment.method) LIKE  UPPER('{method}')
            ORDER BY random()
            """
        s = q.format(split=self.split,
                     method=self.method)
        return s
    
    def _testNegBatchQuery(self):
        q = """
            SELECT *
            FROM 
                  (SELECT experiment.experiment as experiment1,
                          frame.frame as frame1,
                          track as track1,
                          latent as lat1,
                          location as loc1,
                          row_number() OVER (ORDER BY random()) as r1
                   FROM track, frame, experiment
                   WHERE track.frame = frame.frame
                   AND track.track < '{split}'
                   AND frame.experiment = experiment.experiment
                   AND UPPER(experiment.method) LIKE  UPPER('{method}')
                   LIMIT {limit}) as t1,
                  (SELECT experiment.experiment as experiment2,
                          frame.frame as frame2,
                          track as track2,
                          latent as lat2,
                          location as loc2,
                          row_number() OVER (ORDER BY random()) as r2
                   FROM track, frame, experiment
                   WHERE track.frame = frame.frame
                   AND track.track > '{split}'
                   AND frame.experiment = experiment.experiment
                   AND UPPER(experiment.method) LIKE  UPPER('{method}')
                   LIMIT {limit}) as t2
            WHERE t1.r1 = t2.r2
            """
        s = q.format(split=self.split,
                     limit=self.numDataPoints,
                     method=self.method)
        return s
        
    def _testBatchQuery(self):
        q = """
            SELECT f1.experiment as experiment1,
                   f2.experiment as experiment2,
                   f1.frame as frame1, 
                   f2.frame as frame2, 
                   t1.track as track1,
                   t2.track as track2,
                   t1.latent as lat1,
                   t2.latent as lat2,
                   t1.location as loc1,
                   t2.location as loc2
            FROM track t1, track t2, frame f1, frame f2, experiment
            WHERE t1.particle = t2.particle
            AND t1.frame = f1.frame
            AND t2.frame = f2.frame
            AND f1.number = f2.number-1
            AND t1.track > '{split}'
            AND f1.experiment = experiment.experiment
            AND UPPER(experiment.method) LIKE  UPPER('{method}')
            ORDER BY random()
            """
        s = q.format(split=self.split,
                     method=self.method)
        return s
        
    async def _fit(self):
        '''
        grabs a large sample from the database, to compute 
        approximate data means.
        Currently computes:
            - frame means
            - location means
        '''
        sampleSize = 10000
        frames = []
        locations = []
        
        async for result in self.db.query("""
                                          SELECT f1.experiment,
                                                 f1.frame as frame1, 
                                                 f2.frame as frame2, 
                                                 t1.track as track1,
                                                 t2.track as track2,
                                                 t1.latent as lat1,
                                                 t2.latent as lat2,
                                                 t1.location as loc1,
                                                 t2.location as loc2
                                          FROM track t1, track t2, frame f1, frame f2, experiment
                                          WHERE t1.particle = t2.particle
                                          AND t1.frame = f1.frame
                                          AND t2.frame = f2.frame
                                          AND f1.number = f2.number-1
                                          AND t1.track < $2
                                          AND f1.experiment = experiment.experiment
                                          AND UPPER(experiment.method) LIKE  UPPER($3)
                                          ORDER BY random()
                                          limit $1
                                          """,
                                          sampleSize,
                                          self.split,
                                          self.method):
            
            frameFile1 = os.path.join(config.experiment_dir, 
                                      str(result["experiment"]),
                                      str(result["frame1"]),
                                      '64x64.png')
                                     
            frameFile2 = os.path.join(config.experiment_dir, 
                                      str(result["experiment"]),
                                      str(result["frame2"]),
                                      '64x64.png')
                                      
            frame1 = io.imread(frameFile1, as_grey=True)
            frame2 = io.imread(frameFile2, as_grey=True)
            
            frames.append(frame1)
            frames.append(frame2)
            
            locations.append(result["loc1"])
            locations.append(result["loc2"])
        
        self.frameMean = np.mean(frames)
        self.frameStd = np.std(frames)
        self.locationMean = np.mean(locations)
        self.locationStd = np.std(locations)
            
    async def _numDataPoints(self):
        q = """
            SELECT COUNT(t1.particle) as numdatapoints
            FROM track t1, track t2, frame f1, frame f2, experiment
            WHERE t1.particle = t2.particle
            AND t1.frame = f1.frame
            AND t2.frame = f2.frame
            AND f1.number = f2.number-1
            AND f1.experiment = experiment.experiment
            AND UPPER(experiment.method) LIKE  UPPER('{method}')
            """
        s = q.format(method=self.method)
        async for result in self.db.query(s):
            self.numDataPoints = result['numdatapoints']
        
        # self.numDataPoints = 10000
    
    async def _batch(self, posQueue, negQueue):
        
        dataBatch = posQueue.get()
        negDataBatch = negQueue.get()
        
        dataBatch.toNumpy()
        negDataBatch.toNumpy()
        
        dataBatch.combine(negDataBatch)
        
        dataBatch.normalize("frame", 
                            self.frameMean, 
                            self.frameStd)
        dataBatch.normalize("location", 
                            self.locationMean, 
                            self.locationStd)
        
        dataBatch.shuffle()

        return dataBatch
        
    async def trainBatch(self):
        posQueue = self.trainBatchQueue
        negQueue = self.trainNegBatchQueue
        return await self._batch(posQueue, negQueue)

    async def testBatch(self):
        posQueue = self.testBatchQueue
        negQueue = self.testNegBatchQueue
        return await self._batch(posQueue, negQueue)

    def close(self):
        for p in self.processors:
            p.terminate()
        
        print('All datagen processes terminated')
        
class DVQueryProcessor(multiprocessing.Process):
    def __init__(self, inputQueue, outputQueue):
        super(DVQueryProcessor, self).__init__()
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        
    def run(self):
        self.go(self.inner_loop, ())
    
    def go(self, fn, args):
        return asyncio.new_event_loop().run_until_complete(fn(*args))
    
    async def inner_loop(self):
        print("DVQueryProcessor ready.")
        db = Database()
        while True:
            if not self.stopped():
                sql_drop = self.inputQueue.get()
                if sql_drop is None:
                    self.stop()
                else:
                    query = sql_drop
                    async for result in db.query(query):
                        if self.stopped():
                            break
                        
                        loc1 = (result["loc1"][0], result["loc1"][1])
                        loc2 = (result["loc2"][0], result["loc2"][1])
                        
                        r = {"experiment1": result["experiment1"],
                             "experiment2": result["experiment2"],
                             "frame1": result["frame1"],
                             "frame2": result["frame2"],
                             "track1": result["track1"],
                             "track2": result["track2"],
                             "lat1": result["lat1"],
                             "lat2": result["lat2"],
                             "loc1": loc1,
                             "loc2": loc2}
                             
                        self.outputQueue.put(r)
            else:
                break
        print("DVQueryProcessor Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()    
    
class DVResultProcessor(multiprocessing.Process):
    def __init__(self, inputQueue, outputQueue, batchSize, label):
        super(DVResultProcessor, self).__init__()
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        self.batchSize = batchSize
        self.label = label
        
    def run(self):
        # await self.inner_loop(Database().transaction, self.queue)
        self.go(self.inner_loop, ())
    
    def go(self, fn, args):
        return asyncio.new_event_loop().run_until_complete(fn(*args))
    
    # dun know if this works or not.. todo: test.
    async def inner_loop(self):
        print("DVResultProcessor ready.")
        d = DataBatch()
        count = 0
        while True:
            if not self.stopped():
                result = self.inputQueue.get()
                if result is None:
                    self.stop()
                else:
                    if count == self.batchSize:
                        # Add batch to output queue
                        
                        self.outputQueue.put(d)
                        # reset d
                        d = DataBatch()
                        count = 0
                        
                    frameFile1 = os.path.join(config.experiment_dir, 
                                              str(result["experiment1"]),
                                              str(result["frame1"]),
                                              '64x64.png')
                                     
                    frameFile2 = os.path.join(config.experiment_dir, 
                                              str(result["experiment2"]),
                                              str(result["frame2"]),
                                              '64x64.png')
                    
                    frame1 = io.imread(frameFile1, as_grey=True)
                    frame2 = io.imread(frameFile2, as_grey=True)
                    
                    latentA_string = result["lat1"][1:-1].split(',')
                    latentA = [float(i) for i in latentA_string]
                    
                    latentB_string = result["lat2"][1:-1].split(',')
                    latentB = [float(i) for i in latentB_string]   
                    
                    locationA = result["loc1"]
                    locationB = result["loc2"]
                    
                    d.addFrame(frame1, frame2)
                    d.addLatent(latentA, latentB)
                    d.addLocation(locationA, locationB)
                    d.addOutput(self.label)
                    
                    count += 1
            else:
                break
        self.outputQueue.put(None)
        print("DBResultProcessor Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()    
    
class DummyModel(object):
    def __init__(self):
        self.metrics_names = ['foo', 'bar']
        
def exit():
    dataGenerator.close()
    print('Ok')
    
atexit.register(exit)
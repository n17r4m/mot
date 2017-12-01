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
import sys
# import atexit
import time
import asyncio
import multiprocessing
import traceback
from uuid import UUID
from skimage import io

from lib.Database import Database
from lib.models.DeepVelocity import DeepVelocity

async def main(args):
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
        
    except KeyboardInterrupt:
        print("You killed it...")
        
    print('Fin')

async def train_DeepVelocity(args):
    os.environ["CUDA_VISIBLE_DEVICES"]="1"
    print('Parent CUDA',os.environ["CUDA_VISIBLE_DEVICES"])
    
    
    dataGenerator = DVDataGen(debug=False)
    DV = DeepVelocity(lr=0.0003)

        
    try:
        if args[1] == "view":
            await DVViewer(model=DV,
                           dataGenerator=dataGenerator)
        else:
            epochs = int(args[1])
            batchSize = int(args[2])
            await dataGenerator.setup(batchSize=batchSize,
                                      epochs=epochs)
            if len(args) == 4:
                DV.load_model(args[3])    
            else:
                DV.compile()
            model = DV.probabilityNetwork 
                
            await trainer(args[1:], 
                          model=model,
                          dataGenerator=dataGenerator)
    except:
        traceback.print_exc()
        dataGenerator.close()
        
async def DVViewer(model, dataGenerator):
    
    dataGenerator = dataGenerator
    await dataGenerator.setup()
    
    DV = model 
    model = DV.probabilityNetwork

    dataGenerator.epochBegin()
    dataGenerator.trainBegin()
    
    dataBatch = await dataGenerator.trainBatch()
    
    dataBatch.denormalize(dataGenerator.normalizeParams)
    
    weightFile = "/local/scratch/mot/py/lib/models/weights/DVexp3-epoch{epoch}.h5"
    
    negCount = 1
    posCount = 0
    outputData = []
    screenCount = 0

    for dataInput, dataOutput in dataBatch:
        if posCount==1 and negCount==1:
            break
        if dataOutput[0][0] == 0.0:
            label='neg'
            print("negative example found...")
            if negCount or not posCount:
                continue
        else:
            label='pos'
            print("positive example found...")
            if posCount:
                continue
            
        loc1, lat1, f1, loc2, lat2, f2 = dataInput
        
        SIZE = 101
        scaleData = []
        for scale in [0.001,0.01,0.1,1.0]:
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
            
            visData.normalize(dataGenerator.normalizeParams)

            epochData = []
            
            for epoch in range(31):
                DV.load_model(weightFile.format(epoch=epoch+1))
                model = DV.probabilityNetwork
                probs = model.predict(visData.getInput())[:,0]
                
                screenBuf = np.zeros((SIZE, SIZE))
                count = 0
                
                for i in range(SIZE):
                    for j in range(SIZE):
                        screenBuf[j,i] = probs[count]
                        count += 1
                screenCount += 1
                print("screen count", screenCount)
                epochData.append(screenBuf)
            scaleData.append(epochData)
        outputData.append(scaleData)
        
        if label=='pos':
            posCount+=1
        elif label=='neg':
            negCount+=1
        if posCount and negCount:
            break
    np.save('screenBuf', np.array(outputData))
        
async def trainer(args, model, dataGenerator):
    '''
    Args: epochs, batchSize
    
    Feature Requests:
    - save the best model weights as training progresses
    
    '''
    startEpoch = 0
    epochs = int(args[0])
    batchSize = int(args[1])
    weightFile = "DVProbNetwork.h5"
                              
    if len(args) == 3:          
        startEpoch = int(args[2].split("epoch")[-1].split(".")[0])
        dataGenerator.changeWeights(weightFile)
    
    trainingLosses = []
    testLosses = []

    modelMetrics = model.metrics_names
    numMetrics = len(modelMetrics)
    print("Begin Training...")
    dataGenerator.epochBegin()
    for epoch in range(startEpoch, epochs):
        # Train Section
        batchLosses = []
        epochStart = time.time()
        
        dataGenerator.trainBegin()
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
            sys.stdout.write("Training epoch progress: %d%% %ds   \r" % (100*float(batchNum+1)/dataGenerator.numTrainBatch, time.time()-epochStart) )
            sys.stdout.flush()
            # print(batchNum, batchLoss, time.time()-batchStart)
        
        epochLoss = np.mean(batchLosses, axis=0)
        trainingLosses.append(epochLoss)
        
        
        model.save_weights(weightFile)
        
        modelFile = "/local/scratch/mot/py/lib/models/weights/DVexp3-epoch{epoch}.h5".format(epoch=epoch+1)
        model.save(modelFile)
        
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
        dataGenerator.testBegin()
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
                                     
        dataGenerator.epochEnd()
        dataGenerator.changeWeights(weightFile)
        
    print("Done")
    
class DataBatch():
    def __init__(self):
        self.data = dict()
        
        self.data["frame"] = {"A": [], "B": []}
        self.data["latent"] = {"A": [], "B": []}
        self.data["location"] = {"A": [], "B": []}
        self.data["output"] = []
        self.current = 0
    
    def copy(self):
        '''
        return a copy of this databatch
        '''
        foo = DataBatch()
        
        for k,v in self.data.items():
            if isinstance(v, dict):
                for _k, _v in v.items():
                    foo.data[k][_k] = _v.copy()
            else:
                foo.data[k] = v.copy()
        
        return foo
        
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
        # self.data["output"][self.mask["output"]] = dataBatch.data["output"][self.mask["output"]]
    
    def randomMasks(self):
        self.mask = dict()
        
        self.mask["frame"] = {"A": [], "B": []}
        self.mask["latent"] = {"A": [], "B": []}
        self.mask["location"] = {"A": [], "B": []}
        self.mask["output"] = []        
        
        # Probability of a feature remaining unchanged... sort of
        # we'll take the complement for A B state pairs probability
        # to guarantee only either A or B are randomized
        probs = {"frame": 0.5,
                 "latent": 0.5,
                 "location": 0.5}
        
        keys = ["frame", "latent", "location"]
        
        selectedKeys = np.random.choice(keys, size=1, replace=False)
        
        for key in selectedKeys:
            prob = probs[key]
            self.mask[key]["A"] = np.random.random(len(self.data[key]["A"]))
            self.mask[key]["B"] = 1.0 - self.mask[key]["A"]
            self.mask[key]["A"][self.mask[key]["A"]>=prob] = 1
            self.mask[key]["A"][self.mask[key]["A"]<prob] = 0
            self.mask[key]["B"][self.mask[key]["B"]>=prob] = 1
            self.mask[key]["B"][self.mask[key]["B"]<prob] = 0
            self.mask[key]["A"] = np.array(self.mask[key]["A"], dtype=bool)
            self.mask[key]["B"] = np.array(self.mask[key]["B"], dtype=bool)
            
        # self.mask["frame"]["A"] = np.random.random(len(self.data["frame"]["A"]))
        # self.mask["frame"]["B"] = 1.0 - self.mask["frame"]["A"]
        # self.mask["latent"]["A"] = np.random.random(len(self.data["latent"]["A"]))
        # self.mask["latent"]["B"] = 1.0 - self.mask["latent"]["A"]
        # self.mask["location"]["A"] = np.random.random(len(self.data["location"]["A"]))
        # self.mask["location"]["B"] = 1.0 - self.mask["location"]["A"]
        
        # self.mask["frame"]["A"][self.mask["frame"]["A"]>=frameProb] = 1
        # self.mask["frame"]["A"][self.mask["frame"]["A"]<frameProb] = 0
        # self.mask["frame"]["B"][self.mask["frame"]["B"]>=frameProb] = 1
        # self.mask["frame"]["B"][self.mask["frame"]["B"]<frameProb] = 0
        # self.mask["latent"]["A"][self.mask["latent"]["A"]>=latentProb] = 1
        # self.mask["latent"]["A"][self.mask["latent"]["A"]<latentProb] = 0
        # self.mask["latent"]["B"][self.mask["latent"]["B"]>=latentProb] = 1
        # self.mask["latent"]["B"][self.mask["latent"]["B"]<latentProb] = 0
        # self.mask["location"]["A"][self.mask["location"]["A"]>=locationProb] = 1
        # self.mask["location"]["A"][self.mask["location"]["A"]<locationProb] = 0
        # self.mask["location"]["B"][self.mask["location"]["B"]>=locationProb] = 1
        # self.mask["location"]["B"][self.mask["location"]["B"]<locationProb] = 0
        
        # self.mask["frame"]["A"] = np.array(self.mask["frame"]["A"], dtype=bool)
        # self.mask["frame"]["B"] = np.array(self.mask["frame"]["B"], dtype=bool)
        # self.mask["latent"]["A"] = np.array(self.mask["latent"]["A"], dtype=bool)
        # self.mask["latent"]["B"] = np.array(self.mask["latent"]["B"], dtype=bool)
        # self.mask["location"]["A"] = np.array(self.mask["location"]["A"], dtype=bool)
        # self.mask["location"]["B"] = np.array(self.mask["location"]["B"], dtype=bool)
        
        # self.mask["frame"]["A"][:split] = False
        # self.mask["frame"]["B"][:split] = False
        # self.mask["latent"]["A"][:split] = False
        # self.mask["latent"]["B"][:split] = False
        # self.mask["location"]["A"][:split] = False
        # self.mask["location"]["B"][:split] = False
        
        # self.mask["output"] = np.zeros(len(self.data["output"]), dtype=bool)
        # self.mask["output"][split:] = True
        
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
            
    def normalize(self, params):
        for feature, stats in params.items():
            mean, std = stats
            self.data[feature]["A"] -= mean
            self.data[feature]["A"] /= std
            self.data[feature]["B"] -= mean
            self.data[feature]["B"] /= std
        
    def denormalize(self, params):
        for feature, stats in params.items():
            mean, std = stats        
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
    
    def addDataPoint(self, d):
        self.addLocation(d["loc1"], d["loc2"])
        self.addLatent(d["lat1"], d["lat2"])
        self.addFrame(d["frame1"], d["frame2"])
        self.addOutput(d["output"])
        
    def getDataPoint(self, i):
        r = {"frame1": self.data["frame"]["A"][i],
             "frame2": self.data["frame"]["B"][i],
             "lat1": self.data["latent"]["A"][i],
             "lat2": self.data["latent"]["B"][i],
             "loc1": self.data["location"]["A"][i],
             "loc2": self.data["location"]["B"][i],
             "output": self.data["output"][i]
            }
        return r
                             
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
    
    def __init__(self, debug=False):
        self.numDataPoints = None
        self.numTrainBatch = None
        self.numTestBatch = None
        self.splitPercent = 0.8
        self.method =  "simulation_tracking"
        self.debug = debug
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
        
        self.normalizeParams = await self._fit()
        for feature, stats in self.normalizeParams.items():
            print("{feature} mean/std {stats}".format(feature=feature,
                                                      stats=stats))

        trainQueryQueue = multiprocessing.Queue()
        trainDataQueue = multiprocessing.Queue(2000)
        self.trainBatchQueue = multiprocessing.Queue(5)

        testQueryQueue = multiprocessing.Queue()
        testDataQueue = multiprocessing.Queue(2000)
        self.testBatchQueue = multiprocessing.Queue(5)
    
        for _ in range(epochs*2):
            q = self._trainBatchQuery()
            trainQueryQueue.put(q)
            q = self._testBatchQuery()
            testQueryQueue.put(q)
            
        trainQueryQueue.put(None)
        testQueryQueue.put(None)

        trainQueryProcessor = DVQueryProcessor(trainQueryQueue,
                                               trainDataQueue)
        trainQueryProcessor.daemon=True
        trainQueryProcessor.start()
        self.processors.append(trainQueryProcessor)
        
        testQueryProcessor = DVQueryProcessor(testQueryQueue,
                                              testDataQueue)
        testQueryProcessor.daemon=True
        testQueryProcessor.start()
        self.processors.append(testQueryProcessor)
         
        batchProcessor = DVBatchProcessor(batchSize=self.batchSize,
                                          normalizeParams=self.normalizeParams,
                                          trainInputQueue=trainDataQueue,
                                          trainOutputQueue=self.trainBatchQueue,
                                          testInputQueue=testDataQueue,
                                          testOutputQueue=self.testBatchQueue)
            
        batchProcessor.daemon=True
        batchProcessor.start()
        self.batchProcessor = batchProcessor
        self.processors.append(batchProcessor)
        
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
        
        if self.debug:
            frameMean = 172.2
            frameStd = 21.8
            locationMean = 1000.0
            locationStd = 585
        else:
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
            
            frameMean = np.mean(frames)
            frameStd = np.std(frames)
            locationMean = np.mean(locations)
            locationStd = np.std(locations)
        
        d = {"frame": None, "location": None}
        d["frame"] = (frameMean, frameStd)
        d["location"] = (locationMean, locationStd)
        
        return d
            
    async def _numDataPoints(self):
        if self.debug:
            self.numDataPoints = 10000
            return
    
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
        
    async def trainBatch(self):
        return self.trainBatchQueue.get()

    async def testBatch(self):
        return self.testBatchQueue.get()

    def epochBegin(self):
        pass
    def epochEnd(self):
        pass
    def trainBegin(self):
        self.batchProcessor.train()
    def trainEnd(self):
        pass
    def testBegin(self):
        self.batchProcessor.test()
    def testEnd(self):
        pass
    
    def changeWeights(self, weightFile):
        self.batchProcessor.changeWeights(weightFile)

    def close(self):
        for p in self.processors:
            p.terminate()
        print('All datagen processes terminated')
        
class DVQueryProcessor(multiprocessing.Process):
    '''
    Input:  database sql queries
    Output: dictionary containing a single row from the
            query results, processed to include assets
            loaded from the filesystem.
    '''
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

                        frameFile1 = os.path.join(config.experiment_dir, 
                                              str(result["experiment1"]),
                                              str(result["frame1"]),
                                              '64x64.png')
                        frame1 = io.imread(frameFile1, as_grey=True)
                        
                        frameFile2 = os.path.join(config.experiment_dir, 
                                                  str(result["experiment2"]),
                                                  str(result["frame2"]),
                                                  '64x64.png')
                        frame2 = io.imread(frameFile2, as_grey=True)
                        
                        latent1_string = result["lat1"][1:-1].split(',')
                        latent1 = [float(i) for i in latent1_string]
                        
                        latent2_string = result["lat2"][1:-1].split(',')
                        latent2 = [float(i) for i in latent2_string]   
                        
                        r = {"frame1": frame1,
                             "frame2": frame2,
                             "lat1": latent1,
                             "lat2": latent2,
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

class DVPredictionProcessor(multiprocessing.Process):
    '''
    Input: a tensor of data
    Output: a list of predictions for the tensor
    '''
    def __init__(self, weightsQueue, inputQueue, outputQueue):
        super(DVPredictionProcessor, self).__init__()
        self.inputQueue = inputQueue
        self.outputQueue = outputQueue
        self.weightsQueue = weightsQueue
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        
    def run(self):
        # await self.inner_loop(Database().transaction, self.queue)
        self.go(self.inner_loop, ())
    
    def go(self, fn, args):
        return asyncio.new_event_loop().run_until_complete(fn(*args))
    
    # dun know if this works or not.. todo: test.
    async def inner_loop(self):
        print("DVPredictionProcessor ready.")
        os.environ["CUDA_VISIBLE_DEVICES"]="0"
        print('Child CUDA',os.environ["CUDA_VISIBLE_DEVICES"])

        model = DeepVelocity().probabilityNetwork
            
        while True:
            if self.stopped():
                break
            if not self.weightsQueue.empty():
                # while not self.outputQueue.empty():
                #     self.outputQueue.get()
                weightFile = self.weightsQueue.get()
                model.load_weights(weightFile)
                print("Loaded new weights...")
            d = self.inputQueue.get()
            probs = model.predict(d)
            self.outputQueue.put(probs)
                    
        print("DVNegativeProcessor Exiting")
        
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()  
    
class DVBatchProcessor(multiprocessing.Process):
    '''
    Input: rows from DVQueryProcessor
    Output: a DataBatch of DV data
    '''
    def __init__(self, batchSize, normalizeParams,
                 trainInputQueue, trainOutputQueue,
                 testInputQueue, testOutputQueue):
        super(DVBatchProcessor, self).__init__()
        
        self.batchSize = batchSize
        self.normalizeParams = normalizeParams
        
        self.queues = {"input": dict(),
                       "output": dict(),
                       "control": dict()}
        self.queues["input"]["train"] = trainInputQueue
        self.queues["output"]["train"] = trainOutputQueue
        self.queues["input"]["test"] = testInputQueue
        self.queues["output"]["test"] = testOutputQueue
        self.queues["input"]["predict"] = multiprocessing.Queue()
        self.queues["output"]["predict"] = multiprocessing.Queue()
        self.queues["control"] = multiprocessing.Queue()
        self.queues["weight"] = multiprocessing.Queue()
        
        self.model = DVPredictionProcessor(self.queues["weight"],
                                           self.queues["input"]["predict"],
                                           self.queues["output"]["predict"])
        self.model.start()
        
        self.stop_event = multiprocessing.Event()
        self.commit_event = multiprocessing.Event()
        
        self.mode = None
        
    def train(self):
        self.queues["control"].put("train")
        
    def test(self):
        self.queues["control"].put("test")
        
    def changeWeights(self, weightFile):
        self.queues["weight"].put(weightFile)
        
    def run(self):
        self.go(self.inner_loop, ())
    
    def go(self, fn, args):
        return asyncio.new_event_loop().run_until_complete(fn(*args))
    
    def controlPending(self):
        return not self.queues["control"].empty()
    
    async def controlMsg(self):
        return self.queues["control"].get()
        
    async def inner_loop(self):
        predInputQueue = self.queues["input"]["predict"]
        predOutputQueue = self.queues["output"]["predict"]
        total=0
        count=0
        while True:
            if self.stopped():
                break
            if self.controlPending() or self.mode is None:
                
                # print("mode is ", self.mode)
                if self.mode == "test":
                    print("accepted / total", count, total)
                    total=0
                    count=0
                self.mode = self.queues["control"].get()
                # print("mode set to", self.mode)
                inputQueue = self.queues["input"][self.mode]
                outputQueue = self.queues["output"][self.mode]
                
            dataBatch = DataBatch()
            batchReady=False
            while len(dataBatch) < self.batchSize // 2:
                if self.stopped():
                    break
                if self.controlPending():
                    break
                    
                d = inputQueue.get()

                dataBatch.addFrame(d["frame1"], d["frame2"])
                dataBatch.addLatent(d["lat1"], d["lat2"])
                dataBatch.addLocation(d["loc1"], d["loc2"])
                dataBatch.addOutput([1.0, 0.0])
                # print("pos accepted")
                
            negBatch = DataBatch()
            while len(negBatch) < self.batchSize // 2:
                if self.stopped():
                    break
                if self.controlPending():
                    break
                dataBatchTmp1 = dataBatch.copy()
                dataBatchTmp2 = dataBatch.copy()
                dataBatchTmp1.toNumpy()
                dataBatchTmp2.toNumpy()
                dataBatchTmp2.shuffle()
                dataBatchTmp1.combine(dataBatchTmp2)
            
                dataBatchTmp1.normalize(self.normalizeParams)
                predInputQueue.put(dataBatchTmp1.getInput())
                probs = predOutputQueue.get()
                dataBatchTmp1.denormalize(self.normalizeParams)
    
                for i in range(len(probs)):
                    if self.stopped():
                        break
                    if self.controlPending():
                        break
                    bias = probs[i][0]
                    addData = int(np.random.random() + bias)
                    total+=1
                    if addData:
                        d = dataBatchTmp1.getDataPoint(i)
                        d["output"] = [0.0, 1.0]
                        negBatch.addDataPoint(d)
                        # print("neg accepted")
                        count+=1
                    if len(negBatch) == self.batchSize // 2:
                        batchReady=True
                        break
            if batchReady:
                dataBatch.join(negBatch)
                dataBatch.toNumpy()
                dataBatch.shuffle()
                dataBatch.normalize(self.normalizeParams)
                outputQueue.put(dataBatch)
            
        print("DVBatchProcessor Exiting")
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()    
    
class DummyModel(object):
    def __init__(self):
        self.metrics_names = ['foo', 'bar']
        
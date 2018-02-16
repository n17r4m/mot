"""
Various utils to retreive from database and export to file
"""


import config
from lib.Database import Database

import os
import shutil
from uuid import UUID
from dateutil.parser import parse as dateparse
import logging
import config

from lib.pymot.pymot import MOTEvaluation

from mpyx.F import EZ, As, By, F
from mpyx.F import Serial, Parallel, Broadcast, S, P, B
from mpyx.F import Iter, Const, Print, Map, Filter, Batch, Seq, Zip, Read, Write


async def main(args):
    
    if len(args) == 0: print("What evaluation would you like to run? [pymot]")
        
    else:
        if args[0] == "pymot":
                await evaluatePymot(args[1:])
        if args[0] == "pymotMethod":
                await evaluateMethod(args[1:])
        if args[0] == "pymotSegment":
                await evaluatePymotBySegment2(args[1:])
        if args[0] == "pymotMethodSegment":
                await evaluateMethodSegment(args[1:])
        else:                         
                print("Invalid export sub-command")


async def evaluateMethodSegment(args):
    groundTruth = args[0]
    method = args[1]

    db = Database()
    s = """
        SELECT experiment, method
        FROM experiment
        WHERE method LIKE '{method}%'
        ORDER BY method ASC
        """
    q = s.format(method=method)
    logFile = os.path.join(config.data_dir, "pymot", "eval_"+method+"_"+groundTruth+".log")
    logger = logging.getLogger('pyMotEval')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    async for result in db.query(q):
        experimentA = groundTruth
        experimentB = str(result["experiment"])
        print("Evaluating Experiment:", experimentB)
        logger.info("Evaluating Experiment:"+ str(experimentB))
        print("Method:", result["method"])
        logger.info("Method:"+ str(result["method"]) )
        await evaluatePymotBySegment2([experimentA, experimentB])
        # logger.info("MOTA "+str(mota))

async def evaluateMethod(args):
    groundTruth = args[0]
    method = args[1]

    db = Database()
    s = """
        SELECT experiment, method
        FROM experiment
        WHERE method LIKE '{method}%'
        ORDER BY method ASC
        """
    q = s.format(method=method)
    logFile = os.path.join(config.data_dir, "pymot", "eval_"+method+"_"+groundTruth+".log")
    logger = logging.getLogger('pyMotEval')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(logFile)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    async for result in db.query(q):
        experimentA = groundTruth
        experimentB = str(result["experiment"])
        print("Evaluating Experiment:", experimentB)
        logger.info("Evaluating Experiment:"+ str(experimentB))
        print("Method:", result["method"])
        logger.info("Method:"+ str(result["method"]) )
        mota = await evaluatePymot([experimentA, experimentB])
        logger.info("MOTA "+str(mota))

async def evaluatePymot(args):
    '''
    A will be considered ground truth
    B will be up for evaluation
    
    feature request:
    - evaluate by segment
    '''
    db = Database()
     
    experimentA = args[0]
    experimentB = args[1]
    
    jsonA = {"frames": [], "class": "video", "filename": experimentA}
    jsonB = {"frames": [], "class": "video", "filename": experimentB}
    
    q = """
        SELECT frame, number
        FROM frame
        WHERE experiment = '{experiment}'
        ORDER BY number ASC
        """
    sA = q.format(experiment = experimentA)
    
    # print("converting experiment A to pymot json...")
    async for result in db.query(sA):
        jsonA["frames"].append({"timestamp": result["number"],
                                "num": result["number"],
                                "class": "frame",
                                "annotations": []})
    
    sB = q.format(experiment = experimentB)
    #
    # print("converting experiment B to pymot json...")
    async for result in db.query(sB):
        jsonB["frames"].append({"timestamp": result["number"],
                                "num": result["number"],
                                "class": "frame",
                                "hypotheses": []})
                                
    q = """
        SELECT p.particle, f.number, t.location, p.radius
        FROM track t, particle p, frame f
        WHERE t.particle=p.particle
        AND t.frame = f.frame
        AND f.experiment = '{experiment}'
        """
    
    
    sA = q.format(experiment=experimentA)
    
    async for result in db.query(sA):
        r = {"dco": False,
             "height": result["radius"]*2.0,
             "width": result["radius"]*2.0,
             "id": result["particle"],
             "x": result["location"].x,
             "y": result["location"].y
            }
        jsonA["frames"][result["number"]]["annotations"].append(r)

    sB = q.format(experiment=experimentB)
    
    async for result in db.query(sB):
        r = {"dco": False,
             "height": result["radius"]*2.0,
             "width": result["radius"]*2.0,
             "id": result["particle"],
             "x": result["location"].x,
             "y": result["location"].y
            }
        jsonB["frames"][result["number"]]["hypotheses"].append(r)
    
    # print('lA:',len(jsonA["frames"]), 'lB:',len(jsonB["frames"]))
    evaluator = MOTEvaluation(jsonA, jsonB, 5)
    
    evaluator.evaluate()
    evaluator.printResults()
    return evaluator.getMOTA()
    
async def evaluatePymotBySegment(args):
    '''
    A will be considered ground truth
    B will be up for evaluation
    
    feature request:
    - evaluate by segment
    '''
    db = Database()
     
    experimentA = args[0]
    experimentB = args[1]
    
    jsonA = {"frames": [], "class": "video", "filename": experimentA}
    jsonB = {"frames": [], "class": "video", "filename": experimentB}
    
    
    q = """
        SELECT sA.segment as segmentA, sB.segment as segmentB, sA.number as number
        FROM segment sA, segment sB
        WHERE sA.experiment = '{experimentA}'
        AND sB.experiment = '{experimentB}'
        AND sA.number = sB.number
        ORDER BY sA.number ASC
        """
    s = q.format(experimentA = experimentA,
                 experimentB = experimentB)

    async for result in db.query(s):
        segmentA = result["segmenta"]
        segmentB = result["segmentb"]
        segmentNumber = result["number"]
        
        print("Evaluating segment " + str(segmentNumber) + " ...")
        
        q = """
            SELECT frame, number
            FROM frame
            WHERE segment = '{segment}'
            ORDER BY number ASC
            """
        sA = q.format(segment=segmentA)
        
        # print("converting experiment A to pymot json...")
        async for result in db.query(sA):
            jsonA["frames"].append({"timestamp": result["number"],
                                    "num": result["number"],
                                    "class": "frame",
                                    "annotations": []})
        
        sB = q.format(segment=segmentB)
        #
        # print("converting experiment B to pymot json...")
        async for result in db.query(sB):
            jsonB["frames"].append({"timestamp": result["number"],
                                    "num": result["number"],
                                    "class": "frame",
                                    "hypotheses": []})
                                    
        q = """
            SELECT p.particle, f.number, t.location, p.radius
            FROM track t, particle p, frame f
            WHERE t.particle=p.particle
            AND t.frame = f.frame
            AND f.segment = '{segment}'
            """
        
        
        sA = q.format(segment=segmentA)
        
        async for result in db.query(sA):
            r = {"dco": False,
                 "height": result["radius"]*2.0,
                 "width": result["radius"]*2.0,
                 "id": result["particle"],
                 "x": result["location"].x,
                 "y": result["location"].y
                }
            jsonA["frames"][result["number"]]["annotations"].append(r)
    
        sB = q.format(segment=segmentB)
        
        async for result in db.query(sB):
            r = {"dco": False,
                 "height": result["radius"]*2.0,
                 "width": result["radius"]*2.0,
                 "id": result["particle"],
                 "x": result["location"].x,
                 "y": result["location"].y
                }
            jsonB["frames"][result["number"]]["hypotheses"].append(r)
        
        # print('lA:',len(jsonA["frames"]), 'lB:',len(jsonB["frames"]))
        evaluator = MOTEvaluation(jsonA, jsonB, 5)
        
        evaluator.evaluate()
        evaluator.printResults()
    return

async def evaluatePymotBySegment2(args):
    
    logger = None
    
    if True:
        logger = logging.getLogger('pyMotEval')
    
    class SomeDataSource(F):
        def setup(self):
            self.myAsyncFoo = self.myAsync(self.foo)
            self.stop()
            
        async def foo(self):
            '''
            A will be considered ground truth
            B will be up for evaluation
            
            feature request:
            - evaluate by segment
            '''
            db = Database()
            experimentA = args[0]
            experimentB = args[1]
            
            q = """
                SELECT sA.segment as segmentA, sB.segment as segmentB, sA.number as number
                FROM segment sA, segment sB
                WHERE sA.experiment = '{experimentA}'
                AND sB.experiment = '{experimentB}'
                AND sA.number = sB.number
                ORDER BY sA.number ASC
                """
            s = q.format(experimentA = experimentA,
                         experimentB = experimentB)
            
            async for result in db.query(s):
                jsonA = {"frames": [], "class": "video", "filename": experimentA}
                jsonB = {"frames": [], "class": "video", "filename": experimentB}
                minFrameInSegment = None
                
                segmentA = result["segmenta"]
                segmentB = result["segmentb"]
                segmentNumber = result["number"]
                
                # print("Evaluating segment " + str(segmentNumber) + " ...")
                
                q = """
                    SELECT frame, number
                    FROM frame
                    WHERE segment = '{segment}'
                    ORDER BY number ASC
                    """
                sA = q.format(segment=segmentA)
                
                # print("converting experiment A to pymot json...")
                async for result in db.query(sA):
                    if minFrameInSegment is None:
                        minFrameInSegment = result["number"]
                    jsonA["frames"].append({"timestamp": result["number"],
                                            "num": result["number"],
                                            "class": "frame",
                                            "annotations": []})
                
                sB = q.format(segment=segmentB)
                #
                # print("converting experiment B to pymot json...")
                async for result in db.query(sB):
                    jsonB["frames"].append({"timestamp": result["number"],
                                            "num": result["number"],
                                            "class": "frame",
                                            "hypotheses": []})
                                            
                q = """
                    SELECT p.particle, f.number, t.location, p.radius
                    FROM track t, particle p, frame f
                    WHERE t.particle=p.particle
                    AND t.frame = f.frame
                    AND f.segment = '{segment}'
                    """
                
                
                sA = q.format(segment=segmentA)
                
                async for result in db.query(sA):
                    r = {"dco": False,
                         "height": result["radius"]*2.0,
                         "width": result["radius"]*2.0,
                         "id": result["particle"],
                         "x": result["location"].x,
                         "y": result["location"].y
                        }
                    jsonA["frames"][result["number"]-minFrameInSegment]["annotations"].append(r)
            
                sB = q.format(segment=segmentB)
                
                async for result in db.query(sB):
                    r = {"dco": False,
                         "height": result["radius"]*2.0,
                         "width": result["radius"]*2.0,
                         "id": result["particle"],
                         "x": result["location"].x,
                         "y": result["location"].y
                        }
                    jsonB["frames"][result["number"]-minFrameInSegment]["hypotheses"].append(r)
                
                self.put((jsonA, jsonB))
        
    class FirstStageProcessing(F):
        def do(self, i):
            evaluator = MOTEvaluation(i[0], i[1], 5)
            evaluator.evaluate()
            mota = evaluator.getMOTA()
            if logger is not None:
                logger.info("MOTA "+str(mota))
            self.put(mota)

    # Set up a simple data source.
    def Src(n = 5):
        return Iter(range(1, (n+1)))
    
    # Print info for each demo
    def demo(description, ez):
        print("\n")
        print(description)
        # print("\n")
        # ez.printLayout()
        # print(ez.graph())
        #ez.watch(0.1)
        ez.start().join()

    # demo("Sanity.", 
    #     EZ(Src(), Print("Serial"))
    # )
    
    # async for i in SomeDataSource():
    #     print(i)
    
    # demo("Do pymot stuff",
    #     EZ(SomeDataSource(),
    #       FirstStageProcessing(),
    #       Print()
    #     )
    # )

    EZ(SomeDataSource(),
       Seq(As(32, FirstStageProcessing)),
       Print()
    ).start().join()
        
        # # print('lA:',len(jsonA["frames"]), 'lB:',len(jsonB["frames"]))
        # evaluator = MOTEvaluation(jsonA, jsonB, 5)
        
        # evaluator.evaluate()
        # evaluator.printResults()
    return
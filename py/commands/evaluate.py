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

async def main(args):
    
    if len(args) == 0: print("What evaluation would you like to run? [pymot]")
        
    else:
        if args[0] == "pymot":
                await evaluatePymot(args[1:])
        if args[0] == "pymotMethod":
                await evaluateMethod(args[1:])
        else:                         print("Invalid export sub-command")

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
"""
Various utils to retreive from database and export to file
"""


import config
from lib.Database import Database

import os
import shutil
from uuid import UUID
from dateutil.parser import parse as dateparse

from lib.pymot.pymot import MOTEvaluation

async def main(args):
    
    if len(args) == 0: print("What evaluation would you like to run? [pymot]")
        
    else:
        if args[0] == "pymot":
                await evaluatePymot(args[1:])
        else:                         print("Invalid export sub-command")

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
    
    print("converting experiment A to pymot json...")
    async for result in db.query(sA):
        jsonA["frames"].append({"timestamp": result["number"],
                                "num": result["number"],
                                "class": "frame",
                                "annotations": []})
    
    sB = q.format(experiment = experimentB)
    
    print("converting experiment B to pymot json...")
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
    
    print('lA:',len(jsonA["frames"]), 'lB:',len(jsonB["frames"]))
    evaluator = MOTEvaluation(jsonA, jsonB, 5)
    
    evaluator.evaluate()
    evaluator.printResults()
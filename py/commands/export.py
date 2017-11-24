"""
Various utils to retreive from database and export to file
"""


import config
from lib.Database import Database

import os
import shutil
from uuid import UUID
from dateutil.parser import parse as dateparse

async def main(args):
    
    if len(args) == 0: print("What you want to export to? [syncrude|pymot]")
        
    else:
        if args[0] == "syncrude":
            if args[1] == 'all':
                await exportSyncrudeAll(args[2:])
            else:
                await exportSyncrude(args[1:])
        if args[0] == "particles":
            await exportParticles(args[1:])
            
        else:                         print("Invalid export sub-command")


async def exportParticles(args):
    directory = args[0]
    limit = args[1]
    
    db = Database()
    
    q = """
        SELECT e.experiment, f.frame, t.track
        FROM experiment e, frame f, track t, particle p
        WHERE e.experiment = f.experiment
        AND p.particle = t.particle
        AND f.frame = t.frame
        AND e.name = 'T02601'
        AND p.area > 100
        AND p.category in (2,3)
        ORDER BY RANDOM()
        LIMIT {limit}
        """
    s = q.format(limit=limit)
    crops = []
    
    async for result in db.query(s):
        srcFile = os.path.join(config.experiment_dir, 
                               str(result["experiment"]),
                               str(result["frame"]),
                               str(result["track"])+'.jpg')
        dstFile = os.path.join(directory,
                               str(result['track'])+".jpg")
                               
        shutil.copyfile(srcFile, dstFile)

async def exportSyncrudeAll(args):
    """
    dir [prefix]
    """
    pass

async def exportSyncrude(args):
    """
    experiment dir [prefix]
    """
    experiment_uuid = args[0]
    directory = args[1]
    if len(args) == 3:
        prefix = args[2]
    else:
        prefix = ''
    
    db = Database()
    
    q = """
        SELECT *
        FROM experiment
        WHERE experiment = $1
        """
    day, name, method = None, None, None
    async for record in db.query(q, UUID(experiment_uuid)):
        day = str(record["day"])
        name = record["name"].strip()
        method = record["method"].strip()
    
    dayDirectory = os.path.join(directory, day)
    file = name+"_"+method+".txt"
    
    if not os.path.exists(dayDirectory):
        print("created new day directory", dayDirectory)
        os.mkdir(dayDirectory)
    
    categoryMap = await db.category_map()
    outfile = os.path.join(dayDirectory, file)
    with open(outfile, 'w+') as f:
    
        q = """
            SELECT f2.number as fnum, 
                   t2.particle as pid, 
                   p.area as area, 
                   p.intensity as intensity, 
                   t2.location-t1.location as delta, 
                   p.category as category
            FROM frame f1, frame f2, track t1, track t2, particle p
            WHERE f1.number = f2.number-1
            AND f1.frame = t1.frame
            AND f2.frame = t2.frame
            AND t1.particle = t2.particle
            AND t2.particle = p.particle
            AND f1.experiment = $1
            ORDER BY t2.particle, f1.number
            """
        async for r in db.query(q, UUID(experiment_uuid)):
            categoryName = categoryMap[r["category"]]
            dx = r["delta"].x
            dy = -r["delta"].y
            l = [r["fnum"], r["pid"], r["area"], r["intensity"], dx, dy, categoryName]
            sl = [str(i) for i in l]
            f.write("{}\n".format(", ".join(sl)))

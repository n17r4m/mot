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
    
    if len(args) == 0: print("What you want to export to? [syncrude|pymot|particlesVelocitiesLatents]")
        
    else:
        if args[0] == "syncrude":
            if args[1] == 'all':
                await exportSyncrudeAll(args[2:])
            else:
                await exportSyncrude(args[1:])
        if args[0] == "particles":
            await exportParticles(args[1:])
        if args[0] == "particlesVelocitiesLatents":
            await exportParticlesVelocitiesLatents(args[1:])            
        if args[0] == "Syncrude2018":
            await exportSyncrude2018(*args[1:])
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
        AND e.experiment = 'b6734bad-2dfc-4502-9260-a7d71e72f6a9'
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
        
async def exportParticlesVelocitiesLatents(args):
    directory = args[0]
    limit = args[1]
    
    db = Database()
    
    q = """
        SELECT e.experiment, f1.frame, t1.track, t1.latent, t2.location-t1.location as delta
        FROM experiment e, frame f1, frame f2, track t1, track t2, particle p
        WHERE e.experiment = f1.experiment
        AND e.experiment = f2.experiment
        AND p.particle = t1.particle
        AND f1.frame = t1.frame
        AND f2.frame = t2.frame
        AND t1.particle = t2.particle
        AND f1.number = f2.number-1
        AND e.experiment = '3a24cfcf-bef5-40a1-a477-6e7007bcd7ae'
        AND p.area > 100
        AND f1.number > 200
        AND f1.number < 500
        AND p.category in (2,3)
        ORDER BY RANDOM()
        LIMIT {limit}
        """
    s = q.format(limit=limit)
    crops = []
    
    line = "{track}, {dx}, {dy}, {latent}\n"
    outFile = os.path.join(directory, "data.txt")
    with open(outFile, 'w+') as f:
        async for result in db.query(s):
            srcFile = os.path.join(config.experiment_dir, 
                                   str(result["experiment"]),
                                   str(result["frame"]),
                                   str(result["track"])+'.jpg')
            dstFile = os.path.join(directory,
                                   str(result['track'])+".jpg")
                                   
            shutil.copyfile(srcFile, dstFile)
            dx = result["delta"][0]
            dy = result["delta"][1]
            f.write(line.format(track=result["track"],
                                dx=dx,
                                dy=dy,
                                latent=result["latent"]))
            
        
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

async def exportSyncrude2018(experiment_uuid, directory):
    """
    experiment outputDir
    
    Requested
    CSV Headers: Frame ID, Particle ID, Particle Area, Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
    
    Actual 
    Modified:
    CSV Headers: SegmentNum, FrameNum, Particle ID, Particle Area, Mean Particle Velocity, Particle Intensity, Particle Perimeter, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
    """

    # print("Currently Exporting valid particles only...")
        
    
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
    
    
    file = name+"_"+method+".txt"
    
    if not os.path.exists(directory):
        print("created new day directory", directory)
        os.mkdir(directory)
    
    categoryMap = await db.category_map()
    
    s = """
        SELECT f2.number as fnum,
               f2.frame as fid,
               p.particle as pid, 
               p.area as area,
               p.intensity as intensity, 
               p.perimeter as perimeter,
               t2.location[1]-t1.location[1] as delta_y,
               t2.location[0] as xpos,
               t2.location[1] as ypos,
               p.major as major,
               p.minor as minor,
               p.orientation as ori,
               p.solidity as solid,
               p.eccentricity as ecc
        FROM frame f1, frame f2, track t1, track t2, particle p, segment s
        WHERE f1.number = f2.number-1
        AND f1.frame = t1.frame
        AND f2.frame = t2.frame
        AND t1.particle = t2.particle
        AND t2.particle = p.particle
        AND s.segment = f1.segment
        AND f1.experiment = '{experiment}'
        """
    q = s.format(experiment=experiment_uuid)
    # CSV Headers: Frame ID, Particle ID, Particle Area, Particle Velocity, Particle Intensity, Particle Perimeter, X Position, Y Position, Major Axis Length, Minor Axis Length, Orientation, Solidity, Eccentricity.
    
    l = "{fid},{pid},{area},{vel},{inten},{per},{xPos},{yPos},{major},{minor},{ori},{solid},{ecc}\n"
    
    # Continue from here...
    
    outfile = os.path.join(directory, file)
    with open(outfile, 'w+') as f:
        async for r in db.query(q):
            
            s = l.format(fid = r["fid"],
                         pid = r["pid"],
                         area = r["area"],
                         vel = r["delta_y"],
                         inten = r["intensity"],
                         per = r["perimeter"],
                         xPos = r["xpos"],
                         yPos = r["ypos"],
                         major = r["major"],
                         minor = r["minor"],
                         ori = r["ori"],
                         solid = r["solid"],
                         ecc = r["ecc"])
                     
            f.write(s)

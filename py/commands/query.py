

from lib.Database import Database

from uuid import UUID

from plotly import tools, utils
from lib.plots.violin2 import violin2


import plotly.offline as py
import plotly.figure_factory as ff
import plotly.graph_objs as go
import json
import numpy as np
import pandas as pd

db = Database()

async def main(args):
    
    if len(args) == 0:   return "Invalid query"
    else:                return await run_query(*args)



async def run_query(query, *args):
    return to_json(await getattr(Queries, query)(*args))




def to_json(data):
    return json.dumps(data)


class Queries:
    
    async def particles_by_category_with_flow_near(experiment, flow, category = None, limit = 10):
        
        if category is None:
            q = ("""
                SELECT t2.particle AS particle, MAX(t2.frame::text) AS frame, AVG(-(t2.location <-> t1.location) * p.area - $1) as dflow
                FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
                WHERE p.particle = t1.particle AND t1.particle = t2.particle 
                AND t1.frame = f1.frame AND t2.frame = f2.frame
                AND f1.number = f2.number - 1 
                AND p.experiment = $2
                GROUP BY t2.particle 
                ORDER BY dflow ASC LIMIT $3
                """, float(flow), UUID(experiment), int(limit))
        else:
            q = ("""
                SELECT t2.particle AS particle, MAX(t2.frame::text) AS frame, AVG(-(t2.location <-> t1.location) * p.area - $1) as dflow
                FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
                WHERE p.particle = t1.particle AND t1.particle = t2.particle 
                AND t1.frame = f1.frame AND t2.frame = f2.frame
                AND f1.number = f2.number - 1 
                AND p.experiment = $2
                AND p.category = $4
                GROUP BY t2.particle 
                ORDER BY dflow ASC LIMIT $3
                """, float(flow), UUID(experiment), int(limit), int(category))
            
        return [[str(row["frame"]), str(row["particle"])] async for row in db.query(*q)]
        


    
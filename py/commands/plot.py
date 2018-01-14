

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
    else:                return await plot_query(*args)


async def plot_query(query, *args):
    return to_json(await getattr(Plots, query)(*args))
    

def to_json(figure):
    return json.dumps({
        "data": figure.get('data', []),
        "layout": figure.get('layout', {})}, cls=utils.PlotlyJSONEncoder)


class Plots:
    
    async def flow_vs_category_histogram(experiment):
        
        labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        data = []
        for category in range(5):
            data.append(
                go.Histogram(name=labels[category], opacity=0.66, x=[
                row["flow"] async for row in db.query("""
                SELECT AVG(-(t2.location[1] - t1.location[1]) * p.area) as flow
                FROM Track t1, Track t2, Frame f1, Frame f2, Particle p
                WHERE category = $1
                AND p.particle = t1.particle AND t1.particle = t2.particle
                AND t1.frame = f1.frame AND t2.frame = f2.frame
                AND f1.number = f2.number - 1 
                AND p.experiment = $2
                GROUP BY p.particle
                """, category, UUID(experiment))]))
        
        layout = go.Layout(barmode='overlay')
        return go.Figure(data=data, layout=layout)


    
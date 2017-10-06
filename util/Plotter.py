#! /usr/bin/env python
"""
Generate html plots for a given query

USING:

    As a command line utility:
    
        $ Plotter.py query input_bag [input_bag ...]
    
    As a module:
    
        from Plotter import Plotter
        TODO
        

Author: Martin Humphreys
"""

from argparse import ArgumentParser
from Query import Query
from DataBag import DataBag
from requests.compat import json
from plotly import tools, utils
from plots.violin2 import violin2


import plotly.offline as py
import plotly.figure_factory as ff
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import os
# import cv2




class Plotter:

    def __init__(self, bags):
        self.qs = []
        for bag in bags:
            self.qs.append(Query(bag))
    
    def to_json(self, figure):
        
        return json.dumps({
            "data": figure.get('data', []),
            "layout": figure.get('layout', {})}, cls=utils.PlotlyJSONEncoder)
        
        
    
    def flow_vs_intensity_histogram(self, threshold=110):
        labels = ["Dark", "Light"]
        data = self.qs[0].flow_vs_intensity_histogram(threshold)
        trace1 = go.Histogram(x=data[0], name=labels[0], opacity=0.75)
        trace2 = go.Histogram(x=data[1], name=labels[1], opacity=0.75)
        data = [trace1, trace2]
        layout = go.Layout(barmode='overlay')
        fig = go.Figure(data=data, layout=layout)
        return self.to_json(fig)
    
    def flow_vs_intensity_distribution(self, threshold=110):
        labels = ["Dark", "Light"]
        data = self.qs[0].flow_vs_intensity_distribution(threshold)
        fig = ff.create_distplot(data, labels, bin_size=50, show_rug=False)
        return self.to_json(fig)
    
    def flow_vs_intensity_violin(self, threshold=110):
        data = self.qs[0].flow_vs_intensity_violin(threshold)
        labels = (["Dark"] * len(data[0])) + (["Light"] * len(data[1]))
        df = pd.DataFrame(dict(Flow = data[0]+data[1], Type = labels))
        fig = ff.create_violin(df, data_header="Flow", group_header="Type", title=None, rugplot=False)
        return self.to_json(fig)


    def flow_vs_category_histogram(self):
        labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        data = self.qs[0].flow_vs_category_histogram()
        
        trace1 = go.Histogram(x=data[0], name=labels[0], opacity=0.66)
        trace2 = go.Histogram(x=data[1], name=labels[1], opacity=0.66)
        trace3 = go.Histogram(x=data[2], name=labels[2], opacity=0.66)
        trace4 = go.Histogram(x=data[3], name=labels[3], opacity=0.66)
        trace5 = go.Histogram(x=data[4], name=labels[4], opacity=0.66)
        
        data = [trace1, trace2, trace3, trace4, trace5]
        layout = go.Layout(barmode='overlay')
        fig = go.Figure(data=data, layout=layout)
        return self.to_json(fig)
    
    def flow_vs_category_distribution(self):
        labels = ["Undefined", "Unknown", "Bitumen", "Sand", "Bubble"]
        data = self.qs[0].flow_vs_category_distribution()
        #data = map(lambda d: [-1, 0, 1] if len(d) == 0 else d, data)
        #TODO 
        fig = ff.create_distplot(data, labels, bin_size=50, show_rug=False)
        return self.to_json(fig)
    
    def flow_vs_category_violin(self):
        data = self.qs[0].flow_vs_category_violin()
        labels = (["Undefined"] * len(data[0])) + (["Unknown"] * len(data[1])) + (["Bitumen"] * len(data[2])) + (["Sand"] * len(data[3])) + (["Bubble"] * len(data[4]))
        df = pd.DataFrame(dict(Flow = data[0]+data[1]+data[2]+data[3]+data[4], Category = labels))
        fig = ff.create_violin(df, data_header="Flow", group_header="Category", title=None, rugplot=False)
        return self.to_json(fig)

        
    def compare_flow_vs_category_violin2(self):
        data = [q.compare_flow_vs_category_violin2() for q in self.qs]
        labels = [q.bag.name.split("/")[-1].split("_")[0] for q in self.qs]
        fig = violin2(data, labels)
        return self.to_json(fig)
  
  
  
def build_parser():
    parser = ArgumentParser()
    parser.add_argument('query', help='stored procedure to run')
    parser.add_argument('input_bags', help='bags to execute query on', nargs="+")
    return parser


def main():
    parser = build_parser()
    opts = parser.parse_args()
    for bagfile in opts.input_bags:
        if not os.path.isfile(bagfile):
            parser.error("DataBag file %s does not exist." % bagfile)
    
    plotr = Plotter(opts.input_bags)
    
    print(getattr(plotr, opts.query)())
    

if __name__ == '__main__':
    main()

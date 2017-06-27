#! /usr/bin/env python
"""
Convert a DataBag's tracking information into the required format for
the pymot evaluation utility.

When used as a command line utility, saves the bag information to a
JSON file in the required format.

When used as a module, returns an JSON formatted array.

USING:

    As a command line utility:
    
        $ Bag2PymotJson.py dataBag output_json type
    
    As a module:
    
        import Bag2PymotJson
        json_tracking_data = Bag2PymotJson("dataBag.db", ground_truth=False)
            # or 
        converter = Bag2PymotJson(dataBag, ground_truth=False)
        json_tracking_data = converter.convert()


Author: Kevin Gordon
"""
from argparse import ArgumentParser
import os
from DataBag import DataBag
from pymot.pymot import MOTEvaluation
import numpy as np
import json

class Bag2PymotJson(object):
    def __init__(self, dataBag, ground_truth=False):
        if isinstance(dataBag, str):
            self.bag = DataBag(dataBag)
        else:
            self.bag = dataBag

        if ground_truth:
            self.type = 'annotations'
        else:
            self.type = 'hypotheses'

        self.JSON = [{"frames":[], "class":"video", "filename": str(self.bag)}]

    def convert(self):
        frames = self.bag.query('SELECT DISTINCT frame FROM frames ORDER BY frame')
        frames = [i[0] for i in frames]
        tracks = self.bag.query('SELECT particle, frame, x, y, area FROM assoc, particles WHERE particles.id == assoc.particle ORDER BY PARTICLE')

        for frame in frames:
            self.JSON[0]["frames"].append({"timestamp":frame, "num": frame, "class":"frame", self.type:[]})

        for assoc in tracks:
            # Could be improved by storing width and height in the database
            diameter = 2.0 * np.sqrt(assoc[4] / np.pi)
            frame = assoc[1]
            pid = assoc[0]
            x = assoc[2]
            y = assoc[3]

            self.JSON[0]['frames'][frame][self.type].append({"dco": False,
                                                                      "height": diameter,
                                                                      "width": diameter,
                                                                      "id": pid,
                                                                      "y": y,
                                                                      "x": x})
        return self.JSON

    def save(self, outfile):
        with open(outfile, 'w') as f:
            json.dump(self.JSON, f)

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('DataBag', help='The databag with tracking information to convert to JSON')
    parser.add_argument('output_json', help='file to save json data to')
    parser.add_argument('-g', help='Is this a ground truth DataBag?', action = 'store_true')

    return parser

def main():
    parser = build_parser()
    options = parser.parse_args()
    if not os.path.isfile(options.DataBag):
        parser.error("Database file %s does not exist." % options.DataBag)
    

    converter = Bag2PymotJson(options.DataBag, options.g)
    _ = converter.convert()
    converter.save(options.output_json)

if __name__ == '__main__':
    main()

#! /usr/bin/env python
"""
Common Queries to execute on a DataBag
======================================

A collection of ueful helpers to interrogate the data in a DataBag.

:Example:

As a command line utility:

$ Query.py file.db the_stored_query_name

As a module:

>>> import Query
>>> q = Query("file.db") # or #  q = Query(bag)
>>> particles = q.particles_in_frame(24)



CHANGELOG
---------

v17.6.26 Moved queries not relating to DB management from DataBag to here.

        
:Author: 
Martin Humphreys
"""

from argparse import ArgumentParser
import numpy as np
import sys
import os
import sqlite3
import json
from DataBag import DataBag


class dotdict(dict):
  """dot.notation access to dictionary attributes"""
  # https://stackoverflow.com/a/23689767
  __getattr__ = dict.get
  __setattr__ = dict.__setitem__
  __delattr__ = dict.__delitem__

class Query(object):
    """A collection of useful queries which can be run on databags"""
    
    def __init__(self, bag, verbose = False):
        """
        :param bag: A databag (object) or a databag filepath (string)
        :param verbose: Print useful debugging information to console.
        """
        self.bag = DataBag.fromArg(bag)
        self.verbose = verbose
    
    def say(self, *args):
        """
        Helper to mute output when not verbose
        
        :param *args: if verbose: print(args)
        """
        if self.verbose:
            print(args)
    

    def cursor(self):
        """
        For doing some raw SQL
        :return: a cursor to the bag database
        """
        return self.bag.cursor()
    
    def commit(self):
        """
        For commiting some raw SQL
        """
        return self.bag.commit()
    
    
    def query(self, query):
        """
        Convenience function that executes a prepared sql statement.
        If you want to escape data into a query, you're probably better off
        using a cursor. 
        
        >>> c = q.cursor()
        >>> c.execute("SELECT * FROM particles WHERE particle = ?", (27,))
        >>> res = c.fetchall()
        
        :param query: the string query you want to execute.
        :return: results of the query
        """
        c = self.cursor()
        c.execute(query)
        res = c.fetchall()
        return res
    
    
    def queryJSON(self, query):
        # Same as self.query but returns a JSON formatting string.
        return json.dumps(self.query(query))
    
    def fieldmap(self, fields, rows):
        results = []
        fields = self.fieldsplit(fields)
        for row in rows:
            r = dotdict()
            for idx, name in enumerate(fields):
                r[name] = row[idx]
            results.append(r)
        return results
        
    def fieldsplit(self, fields):
        return fields.split(", ")
    
    def frame_list(self):
        c = self.cursor()
        c.execute("SELECT frame FROM frames ORDER BY frame")
        return c.fetchall()
    
    def particles_in_frame(self, frame, category = None):
        c = self.cursor()
        fields = "id, area, intensity, category, x, y, radius"
        if category is None:
            c.execute("SELECT " + fields + " FROM LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ?", (frame,))
        else:    
            c.execute("SELECT " + fields + " FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ? and category = ?", (frame, category))
        return self.fieldmap(fields, c.fetchall())
    
    def particle_points(self, particle):
        c = self.cursor()
        c.execute("SELECT x, y FROM assoc WHERE particle = ?", (particle,))
        return c.fetchall()
    
    def particle_velocities(self, particle):
        points = self.particle_points(particle)
        return points[1:] - points[:-1] 
    
    def particle_mean_velocity(self, particle):
        return np.mean(self.particle_velocities(particle), axis=0)
    
    def frameMeanVelocity(self, frame):
        particles = self.particles_in_frame(frame)
        num = float(particles.shape[0])
        mean = 0.0
        for p in particles:
            mean += (1.0/num) * self.particleMeanVelocity(p[0])
        return mean


    def compare(self, db_file):
        
        c = self.cursor()
        c.executescript("attach '{}' as d2;".format(db_file))
        
        c.execute("""
            select a1.frame, count(*) / 2, sum(sqrt(power(a1.x - a2.x, 2) + power(a1.y - a2.y, 2))) / count(*)
            from 
                (select * from assoc left join particles on assoc.particle = particles.id) as a1, 
                (select * from d2.assoc left join d2.particles on d2.assoc.particle = d2.particles.id) as a2
            where a1.frame = a2.frame
            and abs(a1.x - a2.x) < sqrt(a1.area)
            and abs(a1.y - a2.y) < sqrt(a2.area)
            and abs(a1.intensity - a2.intensity) < 35
            group by a1.frame
        """)
        return c.fetchall()
        
    
    def getBitmap(self, frame_no):
        res = self.query("SELECT bitmap FROM frames WHERE frame == " + str(frame_no))
        return self.bag.fromPng(res[0][0])

    

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('dbfile', help='database to operate on', default=":memory:")
    parser.add_argument('query', help='query to run', default="")
    parser.add_argument('args', help='positional argument(s) for query', nargs='*')
    parser.add_argument('-v', help='print verbose statements while executing', action='store_true')
    return parser


if __name__ == '__main__':
    parser = build_parser()
    options = parser.parse_args()

    q = Query(options.dbfile, options.v)
    
    print(json.dumps(getattr(q, options.query)(*options.args)))
    
    
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
        fields = "frame, particles"
        c.execute("SELECT frame, count(particle) as particles FROM assoc GROUP BY frame")
        return self.fieldmap(fields, c.fetchall())
    
    def particle_list(self):
        c = self.cursor()
        fields = "id, area, intensity, perimeter, radius, category"
        c.execute("SELECT " + fields + " FROM particles")
        return self.fieldmap(fields, c.fetchall())
    
    def particle_properties(self, frame, particle):
        c = self.cursor()
        fields = "id, area, intensity, category, x, y, radius, frame"
        c.execute("SELECT " + fields + " FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ? and particles.id = ?", (frame, particle))
        rows = c.fetchall()
        
        if len(rows) > 0:
            return self.fieldmap(fields, rows)[0]
        else:
            return None
    
    def particles_in_frame(self, frame, category = None):
        c = self.cursor()
        fields = "id, area, intensity, category, x, y, radius, frame"
        if category is None:
            c.execute("SELECT " + fields + " FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ?", (frame,))
        else:    
            c.execute("SELECT " + fields + " FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ? and category = ?", (frame, category))
        return self.fieldmap(fields, c.fetchall())
    
    
    def particle_instances(self, particle):
        c = self.cursor()
        fields = "id, area, intensity, category, x, y, radius, frame"
        c.execute("SELECT " + fields + " FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE particles.id = ?", (particle,))
        return self.fieldmap(fields, c.fetchall())
    
    def particle_points(self, particle):
        c = self.cursor()
        fields = "x, y"
        c.execute("SELECT " + fields + " FROM assoc WHERE particle = ?", (particle,))
        return self.fieldmap(fields, c.fetchall())
    
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


    def flow_vs_intensity_histogram(self, threshold = 110):
        buf1 = self.bag.query('select -(a2.y-a1.y)*p.area from assoc a1, assoc a2, particles p where intensity < '+str(threshold)+' and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1')
        buf2 = self.bag.query('select -(a2.y-a1.y)*p.area from assoc a1, assoc a2, particles p where intensity >= '+str(threshold)+' and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1')
        
        buf1 = np.array([i[0] for i in buf1])
        buf2 = np.array([i[0] for i in buf2])

        """
        q75, q25 = np.percentile(buf1, [75 ,25])                         
        iqr = q75 - q25
        lb = q25 - 3.0 * iqr
        ub = q75 + 3.0 * iqr
        buf1 = buf1[(buf1<ub) & (buf1>lb)]
        
        q75, q25 = np.percentile(buf2, [75 ,25])                         
        iqr = q75 - q25
        lb = q25 - 3.0 * iqr
        ub = q75 + 3.0 * iqr
        buf2 = buf2[(buf2<ub) & (buf2>lb)]
        """
        
        return [buf1.tolist(), buf2.tolist()]
    
    def flow_vs_intensity_distribution(self, threshold = 110):
        return self.flow_vs_intensity_histogram(threshold)
    
    def flow_vs_intensity_violin(self, threshold = 110):
        return self.flow_vs_intensity_histogram(threshold)


    def flow_vs_category_histogram(self):
        cat0 = self.bag.query('select AVG(-(a2.y-a1.y)*p.area) from assoc a1, assoc a2, particles p where category = 0 and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1 GROUP BY p.id')
        cat1 = self.bag.query('select AVG(-(a2.y-a1.y)*p.area) from assoc a1, assoc a2, particles p where category = 1 and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1 GROUP BY p.id')
        cat2 = self.bag.query('select AVG(-(a2.y-a1.y)*p.area) from assoc a1, assoc a2, particles p where category = 2 and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1 GROUP BY p.id')
        cat3 = self.bag.query('select AVG(-(a2.y-a1.y)*p.area) from assoc a1, assoc a2, particles p where category = 3 and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1 GROUP BY p.id')
        cat4 = self.bag.query('select AVG(-(a2.y-a1.y)*p.area) from assoc a1, assoc a2, particles p where category = 4 and p.id==a1.particle and a1.particle==a2.particle and a1.frame == a2.frame - 1 GROUP BY p.id')
        
        cat0 = np.array([i[0] for i in cat0])
        cat1 = np.array([i[0] for i in cat1])
        cat2 = np.array([i[0] for i in cat2])
        cat3 = np.array([i[0] for i in cat3])
        cat4 = np.array([i[0] for i in cat4])
        """
        if len(cat0):
            q75, q25 = np.percentile(cat0, [75 ,25])                         
            iqr = q75 - q25
            lb = q25 - 3.0 * iqr
            ub = q75 + 3.0 * iqr
            cat0 = cat0[(cat0<ub) & (cat0>lb)]
        
        if len(cat1):
            q75, q25 = np.percentile(cat1, [75 ,25])                         
            iqr = q75 - q25
            lb = q25 - 3.0 * iqr
            ub = q75 + 3.0 * iqr
            cat1 = cat1[(cat1<ub) & (cat1>lb)]
        
        if len(cat2):
            q75, q25 = np.percentile(cat2, [75 ,25])                         
            iqr = q75 - q25
            lb = q25 - 3.0 * iqr
            ub = q75 + 3.0 * iqr
            cat2 = cat2[(cat2<ub) & (cat2>lb)]
        
        if len(cat3):
            q75, q25 = np.percentile(cat3, [75 ,25])                         
            iqr = q75 - q25
            lb = q25 - 3.0 * iqr
            ub = q75 + 3.0 * iqr
            cat3 = cat3[(cat3<ub) & (cat3>lb)]
        
        if len(cat4):
            q75, q25 = np.percentile(cat4, [75 ,25])                         
            iqr = q75 - q25
            lb = q25 - 3.0 * iqr
            ub = q75 + 3.0 * iqr
            cat4 = cat4[(cat4<ub) & (cat4>lb)]
        """
        return [cat0.tolist(), cat1.tolist(), cat2.tolist(), cat3.tolist(), cat4.tolist()]
    
    def flow_vs_category_distribution(self):
        return self.flow_vs_category_histogram()
    
    def flow_vs_category_violin(self):
        return self.flow_vs_category_histogram()


    def particles_by_category_with_flow_near(self, flow, category = None, limit = 10):
        c = self.cursor()
        fields = "id, dv"
        if category is None:
            c.execute("SELECT a2.particle AS id, AVG(ABS(-(a2.y-a1.y)*p.area - ?)) AS dv FROM assoc a1, assoc a2, particles p WHERE p.id==a1.particle AND a1.particle==a2.particle AND a1.frame == a2.frame - 1 GROUP BY id ORDER BY dv ASC LIMIT ?", (flow, limit))
        else:
            c.execute("SELECT a2.particle AS id, AVG(ABS(-(a2.y-a1.y)*p.area - ?)) AS dv FROM assoc a1, assoc a2, particles p WHERE category = ? AND p.id==a1.particle AND a1.particle==a2.particle AND a1.frame == a2.frame - 1 GROUP BY id ORDER BY dv ASC LIMIT ?", (flow, category, limit))
        return self.fieldmap(fields, c.fetchall())
    
    
    def particles_by_intensity_with_flow_near(self, flow, take="Light", intensity = 110, limit = 10):
        c = self.cursor()
        fields = "id, dv"
        op = ">=" if take =="Light" else "<"
        c.execute("SELECT a2.particle AS id, AVG(ABS(-(a2.y-a1.y)*p.area - ?)) AS dv FROM assoc a1, assoc a2, particles p WHERE p.id==a1.particle AND a1.particle==a2.particle AND a1.frame == a2.frame - 1 AND intensity " + op + " ? GROUP BY id ORDER BY dv ASC LIMIT ?", (flow, intensity, limit))
        return self.fieldmap(fields, c.fetchall())
    
        
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
    
    
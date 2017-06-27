#! /usr/bin/env python
"""
Storage for tracking information
USING:

    As a command line utility:
    
        $ DataBag.py file.db QUERY
    
    As a module:
    
        import DataBag
        bag = DataBag("file.db")

Author: Martin Humphreys
"""

from argparse import ArgumentParser
import numpy as np
import os
import re
import sys
import sqlite3
import json
import png
import StringIO
import readline
import itertools
import time


class DataBag(object):
    
    def __init__(self, db_file = ":memory:", verbose = False):
        self.verbose = verbose
        self.name = db_file
        self.db = sqlite3.connect(db_file, isolation_level="DEFERRED")
        self.db.enable_load_extension(True)
        self.db.load_extension(os.path.dirname(os.path.realpath(__file__)) + "/libsqlitefunctions.so")
        
        # alternatively you can load the extension using an API call:
        # con.load_extension("./fts3.so")
        self.say("Connected to database", db_file)
        self.initTables()
    
    def __repr__(self):
        return self.name.split('/')[-1]

    def say(self, *args):
        if self.verbose:
            print(args)
    
    def repl(self):
        while True:
            cmd = raw_input("sql> ")
            try:
                c = self.db.cursor()
                c.execute(cmd.strip())
                if cmd.lstrip().upper().startswith("SELECT"):
                    print c.fetchall()
                self.db.commit()
            except sqlite3.Error, e:
               print "An error occurred:", e.args[0]

    def query(self, query):
        c = self.db.cursor()
        c.execute(query)
        res = c.fetchall()
        return res

    def queryJSON(self, query):
        return json.dumps(self.query(query))
    
    def initTables(self):
        if not self.tableExists("frames"): self.createFramesTable()
        if not self.tableExists("assoc"): self.createAssocTable()
        if not self.tableExists("particles"): self.createParticlesTable()
        self.db.commit()
    
    def tableExists(self, table):
        c = self.db.cursor()
        c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table,));
        return c.fetchone()[0] is 1
    
    def createFramesTable(self):
        self.db.cursor().execute("CREATE TABLE frames (frame INTEGER, bitmap BLOB)");
    
    def createAssocTable(self):
        self.db.cursor().execute("CREATE TABLE assoc (frame INTEGER, particle INTEGER, x REAL, y REAL)");
    
    def createParticlesTable(self):
        self.db.cursor().execute("CREATE TABLE particles (id INTEGER PRIMARY KEY, area INTEGER, intensity INTEGER, perimeter INTEGER)");
    
    def batchInsertFrame(self, number, bitmap = None):
        c = self.db.cursor()
        c.execute("SELECT frame FROM frames WHERE frame = ?", (number,))
        if len(c.fetchall()) == 0:
            if bitmap is None:
                c.execute("INSERT INTO frames (frame) VALUES (?)", (number,))
            else:
                c.execute("INSERT INTO frames (frame, bitmap) VALUES (?, ?)", (number, self.toPng(bitmap)))

    def insertFrame(self, number, bitmap = None):
        self.batchInsertFrame(number, bitmap)
        self.db.commit()
    
    def batchInsertParticle(self, area = 1, intensity = 0, perimeter = 0, id = None):
        c = self.db.cursor()
        if id is None:
            c.execute("INSERT INTO particles (area, intensity, perimeter) VALUES (?, ?, ?)", (area, intensity, perimeter))
        else:
            c.execute("INSERT INTO particles (id, area, intensity, perimeter) VALUES (?, ?, ?, ?)", (id, area, intensity, perimeter))
        return c.lastrowid

    def insertParticle(self, area = 1, intensity = 0, perimeter = 0, id = None):
        lastrowid = self.batchInsertParticle(area, intensity, perimeter, id)
        self.db.commit()
        return lastrowid
    
    def batchInsertAssoc(self, frame, particle, x, y):
        c = self.db.cursor()
        c.execute("INSERT INTO assoc (frame, particle, x, y) VALUES (?, ?, ?, ?)", (frame, particle, x, y))

    def insertAssoc(self, frame, particle, x, y):
        self.batchInsertAssoc(frame, particle, x, y)
        self.db.commit()

    def batchCommit(self):
        pass
        self.db.commit()
    
    def insertTrace(self, frame, area, intensity, points):
        samples = points.shape[0]
        if samples > 0:
            pId = self.insertParticle(area, intensity)
            for pair in points:
                self.insertFrame(frame)
                self.insertAssoc(frame, pId, pair[0], pair[1])
                frame += 1
        self.db.commit()
    
    def particlesInFrame(self, frame):
        c = self.db.cursor()
        c.execute("SELECT id, area, intensity, x, y FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ?", (frame,))
        return np.array(c.fetchall())
    
    def particlePoints(self, particle):
        c = self.db.cursor()
        c.execute("SELECT x, y FROM assoc WHERE particle = ?", (particle,))
        return np.array(c.fetchall())
    
    def particleVelocities(self, particle):
        points = self.particlePoints(particle)
        return points[1:] - points[:-1] 
    
    def particleMeanVelocity(self, particle):
        return np.mean(self.particleVelocities(particle), axis=0)
    
    def frameMeanVelocity(self, frame):
        particles = self.particlesInFrame(frame)
        num = float(particles.shape[0])
        mean = 0.0
        for p in particles:
            mean += (1.0/num) * self.particleMeanVelocity(p[0])
        return mean


    def compare(self, db_file):
        
        c = self.db.cursor()
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
        return np.array(c.fetchall())
        
        stats = []
        return stats

    
    def toPng(self, bitmap):
        data = png.from_array(bitmap, mode='L;1').save('tmp.png')
        data = open('tmp.png').read()
        data = buffer(data)
        return data

    
    def fromPng(self, data):
        im = png.Reader(bytes=data).asDirect()
        return np.vstack(itertools.imap(np.uint8, im[2]))

    
    def getBitmap(self, frame_no):
        res = self.query("SELECT bitmap FROM frames WHERE frame == " + str(frame_no))
        return self.fromPng(res[0][0])

    def li_import(self, file_name):
        with open(file_name) as file:
            l = 0
            for line in file:
                l += 1
                line = re.sub(' +',' ', re.sub('\t',' ',line)).strip() # remove ws
                line = np.array(line.split(" "), dtype=np.float64)
                (frame, area, intensity) = (line[0], line[1], line[2])
                points = line[3:]
                samples = points.shape[0]
                if samples % 2 == 1:
                    raise ValueError("There must be equal number of x,y samples. Line " + l)
                points = points.reshape(2, samples/2).T
                self.insertTrace(frame, area, intensity, points)


def build_parser():
    parser = ArgumentParser()
    parser.add_argument('dbfile', help='database to operate on', default=":memory:")
    parser.add_argument('action', help='command to execute', default="")
    parser.add_argument('query', nargs='?', help='options for command', default="")
    parser.add_argument('-v', help='print verbose statements while executing', action='store_true')
    return parser


if __name__ == '__main__':
    parser = build_parser()
    options = parser.parse_args()
    if options.dbfile != ":memory:" and not os.path.isfile(options.dbfile):
        if options.v:
            print "Notice: database file", options.dbfile, "does not exist. Creating."
    bag = DataBag(options.dbfile, options.v)
    
    if options.action == "query" or options.action == "repl":
        bag.repl()
    
    if options.action == "compare":
        if not os.path.isfile(options.query):
            parser.error("Comparision file %s does not exist." % options.query)
        else:
            stats = bag.compare(options.query)
            print stats
        
        
    if options.action == "import":
        if not os.path.isfile(options.query):
            parser.error("Import file %s does not exist." % options.query)
        else:
            bag.li_import(options.query)
            
    if options.action == "debug":
        print bag.particlePoints(1)
        print bag.particleMeanVelocity(1)
        print bag.frameMeanVelocity(41)
        print bag.frameMeanVelocity(42)
        print bag.frameMeanVelocity(43)
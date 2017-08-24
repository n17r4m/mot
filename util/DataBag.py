#! /usr/bin/env python
"""
Storage for detection and tracking information.

CHANGELOG:
    
    v17.6.26  Reworked the database migration system
              Moved out common queries to Query.py
    v17.6.8   Added particle categories (bubble, bitumen, etc)

USING: 

    As a command line utility:
    
        $ DataBag.py file.db query "SOME sql=true QUERY"
        $ DataBag.py file.db repl
        $ DataBag.py ":memory:" repl
        $ DataBag.py newfile.db import import.csv
        $ DataBag.py 1file.db compare 2file.csv
    
    As a module:
    
        from DataBag import DataBag
        bag = DataBag("../data/file.db")
        bag = DataBag.fromArg(existingBagOrFilePathToDB)
        
        
        

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
    
    @staticmethod
    def fromArg(bag):
        if isinstance(bag, DataBag):
            return bag
        if isinstance(bag, (str, unicode)):
            if not os.path.isfile(bag):
                raise OSError(2, 'No such data bag file', bag)
            else:
                return DataBag(bag)
        raise TypeError('Invalid bag.')
    
    def __init__(self, db_file = ":memory:", verbose = False):
        
        self.verbose = verbose
        self.name = db_file
        self.db = sqlite3.connect(db_file, isolation_level="DEFERRED")
        self.db.enable_load_extension(True)
        self.db.load_extension(os.path.dirname(os.path.realpath(__file__)) + "/libsqlitefunctions.so")
        
        self.say("Connected to database", db_file)
        self.initDB()
    
    def __repr__(self):
        return self.name.split('/')[-1]

    def say(self, *args):
        if self.verbose:
            print(args)
    

    def repl(self):
        # Read Evaluate Print Loop (REPL)
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
    
    def cursor(self):
        # for doing some raw SQL
        return self.db.cursor()
    
    def commit(self):
        # for doing some raw SQL
        return self.db.commit()
    
    def query(self, query):
        # Execute a string query
        # Access through self.cursor() when needing to escape arguments.
        c = self.db.cursor()
        c.execute(query)
        res = c.fetchall()
        return res
    
    def tryQuery(self, query):
        try:
            return self.query(query)
        except: 
            return None
    
    

    def queryJSON(self, query):
        # Same as self.query but returns a JSON formatting string.
        return json.dumps(self.query(query))
    
    def initDB(self):
        # Make sure tables and columns are as they should be.
        rev = self.revision()
        if rev is 0: self.migration_0()
        if rev is 1: self.migration_1()
        if rev is 2: self.migration_2()
        self.say("Database ready")

    
    def revision(self):
        c = self.db.cursor()
        rev = 0
        try:
            c.execute("SELECT value FROM meta where name='revision'")
            rev = int(c.fetchone()[0])
        except: pass
        self.say("BataBag revision", rev)
        return rev
    
    def migration_0(self):
        self.say("Migrating to revision", 1)
        c = self.cursor()
        if not self.tableExists("frames"):    c.execute("CREATE TABLE frames (frame INTEGER PRIMARY KEY, bitmap BLOB)")
        if not self.tableExists("assoc"):     c.execute("CREATE TABLE assoc (frame INTEGER, particle INTEGER, x REAL, y REAL)")
        if not self.tableExists("particles"): c.execute("CREATE TABLE particles (id INTEGER PRIMARY KEY, area REAL, intensity REAL, perimeter REAL)")
        if not self.tableExists("meta"):
            c.execute("CREATE TABLE meta (name TEXT PRIMARY KEY, value TEXT)")
            c.execute("INSERT INTO meta (name, value) VALUES ('revision', '1')")
        self.commit()
        self.migration_1()
    
    def migration_1(self):
        self.say("Migrating to revision", 2)
        if not self.tableExists("categories"):
            c = self.cursor()
            c.execute("CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT)")
            c.execute("INSERT INTO categories (id, name) VALUES (0, 'undefined')")
            c.execute("INSERT INTO categories (id, name) VALUES (1, 'unknown')")
            c.execute("INSERT INTO categories (id, name) VALUES (2, 'bitumen')")
            c.execute("INSERT INTO categories (id, name) VALUES (3, 'sand')")
            c.execute("INSERT INTO categories (id, name) VALUES (4, 'bubble')")
            self.commit()
        
        c.execute("ALTER TABLE particles ADD COLUMN radius REAL DEFAULT 0")
        c.execute("ALTER TABLE particles ADD COLUMN category INTEGER DEFAULT 0")
        
        self.commit()
        
        self.tryQuery("CREATE INDEX Idx1 on particles (area, intensity, perimeter)")
        self.tryQuery("CREATE INDEX Idx2 on particles (frame, category)") 
        self.tryQuery("CREATE INDEX Idx3 on assoc (frame, particle)")
        
        c.execute("UPDATE meta SET value='2' WHERE name='revision'");
        self.commit()
    
    def migration_2(self):
        self.say("Migrating to revision", 3)
        c = self.cursor()
        c.execute("ALTER TABLE assoc ADD COLUMN scale REAL")
        c.execute("ALTER TABLE assoc ADD COLUMN crop BLOB")
        c.execute("UPDATE meta SET value='3' WHERE name='revision'");
        self.commit()
    
    def tableExists(self, table):
        c = self.cursor()
        c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table,));
        return c.fetchone()[0] is 1
    
    def categoryFor(self, category):
        c = self.cursor()
        c.execute("SELECT id FROM categories WHERE name = ?", (category))
        id = c.fetchone()
        if id is None: return 0
        return id[0]
        
    def batchInsertFrame(self, props):
        number = props.get("number", 0)
        bitmap = props.get("bitmap", None)
        c = self.db.cursor()
        c.execute("SELECT frame FROM frames WHERE frame = ?", (number,))
        if len(c.fetchall()) == 0:
            if bitmap is None:
                c.execute("INSERT INTO frames (frame) VALUES (?)", (number,))
            else:
                c.execute("INSERT INTO frames (frame, bitmap) VALUES (?, ?)", (number, self.toPng(bitmap)))
    
    
    def insertFrame(self, props):
        self.batchInsertFrame(props)
        self.commit()
    
    def batchInsertParticle(self, props):
        id = props.get("id", None)
        area = props.get("area", 0)
        perimeter = props.get("perimeter", 0)
        intensity = props.get("intensity", 0)
        radius = props.get("radius", 0)
        category = props.get("category", 0)
        
        
        c = self.cursor()
        if id is None:
            c.execute("INSERT INTO particles (area, intensity, perimeter, radius, category) VALUES (?, ?, ?, ?, ?)", (area, intensity, perimeter, radius, category))
        else:
            c.execute("INSERT INTO particles (id, area, intensity, perimeter, radius, category) VALUES (?, ?, ?, ?, ?, ?)", (id, area, intensity, perimeter, radius, category))
        return c.lastrowid

    def insertParticle(self, props):
        lastrowid = self.batchInsertParticle(props)
        self.commit()
        return lastrowid
    
    def batchInsertAssoc(self, props):
        frame = props.get("frame", 0)
        particle = props.get("particle", 0)
        x = props.get("x", 0)
        y = props.get("y", 0)
        c = self.cursor()
        c.execute("INSERT INTO assoc (frame, particle, x, y) VALUES (?, ?, ?, ?)", (frame, particle, x, y))

    def insertAssoc(self, frame, particle, x, y):
        self.batchInsertAssoc(frame, particle, x, y)
        self.commit()


    def insertTrace(self, props, points):
        
        frame = props.get("frame", 1)
        area = props.get("area", 1)
        intensity = props.get("intensity", 0)
        perimeter = props.get("perimeter", 0)
        width = props.get("radius", 0)
        category = props.get("category", 0)
        
        samples = points.shape[0]
        if samples > 0:
            particle = self.batchInsertParticle(props)
            for pair in points:
                props.set("frame", frame)
                props.set("particle", particle)
                props.set("x", pair[0])
                props.set("y", pair[1])
                self.batchInsertFrame(frame)
                self.batchInsertAssoc(frame, pId, pair[0], pair[1])
                frame += 1
        self.commit()
    
    def particlesInFrame(self, frame, category = None):
        c = self.cursor()
        if category is None:
            c.execute("SELECT id, area, intensity, category, x, y FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ?", (frame,))
        else:    
            c.execute("SELECT id, area, intensity, category, x, y FROM assoc LEFT JOIN particles ON assoc.particle = particles.id WHERE frame = ? and category = ?", (frame, category))
        return np.array(c.fetchall())
    
    def particlePoints(self, particle):
        c = self.cursor()
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
                props = {
                    "frame": line[0], 
                    "area": line[1], 
                    "intensity": line[2],
                    "category": 2, # bitumen
                    "perimeter": 0
                }
                points = line[3:]
                samples = points.shape[0]
                if samples % 2 == 1:
                    raise ValueError("There must be equal number of x,y samples. Line " + l)
                points = points.reshape(2, samples/2).T
                self.insertTrace(props, points)


    
        

def build_parser():
    parser = ArgumentParser()
    parser.add_argument('dbfile', help='database to operate on', default=":memory:")
    parser.add_argument('action', help='command to execute [query, repl, compare]', default="")
    parser.add_argument('query', nargs='?', help='options for command', default="")
    parser.add_argument('-v', help='print verbose statements while executing', action='store_true')
    return parser


if __name__ == '__main__':
    parser = build_parser()
    options = parser.parse_args()
    if options.dbfile != ":memory:" and not os.path.isfile(options.dbfile):
        if options.v:
            self.say("Database file", options.dbfile, "does not exist. Creating.")
    bag = DataBag(options.dbfile, options.v)
    
    if options.action == "query":
        print(bag.queryJSON(options.query))
    
    if options.action == "repl":
        # TODO: accept stdin sql?
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

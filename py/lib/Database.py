#! /usr/bin/env python
"""
Database connector

Author: Martin Humphreys
"""

import asyncpg
import asyncio
from mpyx.F import F

DATABASE = "mot"
USERNAME = "martin"
PASSWORD = None


def cube_encoder(value):
    pass

def cube_decoder(value):
    pass


class Database(object):


    def __init__(self):
        self._pool = None
        pass
    
    async def pool(self):
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                database=DATABASE, user=USERNAME, password=PASSWORD, min_size=1, max_size=5)
        return self._pool

    async def query(self, query, *args):
        async with (await self.pool()).acquire() as connection:
            async with connection.transaction():
                async for record in connection.cursor(query, *args):
                    yield record
    
    async def transaction(self):
        connection = await (await self.pool()).acquire()
        transaction = connection.transaction()
        await transaction.start()
        return (connection, transaction)

    async def execute(self, query, *args):
        async with (await self.pool()).acquire() as connection:
            async with connection.transaction():
                await connection.execute(query, *args)
    
    async def executemany(self, query, args):
        async with (await self.pool()).acquire() as connection:
            async with connection.transaction():
                await connection.executemany(query, args)
    
    async def category_map(self):
        mapping = dict()
        async for category in self.query("SELECT category, label FROM Category"):
            mapping[category["category"]] = category["label"]
            mapping[category["label"]] = category["category"]
        return mapping
    
    async def createSchema(self):
        await self.execute("""
            
            CREATE EXTENSION IF NOT EXISTS "pgcrypto";
            CREATE EXTENSION IF NOT EXISTS "cube";
            
            
            CREATE TABLE Category (
                category SMALLINT NOT NULL ,
                label text NOT NULL 
            );
            ALTER TABLE Category ADD CONSTRAINT category_pk PRIMARY KEY (category);
            ALTER TABLE Category ADD CONSTRAINT category_unique UNIQUE (label);
            
            
            CREATE TABLE Experiment (
                experiment UUID NOT NULL DEFAULT gen_random_uuid(),
                day date NOT NULL  DEFAULT CURRENT_DATE,
                name text,
                method text,
                notes text
            );
            ALTER TABLE Experiment ADD CONSTRAINT experiment_pk PRIMARY KEY (experiment);
            ALTER TABLE Experiment ADD CONSTRAINT experiment_day_and_name_unique UNIQUE (name,day,method);
            CREATE INDEX Experiment_day_index ON Experiment(day);
            
            CREATE TABLE Segment (
                segment UUID NOT NULL DEFAULT gen_random_uuid(),
                experiment UUID NOT NULL,
                number integer NOT NULL
            );
            ALTER TABLE Segment ADD CONSTRAINT segment_pk PRIMARY KEY (segment);
            ALTER TABLE Segment ADD CONSTRAINT segment_experiment_fk FOREIGN KEY (experiment) REFERENCES Experiment(experiment) ON UPDATE CASCADE ON DELETE CASCADE;
            CREATE INDEX segment_experiment_index ON Segment(experiment);
            
            CREATE TABLE Frame (
                frame UUID NOT NULL DEFAULT gen_random_uuid(),
                experiment UUID NOT NULL,
                segment UUID,
                number integer NOT NULL 
            );
            ALTER TABLE Frame ADD CONSTRAINT frame_pk PRIMARY KEY (frame);
            ALTER TABLE Frame ADD CONSTRAINT frame_experiment_fk FOREIGN KEY (experiment) REFERENCES Experiment(experiment) ON UPDATE CASCADE ON DELETE CASCADE;
            ALTER TABLE Frame ADD CONSTRAINT frame_segment_fk FOREIGN KEY (segment) REFERENCES Segment(segment) ON UPDATE CASCADE ON DELETE SET NULL;
            CREATE INDEX Frame_experiment_index ON Frame(experiment);
            CREATE INDEX Frame_segment_index ON Frame(segment);
            CREATE INDEX Frame_frame_number_index ON Frame(frame, number);
            
            
            CREATE TABLE Particle (
                particle UUID NOT NULL DEFAULT gen_random_uuid(),
                experiment UUID NOT NULL ,
                area REAL,
                intensity REAL,
                perimeter REAL,
                radius REAL,
                category SMALLINT,
                valid BOOLEAN
            );
            ALTER TABLE Particle ADD CONSTRAINT particle_pk PRIMARY KEY (particle);
            ALTER TABLE Particle ADD CONSTRAINT particle_experiment_fk FOREIGN KEY (experiment) REFERENCES Experiment(experiment) ON UPDATE CASCADE ON DELETE CASCADE;
            ALTER TABLE Particle ADD CONSTRAINT particle_category_fk FOREIGN KEY (category) REFERENCES Category(category) ON UPDATE CASCADE ON DELETE SET NULL;
            CREATE INDEX Particle_experiment_index ON Particle(experiment);
            CREATE INDEX Particle_category_index ON Particle(category);
            
            
            CREATE TABLE Track (
                track UUID NOT NULL DEFAULT gen_random_uuid(),
                frame UUID NOT NULL,
                particle UUID NOT NULL,
                location POINT NOT NULL,
                bbox BOX,
                latent CUBE
            );
            ALTER TABLE Track ADD CONSTRAINT track_pk PRIMARY KEY (frame,particle);
            ALTER TABLE Track ADD CONSTRAINT track_frame_fk FOREIGN KEY (frame) REFERENCES Frame(frame) ON UPDATE CASCADE ON DELETE CASCADE;
            ALTER TABLE Track ADD CONSTRAINT track_particle_fk FOREIGN KEY (particle) REFERENCES Particle(particle) ON UPDATE CASCADE ON DELETE CASCADE;
            CREATE INDEX Track_track_index  ON Track(track);
            CREATE INDEX Track_frame_index  ON Track(frame);
            CREATE INDEX Track_particle_index  ON Track(particle);
            CREATE INDEX Track_frame_particle_index  ON Track(frame, particle);
            CREATE INDEX Track_location_index  ON Track USING gist(location);
            CREATE INDEX Track_latent_index  ON Track USING gist(latent);
            
        """)
    
    async def insertFixtures(self):
        await self.execute("""
            INSERT INTO Category (category, label) VALUES (0, 'undefined');
            INSERT INTO Category (category, label) VALUES (1, 'unknown');
            INSERT INTO Category (category, label) VALUES (2, 'bitumen');
            INSERT INTO Category (category, label) VALUES (3, 'sand');
            INSERT INTO Category (category, label) VALUES (4, 'bubble');
        """)
    
    async def dropTables(self):
        await self.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$; """)
    
    async def vacuum(self):
        async with (await self.pool()).acquire() as connection: 
            await connection.execute("VACUUM FULL;")


    async def reset(self):
        print("Database reset commencing in 5 seconds...")
        await asyncio.sleep(5)
        
        print("Bobby is dropping the tables...")
        await self.dropTables()
            
        print("Vacuuming...")
        await self.vacuum()
        
        print("Rebuilding schema...")
        await self.createSchema()
        
        print("Inserting fixtures...")
        await self.insertFixtures()
        
        
        print("Database reset complete.")



class DBReader(F):
    
    def setup(self, query, *args):
        self.async(self.begin(Database(), query, *args))
        
    async def begin(self, db, q, *args):
        async for row in db.query(q, *args):
            if self.stopped():
                break
            else:
                self.push(dict(row))

class DBWriter(F):

    def initialize(self):
        self.commit_event = self.Event()

    def setup(self):
        print("DBWriter meta", self.meta)
        self.tx, self.transaction = self.async(Database().transaction())
        print("DBWriter tx", self.tx)
        
    def do(self, sql):
        method, query, args = sql
        self.async(getattr(self.tx, method)(query, *args))
        
    def teardown(self):
        print("db dying")
        if self.commit_event.is_set():
            print("db commiting")
            self.async(self.transaction.commit())
        else:
            print("db rollback")
            self.async(self.transaction.rollback())
    
    def commit(self):
        self.commit_event.set()
        return self
        
    def rollback(self):
        self.stop()
        return self
    

    
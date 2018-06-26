"""
A network flow multiple object tracker

    Zhang et al. 2008 Section 3
    This formulation can be mapped into a cost-flow network
    G(X ) with source s and sink t. Given an observation set
    X : for every observation xi ∈ X , create two nodes ui, vi,
    create an arc (ui, vi) with cost c(ui, vi) = Ci and flow
    f(ui, vi) = fi, an arc (s, ui) with cost c(s, ui) = Cen,i
    and flow f(s, ui) = fen,i, and an arc (vi, t) with cost
    c(vi, t) = Cex,i and flow f(vi, t) = fex,i. For every transition
    Plink(xj |xi) = 0, create an arc (vi, uj ) with cost
    c(vi, uj ) = Ci,j and flow f(vi, uj ) = fi,j . An example
    of such a graph is shown in Figure 2. Eqn.10 is equivalent
    to the flow conservation constraint and Eqn.11 to the cost
    of flow in G. Finding optimal association hypothesis T ∗ is
    equivalent to sending the flow from source s to sink t that
    minimizes the cost.
    
    Cen = -log(Pentr(xi))
    Cex = -log(Pexit(xi))
    Cij = -Log(Plink(xi|xj))
    Ci = log(Bi/(1-Bi)
    
    Bi := miss detection rate of detector
    Pentr = Pexit 
          = #traj / #hyp
    Plink = Psize*Pposiiton*Pappearance*Ptime
    
    

Cost Strategies:
- Try dot product on the encoded state (Nilanjan)
   - allows for computation of all forward passes before graph time
- Aggregate all the node pairs with edges between them,
  then forward pass, the set cost
- Use engineered cost
- Use engineered + network cost
   
"""

import config


from lib.Database import Database

import numpy as np

import os
from os.path import isdir, isfile, join
import shutil
import traceback
import multiprocessing
import subprocess
import threading
import concurrent.futures
import tempfile
import queue
import asyncio
from scipy.optimize import golden

from skimage import io
import time

from uuid import uuid4, UUID

import pyMCFSimplex

from mpyx.F import EZ, As, By, F, Seq, Data


async def main(args):

    if len(args) < 1:
        print("USING: experiment-uuid [method]")
    else:
        start = time.time()
        return await track_experiment(*args)


class SegmentEmitter(F):

    def setup(self, experiment_uuid):
        self.verbose = False
        self.async(self.query(experiment_uuid))

    async def query(self, experiment_uuid):
        db = Database()
        async for segment in db.query(
            """
            SELECT segment, number
            FROM segment
            WHERE experiment = $1
            ORDER BY number ASC
            """,
            experiment_uuid,
        ):
            if self.verbose:
                print("Emitting segment", segment["number"], "for processing...")
            self.put(segment["segment"])


class Tracker(F):

    def setup(self, new_experiment_uuid, frame_uuid_map, track_uuid_map):
        self.db = Database()
        self.tx, self.transaction = self.async(self.db.transaction())
        self.new_experiment_uuid = new_experiment_uuid
        self.frame_uuid_map = frame_uuid_map
        self.track_uuid_map = track_uuid_map
        self.verbose = False

    async def getEdges(self, segment):

        Ci = -100
        Cen = 150
        Cex = 150

        q = """
            SELECT f1.frame as fr1, f2.frame as fr2,
                   t1.location as location1, t2.location as location2,
                   t1.bbox as bbox1, t2.bbox as bbox2,
                   t1.latent as latent1, t2.latent as latent2,
                   p1.area as area1, p2.area as area2,
                   p1.intensity as intensity1, p2.intensity as intensity2,
                   p1.radius as radius1, p2.radius as radius2,
                   p1.category as category1, p2.category as category2,
                   p1.perimeter as perimeter1, p2.perimeter as perimeter2,
                   tr1, tr2,
                   cost1,
                   cost2,
                   cost3
            FROM frame f1, frame f2,track t1, track t2, particle p1, particle p2
            JOIN LATERAL (
                SELECT t3.track AS tr1, tr2, cost1, cost2, cost3     
                FROM track t3
                JOIN LATERAL (
                    SELECT t4.track AS tr2,
                           ((1 + (t3.latent <-> t4.latent))
                           *(1 + (t3.location <-> t4.location))) AS cost1,
                           (1 + (t3.location <-> t4.location)) AS cost2,
                           (1 + (t3.latent <-> t4.latent)) AS cost3
                    FROM track t4
                    WHERE t4.frame = f2.frame
                    ORDER BY cost1 ASC
                    LIMIT 5
                ) C ON TRUE
                WHERE t3.frame = f1.frame
            ) E on true
            WHERE f1.number = f2.number-1
            AND t1.track = tr1 AND t2.track = tr2
            AND t1.particle = p1.particle AND t2.particle = p2.particle
            AND f1.segment = '{segment}'
            AND f2.segment = '{segment}'
            ORDER BY f1.number ASC;
            """
        # The following uses no deep learning
        ## Developed on the Syncrude bead 200-300 um megaspeed camera video
        q = """
            SELECT f1.frame as fr1, f2.frame as fr2,
                   t1.location as location1, t2.location as location2,
                   t1.bbox as bbox1, t2.bbox as bbox2,
                   t1.latent as latent1, t2.latent as latent2,
                   p1.area as area1, p2.area as area2,
                   p1.intensity as intensity1, p2.intensity as intensity2,
                   p1.radius as radius1, p2.radius as radius2,
                   p1.category as category1, p2.category as category2,
                   p1.perimeter as perimeter1, p2.perimeter as perimeter2,
                   p1.major as major1, p2.major as major2,
                   p1.minor as minor1, p2.minor as minor2,
                   p1.eccentricity as eccentricity1, p2.eccentricity as eccentricity2,
                   p1.orientation as orientation1, p2.orientation as orientation2,
                   p1.solidity as solidity1, p2.solidity as solidity2,
                   tr1, tr2,
                   cost1,
                   cost2,
                   cost3
            FROM frame f1, frame f2,track t1, track t2, particle p1, particle p2
            JOIN LATERAL (
                SELECT t3.track AS tr1, tr2, cost1, cost2, cost3     
                FROM track t3
                JOIN LATERAL (
                    SELECT t4.track AS tr2,
                           ((1 + (t3.latent <-> t4.latent))
                           *(1 + (t3.location <-> t4.location))) AS cost1,
                           (1 + (t3.location <-> t4.location)) AS cost2,
                           (1 + (t3.latent <-> t4.latent)) AS cost3
                    FROM track t4
                    WHERE t4.frame = f2.frame
                    ORDER BY cost2 ASC
                    LIMIT 5
                ) C ON TRUE
                WHERE t3.frame = f1.frame
            ) E on true
            WHERE f1.number = f2.number-1
            AND t1.track = tr1 AND t2.track = tr2
            AND t1.particle = p1.particle AND t2.particle = p2.particle
            AND f1.segment = '{segment}'
            AND f2.segment = '{segment}'
            ORDER BY f1.number ASC;
            """
        s = q.format(segment=segment)
        async for edges in self.db.query(s):
            if edges["tr1"] not in self.edge_data:
                self.edge_data[edges["tr1"]] = {
                    "track": edges["tr1"],
                    "frame": edges["fr1"],
                    "location": edges["location1"],
                    "bbox": edges["bbox1"],
                    "latent": edges["latent1"],
                    "area": edges["area1"],
                    "intensity": edges["intensity1"],
                    "radius": edges["radius1"],
                    "perimeter": edges["perimeter1"],
                    "major": edges["major1"],
                    "minor": edges["minor1"],
                    "orientation": edges["orientation1"],
                    "solidity": edges["solidity1"],
                    "eccentricity": edges["eccentricity1"],
                    "category": edges["category1"],
                }
            self.edge_data[edges["tr2"]] = {
                "track": edges["tr2"],
                "frame": edges["fr2"],
                "location": edges["location2"],
                "bbox": edges["bbox2"],
                "latent": edges["latent2"],
                "area": edges["area2"],
                "intensity": edges["intensity2"],
                "radius": edges["radius2"],
                "perimeter": edges["perimeter2"],
                "major": edges["major2"],
                "minor": edges["minor2"],
                "orientation": edges["orientation2"],
                "solidity": edges["solidity2"],
                "eccentricity": edges["eccentricity2"],
                "category": edges["category2"],
            }

            u1, v1 = "u_" + str(edges["tr1"]), "v_" + str(edges["tr1"])
            u2, v2 = "u_" + str(edges["tr2"]), "v_" + str(edges["tr2"])

            # create ui, create vi, create edge (ui, vi), cost CI(ui,vi), cap = 1
            if self.mcf_graph.add_node(u1):
                self.mcf_graph.add_node(v1)

                # Heuristic reward for larger, darker; penalize undefined
                larger = 500
                darker = 0
                area = self.edge_data[edges["tr1"]]["area"]
                intensity = self.edge_data[edges["tr1"]]["intensity"]
                nodeCi = Ci * (1 + (area / larger) * ((255 - intensity) / 255))
                # if not edge_data[edges["tr1"]]["category"]:
                # nodeCi = 10
                # End heuristic reward

                self.mcf_graph.add_edge(u1, v1, capacity=1, weight=int(nodeCi))
                self.mcf_graph.add_edge("START", u1, capacity=1, weight=Cen)
                self.mcf_graph.add_edge(v1, "END", capacity=1, weight=Cex)

            if self.mcf_graph.add_node(u2):
                self.mcf_graph.add_node(v2)

                # Heuristic reward for larger, darker; penalize undefined
                larger = 500
                darker = 0
                area = self.edge_data[edges["tr2"]]["area"]
                intensity = self.edge_data[edges["tr2"]]["intensity"]
                nodeCi = Ci * (1 + (area / larger) * ((255 - intensity) / 255))
                # if not edge_data[edges["tr1"]]["category"]:
                # nodeCi = 10
                # End heuristic reward

                self.mcf_graph.add_edge(u2, v2, capacity=1, weight=int(nodeCi))
                self.mcf_graph.add_edge("START", u2, capacity=1, weight=Cen)
                self.mcf_graph.add_edge(v2, "END", capacity=1, weight=Cex)

            # Cij = -Log(Plink(xi|xj)), Plink = Psize*Pposiiton*Pappearance*Ptime
            Cij = int(2 * edges["cost2"])
            self.costs.append(Cij)

            self.mcf_graph.add_edge(v1, u2, weight=Cij, capacity=1)

    async def inserts(self):
        await self.tx.executemany(
            """
            INSERT INTO Particle (particle, 
                                  experiment, 
                                  area, 
                                  intensity, 
                                  perimeter, 
                                  major,
                                  minor,
                                  orientation,
                                  solidity,
                                  eccentricity,
                                  category)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """,
            self.particle_inserts,
        )

        await self.tx.executemany(
            """
            INSERT INTO Track (track, frame, particle, location, bbox, latent)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
            self.track_inserts,
        )

    def do(self, segment):

        self.mcf_graph = MCF_GRAPH_HELPER()
        self.mcf_graph.add_node("START")
        self.mcf_graph.add_node("END")

        self.edge_data = dict()
        self.costs = []

        self.async(self.getEdges(segment))

        if self.mcf_graph.n_nodes == 2:  # only START and END nodes present (empty)
            if self.verbose:
                print("Nothing in segment")
            return

        if self.verbose:
            print("cost", np.min(self.costs), np.mean(self.costs), np.max(self.costs))

        if self.verbose:
            print("Solving min-cost-flow for segment")

        demand = goldenSectionSearch(
            self.mcf_graph.solve,
            0,
            self.mcf_graph.n_nodes // 4,
            self.mcf_graph.n_nodes // 2,
            10,
            memo=None,
        )

        if self.verbose:
            print("Optimal number of tracks", demand)
        min_cost = self.mcf_graph.solve(demand)
        if self.verbose:
            print("Min cost", min_cost)

        mcf_flow_dict = self.mcf_graph.flowdict()
        self.mcf_graph = None

        tracks = dict()
        for dest in mcf_flow_dict["START"]:
            new_particle_uuid = uuid4()
            track = []
            curr = dest
            while curr != "END":
                if curr[0] == "u":
                    old_particle_uuid = UUID(curr.split("_")[-1])
                    track.append(old_particle_uuid)
                curr = mcf_flow_dict[curr][0]

            tracks[new_particle_uuid] = track

        if self.verbose:
            print("Tracks reconstructed", len(tracks))

        """
        Headers for Syncrude 2018
        
        Frame ID, 
        Particle ID, 
        Particle Area, 
        Particle Velocity, 
        Particle Intensity, 
        Particle Perimeter, 
        X Position, 
        Y Position, 
        Major Axis Length, 
        Minor Axis Length, 
        Orientation, 
        Solidity, 
        Eccentricity.
        """

        start = time.time()
        self.particle_inserts = []
        self.track_inserts = []
        for new_particle_uuid, track in tracks.items():
            mean_area = 0.0
            mean_intensity = 0.0
            mean_perimeter = 0.0
            # mean_radius = 0.0
            mean_major = 0.0
            mean_minor = 0.0
            mean_orientation = 0.0
            mean_solidity = 0.0
            mean_eccentricity = 0.0
            category = []

            for data in [self.edge_data[i] for i in track]:
                mean_area += data["area"] / len(track)
                mean_intensity += data["intensity"] / len(track)
                mean_perimeter += data["perimeter"] / len(track)
                # mean_radius += data["radius"] / len(track)
                mean_major += data["major"] / len(track)
                mean_minor += data["minor"] / len(track)
                mean_orientation += data["orientation"] / len(track)
                mean_solidity += data["solidity"] / len(track)
                mean_eccentricity += data["eccentricity"] / len(track)
                category.append(data["category"])

                new_frame_uuid = self.frame_uuid_map[data["frame"]]
                new_track_uuid = self.track_uuid_map[data["track"]]

                loc = (data["location"][0], data["location"][1])
                bbox = (
                    (data["bbox"][0][0], data["bbox"][0][1]),
                    (data["bbox"][1][0], data["bbox"][1][1]),
                )

                self.track_inserts.append(
                    (new_track_uuid, new_frame_uuid, new_particle_uuid, loc, bbox)
                )

            category = np.argmax(np.bincount(category))

            self.particle_inserts.append(
                (
                    new_particle_uuid,
                    self.new_experiment_uuid,
                    mean_area,
                    mean_intensity,
                    mean_perimeter,
                    mean_major,
                    mean_minor,
                    mean_orientation,
                    mean_solidity,
                    mean_eccentricity,
                    category,
                )
            )

        # self.async(self.inserts())

        trackingData = TrackingData()
        trackingData.save("particles", self.particle_inserts)
        trackingData.save("tracks", self.track_inserts)

        self.put(trackingData)

    def teardown(self,):
        self.async(self.transaction.commit())
        # self.async(self.db.vacuum('track'))


class TrackingData(Data):

    def initialize(self):
        pass


class CSVWriter(F):

    def initialize(self, experiment_uuid):
        self.experiment_uuid = experiment_uuid
        self.verbose = True
        if self.verbose:
            print("Launching CSV processor")

        self.csv_files = ["/tmp/{}_track.csv", "/tmp/{}_particle.csv"]

    def do(self, trackingData):
        # Add detections
        self.add_tracking_data(trackingData)
        trackingData.erase("particles")
        trackingData.erase("tracks")
        self.put(trackingData)

    def add_tracking_data(self, trackingData):
        particles = list(trackingData.load("particles"))
        tracks = trackingData.load("tracks")

        s = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_particle.csv".format(self.experiment_uuid), "a") as f:
            for p in particles:
                f.write(
                    s.format(
                        p[0],
                        p[1],
                        p[2],
                        p[3],
                        p[4],
                        p[5],
                        p[6],
                        p[7],
                        p[8],
                        p[9],
                        p[10],
                    )
                )

        s = "{}\t{}\t{}\t{}\t{}\n"
        with open("/tmp/{}_track.csv".format(self.experiment_uuid), "a") as f:
            for t in tracks:
                f.write(s.format(t[0], t[1], t[2], t[3], t[4]))


class DBProcessor(F):

    def initialize(self, experiment_uuid):
        self.verbose = True
        if self.verbose:
            print("Launching DB processor")
        self.experiment_uuid = experiment_uuid

        self.csv_files = ["/tmp/{}_track.csv", "/tmp/{}_particle.csv"]

    async def copy_to_database(self):
        if self.verbose:
            print("Copying to database.")

        if self.verbose:
            print("Inserting particles into database.")
        await self.tx.execute(
            """
            COPY particle (particle, experiment, area, intensity, perimeter, major, minor, orientation, solidity, eccentricity, category\n)FROM '/tmp/{}_particle.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )
        if self.verbose:
            print("Inserting tracks into database.")
        await self.tx.execute(
            """
            COPY track (track, frame, particle, location, bbox\n) FROM '/tmp/{}_track.csv' DELIMITER '\t' CSV;
            """.format(
                self.experiment_uuid
            )
        )

    def teardown(self):
        self.tx, self.transaction = self.async(Database().transaction())
        try:
            self.async(self.copy_to_database())
        except Exception as e:
            print(e)
            print("rolling back database")
            self.async(self.transaction.rollback())
        else:
            self.async(self.transaction.commit())
        self.cleanupFS()

    def cleanupFS(self):
        for f in self.csv_files:
            if os.path.isfile(f.format(self.experiment_uuid)):
                os.remove(f.format(self.experiment_uuid))


class Cleaner(F):

    def do(self, trackingData):
        trackingData.clean()


async def track_experiment(experiment_uuid, method="Tracking_Parallel", model=None):
    """
    
    """
    verbose = True
    cpus = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    db = Database()

    # Clone the experiment
    try:
        start = time.time()
        tx, transaction = await db.transaction()
        new_experiment_uuid, frame_uuid_map, track_uuid_map = await clone_experiment(
            experiment_uuid, tx, testing=False, method=method
        )
        await transaction.commit()
        new_experiment_dir = os.path.join(
            config.experiment_dir, str(new_experiment_uuid)
        )
        if verbose:
            print("clone time:", time.time() - start)

        # End Cloning

        # 2) Perform tracking analysis

        segments = (
            EZ(
                SegmentEmitter(experiment_uuid),
                As(12, Tracker, new_experiment_uuid, frame_uuid_map, track_uuid_map),
                CSVWriter(new_experiment_uuid),
                DBProcessor(new_experiment_uuid),
                Cleaner(),
            )
            .start()
            .join()
        )

    except Exception as e:  ### ERROR: UNDO EVERYTHING !    #################
        print("Uh oh. Something went wrong")
        traceback.print_exc()

        await transaction.rollback()

        if os.path.exists(new_experiment_dir):
            shutil.rmtree(new_experiment_dir)
        traceback.print_exc()

    else:
        ##################  OK: COMMIT DB TRANSACTRION    ###############
        if verbose:
            print("made it! :)")
        # await transaction.commit()

    return str(new_experiment_uuid)


async def clone_experiment(experiment_uuid, tx, method, testing=False):

    # Create maps

    new_experiment_uuid = uuid4()
    experiment_path = join(config.experiment_dir, str(experiment_uuid))

    base_files = [
        file
        for file in os.listdir(experiment_path)
        if isfile(join(experiment_path, file))
    ]

    s = """
        SELECT frame
        FROM frame
        WHERE experiment = '{experiment}'
        """
    q = s.format(experiment=experiment_uuid)
    dbFrames = []
    async for row in tx.cursor(q):
        dbFrames.append(str(row["frame"]))

    osFrames = [
        frame
        for frame in os.listdir(experiment_path)
        if isdir(join(experiment_path, frame))
    ]
    frame_uuid_map = {UUID(f): uuid4() for f in dbFrames}

    s = """
        SELECT t.frame as frame, track
        FROM track t, frame f
        WHERE t.frame = f.frame
        AND f.experiment = '{experiment}'
        """
    q = s.format(experiment=experiment_uuid)
    dbTracks = []
    async for row in tx.cursor(q):
        dbTracks.append(str(row["track"]))

    osTracks = [
        (frame, os.path.splitext(track))
        for frame in osFrames
        for track in os.listdir(join(experiment_path, frame))
        if len(track) == 40
    ]
    track_uuid_map = {UUID(track): uuid4() for track in dbTracks}

    # tracks = [(frame, (uuid, ext))]

    # Copy data

    new_experiment_path = join(config.experiment_dir, str(new_experiment_uuid))
    if not testing:
        os.mkdir(new_experiment_path)
    await tx.execute(
        """
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            SELECT $1, day, name, $3, notes FROM Experiment
            WHERE experiment = $2
            """,
        new_experiment_uuid,
        experiment_uuid,
        method,
    )
    if not testing:
        for file in base_files:
            os.link(join(experiment_path, file), join(new_experiment_path, file))

        for old_frame_uuid, new_frame_uuid in frame_uuid_map.items():
            os.mkdir(join(new_experiment_path, str(new_frame_uuid)))

    segment_uuid_map = {}
    segment_insert = []
    async for s in tx.cursor(
        "SELECT segment, number FROM Segment WHERE experiment = $1", experiment_uuid
    ):
        segment_uuid = uuid4()
        segment_uuid_map[s["segment"]] = {
            "segment": segment_uuid,
            "number": s["number"],
        }
        segment_insert.append((segment_uuid, new_experiment_uuid, s["number"]))

    await tx.executemany(
        "INSERT INTO Segment (segment, experiment, number) VALUES ($1, $2, $3)",
        segment_insert,
    )

    frame_segment_map = {}
    async for f in tx.cursor(
        "select frame, segment From Frame WHERE experiment = $1", experiment_uuid
    ):
        frame_segment_map[f["frame"]] = segment_uuid_map[f["segment"]]["segment"]

    await tx.executemany(
        """
            INSERT INTO Frame (frame, experiment, segment, number) 
            SELECT $1, $2, $3, number FROM Frame
            WHERE frame = $4
            """,
        [
            (
                frame_uuid_map[UUID(frame)],
                new_experiment_uuid,
                frame_segment_map[UUID(frame)],
                UUID(frame),
            )
            for frame in dbFrames
        ],
    )

    if not testing:
        for track in osTracks:
            os.link(
                join(experiment_path, track[0], "".join(track[1])),
                join(
                    new_experiment_path,
                    str(frame_uuid_map[UUID(track[0])]),
                    str(track_uuid_map[UUID(track[1][0])]) + track[1][1],
                ),
            )

    return (new_experiment_uuid, frame_uuid_map, track_uuid_map)


class MCF_GRAPH_HELPER:
    """
    Add nodes with UUID substrings to this helper,
    will manage the mapping between nodes and an integer
    name.
    
    Simplified for our purposes, the graph will always have a
    super-source/super-sink 'START'/'END', 
    and will be assigned demand and -demand respectively.
    
    Simplified for our purposes, the capacity will always have
    a lower bound zero, and can not be set explicitly.
    """

    def __init__(self, verbose=False):
        self.nodes = dict()
        self.edges = []
        self.n_nodes = 0
        self.n_edges = 0
        self.demand = 0
        self.verbose = verbose

    def add_node(self, k):
        """
        expects uuid
        pyMCFSimplex node names {1,2,...,n}
        returns true if the node was added, false
        if the node was added prior.
        """
        if not k in self.nodes:
            self.nodes[k] = self.n_nodes + 1
            self.nodes[self.n_nodes + 1] = k
            self.n_nodes += 1
            return True
        else:
            return False

    def add_edge(self, start, end, capacity, weight):
        """
        expects uuid start/end nodes
        """
        self.edges.append((self.nodes[start], self.nodes[end], 0, capacity, weight))
        self.n_edges += 1

    def remove(self, k):
        self.d.pop(self.d.pop(k))

    def get_node(self, k):
        """
        given an integer returns {'u_', 'v_'}+str(UUID)
        given {'u_', 'v_'}+str(UUID) returns integer
        """

        if isinstance(k, int):
            return self.nodes[k]
        else:
            return self.nodes[k]

    def write(self, file):
        """
        writes graph to file for input to pyMCFSimplex
        """
        file.write("p min %s %s\n" % (self.n_nodes, self.n_edges))
        file.write("n %s %s\n" % (self.nodes["START"], self.demand))
        file.write("n %s %s\n" % (self.nodes["END"], -self.demand))

        for (start, end, low, high, weight) in self.edges:
            file.write("a %s %s %s %s %s\n" % (start, end, low, high, weight))

    def solve(self, demand):
        self.demand = demand
        self.mcf = pyMCFSimplex.MCFSimplex()
        fp = tempfile.TemporaryFile("w+")
        self.write(fp)
        fp.seek(0)
        inputStr = fp.read()
        fp.close()
        self.mcf.LoadDMX(inputStr)
        # solve graph
        self.mcf.SetMCFTime()
        self.mcf.SolveMCF()
        if self.mcf.MCFGetStatus() == 0:
            min_cost = self.mcf.MCFGetFO()
            if self.verbose:
                print("Optimal solution: %s" % self.mcf.MCFGetFO())
                print("Time elapsed: %s sec " % (self.mcf.TimeMCF()))
            return min_cost
        else:
            if self.verbose:
                print("Problem unfeasible!")
                print("Time elapsed: %s sec " % (self.mcf.TimeMCF()))
            return float("inf")

    def flowdict(self):
        mcf_flow_dict = dict()
        # Build flowdict
        # BEGIN FROM EXAMPLE
        mmx = self.mcf.MCFmmax()
        pSn = []
        pEn = []
        startNodes = pyMCFSimplex.new_uiarray(mmx)
        endNodes = pyMCFSimplex.new_uiarray(mmx)
        self.mcf.MCFArcs(startNodes, endNodes)

        for i in range(0, mmx):
            pSn.append(pyMCFSimplex.uiarray_get(startNodes, i) + 1)
            pEn.append(pyMCFSimplex.uiarray_get(endNodes, i) + 1)

        length = self.mcf.MCFm()

        cost_flow = pyMCFSimplex.new_darray(length)
        self.mcf.MCFGetX(cost_flow)
        # END FROM EXAMPLE

        for i in range(0, length):
            startNode = pSn[i]
            endNode = pEn[i]
            flow = pyMCFSimplex.darray_get(cost_flow, i)

            if flow > 0:
                if not self.get_node(startNode) in mcf_flow_dict:
                    mcf_flow_dict[self.get_node(startNode)] = []
                mcf_flow_dict[self.get_node(startNode)].append(self.get_node(endNode))
                # print("Flow on arc %s from node %s to node %s: %s " %(i,startNode,endNode,flow,))
        return mcf_flow_dict


phi = (1 + np.sqrt(5)) / 2
resphi = 2 - phi
# a and b are the current bounds; the minimum is between them.
# c is the center pointer pushed slightly left towards a
def goldenSectionSearch(f, a, c, b, absolutePrecision, memo=None):
    if memo is None:
        memo = dict()

    if abs(a - b) < absolutePrecision:
        return int((a + b) / 2)
    # Create a new possible center, in the area between c and b, pushed against c
    d = int(c + resphi * (b - c))

    if d in memo:
        f_d = memo[d]
    else:
        f_d = f(d)
        memo[d] = f_d
        # print(d, f_d)

    if c in memo:
        f_c = memo[c]
    else:
        f_c = f(c)
        memo[c] = f_c
        # print(c, f_c)

    if f_d < f_c:
        return goldenSectionSearch(f, c, d, b, absolutePrecision, memo)
    else:
        return goldenSectionSearch(f, d, c, a, absolutePrecision, memo)

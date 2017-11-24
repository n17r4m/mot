

import config


from lib.Database import Database

import numpy as np
import networkx as nx

import os
from os.path import isdir, isfile, join
import shutil
import traceback
import multiprocessing
import subprocess
import threading
import concurrent.futures
from tempfile import TemporaryFile
import queue
import asyncio

from uuid import uuid4, UUID

USE_MCFSIMPLEX = True
if USE_MCFSIMPLEX:
    import pyMCFSimplex


async def main(args):
    
    if len(args) < 1: 
        
        print("What you want to track?")
        print("USING: experiment-uuid")
    else:
        print(await track_experiment(*args))




async def track_experiment(experiment_uuid):
    
    global USE_MCFSIMPLEX
    cpus = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    
    db = Database()
    
    
    async for experiment in db.query("SELECT * FROM Experiment WHERE experiment = $1", experiment_uuid):
        
      
        
        G = nx.DiGraph()
        G.add_node("START", demand=-150)
        G.add_node("END", demand=150)
        
        if USE_MCFSIMPLEX:
            mcf_graph = MCF_GRAPH_HELPER()
            mcf_graph.add_node('START')
            mcf_graph.add_node('END')

        frame_costs = []
        
        top_costs = [[], [], [], [], []]
        top_dists = [[], [], [], [], []]
        
        '''
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
        '''
        
        '''
        Cost Strategies:
        - Try dot product on the encoded state (Nilanjan)
           - allows for computation of all forward passes before graph time
        - Aggregate all the node pairs with edges between them,
          then forward pass, the set cost
        - Use engineered cost
        - Use engineered + network cost
        '''
        
        
        frame1 = None
        
        async for frame2 in db.query("SELECT * FROM Frame WHERE experiment = $1 ORDER BY number ASC", experiment["experiment"]):
            # for every observation xi
            async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame2["frame"]):
                # Ci = log(Bi/(1-Bi), Bi := miss detection rate of detector
                Ci = -100
                # create ui, create vi, create edge (ui, vi), cost CI(ui,vi), cap = 1
                G.add_node("u_"+str(track["track"]), particle=str(track["particle"]))
                G.add_node("v_"+str(track["track"]))
                G.add_edge("u_"+str(track["track"]), "v_"+str(track["track"]), capacity=1, weight=Ci)
                
                # Cen = -log(Pentr(xi)), Pentr = #traj / #hyp
                Cen = 150
                # create edge (s, ui), cost Cen(s, ui), cap = 1
                G.add_edge("START", "u_"+str(track["track"]), capacity=1, weight=Cen)
                
                # Cex = -log(Pexit(xi)), Pexit = #traj / #hyp
                Cex = 150
                # create edge (vi, t), cost Cex(vi, t), cap = 1
                G.add_edge("v_"+str(track["track"]), "END", capacity=1, weight=Cex)
                
                if USE_MCFSIMPLEX:
                    # Ci = log(Bi/(1-Bi), Bi := miss detection rate of detector
                    Ci = -100
                    # create ui, create vi, create edge (ui, vi), cost CI(ui,vi), cap = 1
                    mcf_graph.add_node("u_"+str(track["track"]))
                    mcf_graph.add_node("v_"+str(track["track"]))
                    mcf_graph.add_edge("u_"+str(track["track"]), "v_"+str(track["track"]), capacity=1, weight=Ci)
                    
                    # Cen = -log(Pentr(xi)), Pentr = #traj / #hyp
                    Cen = 150
                    # create edge (s, ui), cost Cen(s, ui), cap = 1
                    mcf_graph.add_edge("START", "u_"+str(track["track"]), capacity=1, weight=Cen)
                    
                    # Cex = -log(Pexit(xi)), Pexit = #traj / #hyp
                    Cex = 150
                    # create edge (vi, t), cost Cex(vi, t), cap = 1
                    mcf_graph.add_edge("v_"+str(track["track"]), "END", capacity=1, weight=Cex)
                        
            if frame1 is None:
                frame1 = frame2
                continue;
            
            frame_cost = 0
            
            print(frame1["frame"], frame1["number"])
            
            #async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame1["frame"]):
                
                
            
            async for track in db.query("""
                SELECT 
                    track as track,
                    candidates[0:5] as candidates,
                    costs[0:5] as costs
                FROM (
                    SELECT 
                        T.track AS track, 
                        array_agg(C.track ORDER BY C.cost ASC) AS candidates,
                        array_agg(C.cost ORDER BY C.cost ASC) AS costs
                    FROM 
                        Track as T, 
                        (
                            SELECT T2.track AS track, 
                                  round(((1 + (T1.latent <-> T2.latent))
                                * (1 + (T1.location <-> T2.location))))::int AS cost
                            FROM Track T1, Track T2
                            WHERE T1.frame = $1 
                            AND T2.frame = $2
                        ) AS C
                    WHERE T.track = C.track
                    GROUP BY T.track
                ) t""", frame1["frame"], frame2["frame"]):
                
                
                frame_cost += track["costs"][0]
                
                [G.add_edge("v_"+str(track["track"]), "u_"+str(c), weight=track["costs"][i], capacity=1) for i, c in enumerate(track["candidates"])]
                
                if USE_MCFSIMPLEX:
                    [mcf_graph.add_edge("v_"+str(track["track"]), "u_"+str(c), weight=track["costs"][i], capacity=1) for i, c in enumerate(track["candidates"])]
            
            
            frame_costs.append(frame_cost)
            
            frame1 = frame2
            #endof track
            
           
        
        # async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame2["frame"]):
        #     G.add_edge(str(track["track"]), "END", capacity=1)
        
        bursts = []
        
        fc_log = np.log(frame_costs)
        fc_std = np.std(fc_log)
        fc_med = np.median(fc_log)
        
        for i, cost in enumerate(fc_log):
            if cost > (fc_med + 1.5 * fc_std):
                if len(bursts) > 0 and bursts[-1] != (i - 1):
                    bursts.append(i)
                elif len(bursts) == 0:
                    bursts.append(i)
                    
        print(fc_log)
        print(fc_med, fc_std)
        print("Bursts detected on frames", bursts)
        
        
        demand = 4000

        G.node["START"]["demand"] = -demand
        G.node["END"]["demand"] = demand
        
        if USE_MCFSIMPLEX:
            mcf_graph.set_demand(demand)
            
        
        print("Writing graphml")
        nx.write_graphml(G, "test.graphml")
        
        
        print("Solving min-cost-flow.")    
        min_cost, flow_dict = nx.network_simplex(G)
        
        if USE_MCFSIMPLEX:
            # init the sovler
            mcf = MCFSimplex()
            
            # Write graph file
            with tempfile.TemporaryFile() as fp:
                mcf_graph.write(fp)
            
            # load graph file
            f = open(FILENAME,'r')
            inputStr = f.read()
            f.close()
            mcf.LoadDMX(inputStr)
            # solve graph
            mcf.SetMCFTime()
            mcf.SolveMCF()
            if mcf.MCFGetStatus() == 0:
                print("Optimal solution: %s" %mcf.MCFGetFO())
                print("Time elapsed: %s sec " %(mcf.TimeMCF()))
            else:
                print("Problem unfeasible!")
                print("Time elapsed: %s sec " %(mcf.TimeMCF()))
                
        
        ####################      BEGIN: Recover Tracks     ####################
        # tracks[new_particle_uuid] = dict(old_frame_uuids: (old_track_uuid, old_particle_uuid))
        # suggestion:
        # tracks[new_particle_uuid] = [old_particle_id1, old_particle_id1, ...]
        tracks = dict()
        for dest, flow in flow_dict["START"].items():
            if not flow:
                continue
            
            new_particle_uuid = uuid4()
            track = []
            curr = dest
            while(curr != "END"):
                if curr[0] == 'u':
                    # old_particle_uuid = UUID(G.node[curr]["particle"])
                    old_particle_uuid = UUID(curr.split('_')[-1])
                    
                    track.append(old_particle_uuid)
                
                for dest, flow in flow_dict[curr].items():
                    if not flow:
                        continue
                    curr = dest
                    break # can't have multiple outgoing flows
            
            tracks[new_particle_uuid] = track
        
        print('tracks reconstructed')
        # insert experiment
        # copy experiment videos 
        # insert frame (if needed) (keep list of inserted?)
        # create frame directory in experiment directory (if needed)
        # insert 1 particle
        # insert n tracks for particle
        # copy track crops into new frame directory
        
        
        
        
        
        ####################       END: Recover Tracks      ####################

        ####################     START DB TRANSACTRION      ####################
        try:
            tx, transaction = await db.transaction()
            new_experiment_uuid, frame_uuid_map, track_uuid_map = await clone_experiment(experiment_uuid, tx)
            new_experiment_dir = os.path.join(config.experiment_dir, str(new_experiment_uuid))
            
            # frame_uuid_map[old_frame_uuid] = new_frame_uuid
            # track_uuid_map[old_track_uuid] = new_track_uuid
            
            #  Particle: (particle, experiment, area, intensity, perimeter, radius, category)
            #  Track: (track, frame, particle, location, bbox, latent)
            for new_particle_uuid, track in tracks.items():
                mean_area = 0.0
                mean_intensity = 0.0
                mean_perimeter = 0.0
                mean_radius = 0.0
                category = []
                
                # insert particle
                await tx.execute("""
                    INSERT INTO Particle (particle, experiment)
                    VALUES ($1, $2)
                """, new_particle_uuid, new_experiment_uuid)
                
                # compute averages / insert tracks
                async for data in tx.cursor("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE particle = ANY($1::UUID[])", track):
                    mean_area += data["area"] / len(track)
                    mean_intensity += data["intensity"] / len(track)
                    mean_perimeter += data["perimeter"] / len(track)
                    mean_radius += data["radius"] / len(track)
                    category.append(data["category"])
                    
                    new_frame_uuid = frame_uuid_map[data["frame"]]
                    new_track_uuid = track_uuid_map[data["track"]]
                    
                    new_track = (new_track_uuid,
                                 new_frame_uuid,
                                 new_particle_uuid,
                                 data["location"],
                                 data["bbox"],
                                 data["latent"])
                    
                    await tx.execute("""
                        INSERT INTO Track (track, frame, particle, location, bbox, latent)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, *new_track)
                
                
                
                # update particle stats
                category = np.argmax(np.bincount(category))
                await tx.execute("""
                    UPDATE Particle
                    SET area = $1, intensity = $2, perimeter = $3, radius = $4, category = $5
                    WHERE particle = $6
                """, mean_area, mean_intensity, mean_perimeter, mean_radius, category, new_particle_uuid)
                

        
        except Exception as e: ### ERROR: UNDO EVERYTHING !    #################
            print("Uh oh. Something went wrong")
            traceback.print_exc()
            
            await transaction.rollback()
            
            if os.path.exists(new_experiment_dir):
                shutil.rmtree(new_experiment_dir)
            traceback.print_exc()
            
        
        else:  ##################  OK: COMMIT DB TRANSACTRION    ###############
            await transaction.commit()
            

        ####################     END: Handle Filesystem     ####################
        
        # for u in flow_dict:
        #     print(u, flow_dict[u])
        print("min cost", min_cost)
        
        # mu = np.median(top_costs, axis=1)
        # std = np.std(top_costs, axis=1)
        # np.save('top_costs', top_costs)
        # np.save('top_dists', top_dists)
        # print(len(top_costs[0]))
        # print(mu)
        # print(std)
        
        
        """
        what is the sample size... n = ?
        [  1.18161018e+02   1.96167244e+06   5.58250181e+06   9.68133977e+06  1.46586190e+07]
        [  3.78273080e+07   4.08500494e+08   9.72344528e+08   1.52232527e+09  2.05291818e+09]
        """
        
        
        #print(frame_costs)
        
        
    return new_experiment_uuid
    """
    async for next_frame in db.query("")
        
    async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame["frame"]):
            
        print(track)
            
    """     
    
    
    
async def clone_experiment(experiment_uuid, tx):

    # Create maps
    
    new_experiment_uuid = uuid4()
    experiment_path = join(config.experiment_dir, str(experiment_uuid))
    
    base_files = [file for file in os.listdir(experiment_path) if isfile(join(experiment_path, file))]
    
    frames = [frame for frame in os.listdir(experiment_path) if isdir(join(experiment_path, frame))]
    frame_uuid_map = {UUID(f): uuid4() for f in frames}
    
    tracks = [(frame, os.path.splitext(track)) for frame in frames for track in os.listdir(join(experiment_path, frame))]
    track_uuid_map = {UUID(track[1][0]): uuid4() for track in tracks}
    
    # tracks = [(frame, (uuid, ext))]
    
    
    # Copy data
    
    new_experiment_path = join(config.experiment_dir, str(new_experiment_uuid))
    os.mkdir(new_experiment_path)
    await tx.execute("""
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            SELECT $1, day, name, 'tracking', notes FROM Experiment
            WHERE experiment = $2
            """, new_experiment_uuid, experiment_uuid)
    
    for file in base_files:
        os.link(join(experiment_path, file), join(new_experiment_path, file))
        
    
    for old_frame_uuid, new_frame_uuid in frame_uuid_map.items():
        os.mkdir(join(new_experiment_path, str(new_frame_uuid)))
    
    await tx.executemany("""
            INSERT INTO Frame (frame, experiment, number) 
            SELECT $1, $2, number FROM Frame
            WHERE frame = $3
            """, [(frame_uuid_map[UUID(frame)], new_experiment_uuid, UUID(frame)) for frame in frames])
    
    
    for track in tracks:
        os.link(
            join(experiment_path, track[0], "".join(track[1])), 
            join(new_experiment_path, 
                str(frame_uuid_map[UUID(track[0])]), 
                str(track_uuid_map[UUID(track[1][0])]) + track[1][1]))
    
    return (new_experiment_uuid, frame_uuid_map, track_uuid_map)
    


class VideoStreamCompressor(threading.Thread):
    def __init__(self, queue, experiment_dir, fname, width=2336, height=1729, fps=300., rate=24., pix_format="gray"):
        super(VideoStreamCompressor, self).__init__()
        self.queue = queue
        self.stop_event = threading.Event()
        self.cmd = ''.join(('ffmpeg',
          ' -f rawvideo -pix_fmt {}'.format(pix_format),
          ' -video_size {}x{}'.format(width,height),
          ' -framerate {}'.format(fps),
          ' -i -',
          ' -c:v libx264 -crf 15 -preset fast',
          ' -pix_fmt yuv420p',
          ' -filter:v "setpts={}*PTS'.format(fps/rate),
          ', crop={}:{}:0:0"'.format(width, height-1) if height % 2 else '"',
          ' -r 24',
          ' -movflags +faststart',
          ' "{}"'.format(os.path.join(experiment_dir, fname))))
    
    def run(self):
        proc = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            if self.stopped():
                return self.close(proc)
            else:
                frame_bytes = self.queue.get()
                if frame_bytes is None:
                    return self.close(proc)
                proc.stdin.write(frame_bytes)
    
    def close(self, proc):
        proc.stdin.close()
        proc.wait()
    
    def stop(self):
        self.stop_event.set()
    
    def stopped(self):
        return self.stop_event.is_set()
        


class MCF_GRAPH_HELPER:
    '''
    Add nodes with UUID substrings to this helper,
    will manage the mapping between nodes and an integer
    name.
    
    Simplified for our purposes, the graph will always have a
    super-source/super-sink 'ST, 
    and will be assigned -demand and demand respectively.
    
    Simplified for our purposes, the capacity will always have
    a lower bound zero
    '''
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.n_nodes = 0
        self.n_edges = 0
        self.demand = 0
        self.old_particle
    def add_node(self, k):
        self.nodes[k] = self.n_nodes
        self.nodes[self.n_nodes] = k
        self.n_nodes += 1
    def add_edge(self, start, end, capacity, weight):
        self.edges.append((self.nodes[start], 
                           self.nodes[end], 
                           0, 
                           capacity,
                           weight))
        self.n_edges += 1
    def remove(self, k):
        self.d.pop(self.d.pop(k))
    def get(self, k):
        return self.d[k]
    def set_demand(self, demand):
        self.demand = demand
    def write(self, file):
        file.write('p min $1 $2', (self.n_nodes, self.n_edges))
        file.write('n 1 $1', (self.demand,))
        file.write('n 2 $1', (-self.demand,))
        for (start, end, low, high, weight) in self.edges:
            file.write('a $1 $2 $3 $4 $5', (start, end, low, high, weight))
    

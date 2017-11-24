'''
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
   
'''

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

import time

from uuid import uuid4, UUID

import pyMCFSimplex


async def main(args):
    
    if len(args) < 1: 
        
        print("What you want to track?")
        print("USING: experiment-uuid")
    else:
        print(await track_experiment(*args))


async def track_experiment(experiment_uuid):
    
    cpus = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    db = Database()
    # Clone the experiment
    
    try:
        start = time.time()
        tx, transaction = await db.transaction()
        new_experiment_uuid, frame_uuid_map, track_uuid_map = await clone_experiment(experiment_uuid, tx, testing=False)
        new_experiment_dir = os.path.join(config.experiment_dir, str(new_experiment_uuid))
        print('clone time:', time.time()-start)
        
        # End Cloning
        
        
        
        # 2) Perform tracking analysis
        
        
        async for segment in tx.cursor("""
                                SELECT segment, number
                                FROM segment
                                WHERE experiment = $1
                                """, experiment_uuid):
                                    
            print('tracking segment', segment['number'])
            mcf_graph = MCF_GRAPH_HELPER()
            mcf_graph.add_node('START')
            mcf_graph.add_node('END')
        
            

            
            Ci = -100
            Cen = 150
            Cex = 150
            edge_data = dict()
            
            async for edges in db.query("""
                                        SELECT f1.frame as fr, tr1, tr2, cost
                                        FROM frame f1, frame f2
                                        JOIN LATERAL (
                                            SELECT t1.track AS tr1, tr2, cost
                                            FROM track t1
                                            JOIN LATERAL (
                                                SELECT 
                                                    t2.track AS tr2, 
                                                    ((1 + (t1.latent <-> t2.latent))
                                                    *(1 + (t1.location <-> t2.location))) AS cost
                                                FROM track t2 
                                                WHERE t2.frame = f2.frame
                                                ORDER BY cost ASC
                                                LIMIT 5
                                            ) C ON TRUE
                                            WHERE t1.frame = f1.frame) E on true
                                        WHERE f1.number = f2.number-1
                                        AND f1.segment = $1
                                        AND f2.segment = $1
                                        ORDER BY f1.number ASC
                                        """, segment['segment']):
                
                u1, v1 = "u_"+str(edges["tr1"]), "v_"+str(edges["tr1"])
                u2, v2 = "u_"+str(edges["tr2"]), "v_"+str(edges["tr2"])
                
            
                
                # create ui, create vi, create edge (ui, vi), cost CI(ui,vi), cap = 1
                if mcf_graph.add_node(u1):
                    mcf_graph.add_node(v1)
                    mcf_graph.add_edge(u1, v1, capacity=1, weight=Ci)
                    mcf_graph.add_edge("START", u1, capacity=1, weight=Cen)
                    mcf_graph.add_edge(v1, "END", capacity=1, weight=Cex)
                
                if mcf_graph.add_node(u2):
                    mcf_graph.add_node(v2)
                    mcf_graph.add_edge(u2, v2, capacity=1, weight=Ci)
                    mcf_graph.add_edge("START", u2, capacity=1, weight=Cen)
                    mcf_graph.add_edge(v2, "END", capacity=1, weight=Cex)
                
                # Cij = -Log(Plink(xi|xj)), Plink = Psize*Pposiiton*Pappearance*Ptime
                Cij = int(edges["cost"])
                
                mcf_graph.add_edge(v1, u2, weight=Cij, capacity=1)
            
        
            if mcf_graph.n_nodes == 2: # only START and END nodes present (empty)
                print("Nothing in segment")    
                continue
            demand = 300
            mcf_graph.set_demand(demand)
                
            print("Solving min-cost-flow.")    
            
            mcf_graph.solve()
            mcf_flow_dict = mcf_graph.flowdict()
            mcf_graph = None
            
            tracks = dict()
            for dest in mcf_flow_dict["START"]:
                new_particle_uuid = uuid4()
                track = []
                curr = dest
                while(curr != "END"):
                    if curr[0] == 'u':
                        old_particle_uuid = UUID(curr.split('_')[-1])
                        track.append(old_particle_uuid)
                    curr = mcf_flow_dict[curr][0]
                
                tracks[new_particle_uuid] = track
           
            print('tracks reconstructed', len(tracks))
            
            
            start = time.time()
            
    
            cnt=0
            for new_particle_uuid, track in tracks.items():
                mean_area = 0.0
                mean_intensity = 0.0
                mean_perimeter = 0.0
                mean_radius = 0.0
                category = []
                start = time.time()
                # insert particle
                await tx.execute("""
                    INSERT INTO Particle (particle, experiment)
                    VALUES ($1, $2)
                """, new_particle_uuid, new_experiment_uuid)
                
                
                
                # add the particle's tracks
                
                # query and avg based on a "group by" for ALL particles
                # BAM (except the category thing... thats not native)
                # Update category later.... ?
                
                # compute averages / insert tracks
                cnt+=1
                flag = 0
                start = time.time()
                
                
                async for data in tx.cursor("""SELECT * 
                                               FROM Frame
                                               LEFT JOIN Track
                                               USING(frame)
                                               LEFT JOIN Particle 
                                               USING(particle) 
                                               WHERE track = ANY($1::UUID[]) 
                                               AND frame.segment = $2
                                            """, 
                                            track, 
                                            segment['segment']):
                    if not flag:
                        # print('query', time.time()-start, end =' ')
                        flag +=1
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
                    start=time.time()
                    await tx.execute("""
                        INSERT INTO Track (track, frame, particle, location, bbox, latent)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, *new_track)
                    # print('track insert:', time.time()-start, end=' ')
                
                
                
                # update particle stats
                category = np.argmax(np.bincount(category))
                await tx.execute("""
                    UPDATE Particle
                    SET area = $1, intensity = $2, perimeter = $3, radius = $4, category = $5
                    WHERE particle = $6
                """, mean_area, mean_intensity, mean_perimeter, mean_radius, category, new_particle_uuid)
                
                print('particle insert:', cnt, time.time()-start, end=' ')
            
    
        
    except Exception as e: ### ERROR: UNDO EVERYTHING !    #################
        print("Uh oh. Something went wrong")
        traceback.print_exc()
        
        await transaction.rollback()
        
        if os.path.exists(new_experiment_dir):
            shutil.rmtree(new_experiment_dir)
        traceback.print_exc()
        
    
    else:  
    ##################  OK: COMMIT DB TRANSACTRION    ###############
        print('made it! :)')
        await transaction.commit()

        
    return new_experiment_uuid

    
async def clone_experiment(experiment_uuid, tx, testing=False):

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
    if not testing:
        os.mkdir(new_experiment_path)
    await tx.execute("""
            INSERT INTO Experiment (experiment, day, name, method, notes) 
            SELECT $1, day, name, 'tracking', notes FROM Experiment
            WHERE experiment = $2
            """, new_experiment_uuid, experiment_uuid)
    if not testing:
        for file in base_files:
            os.link(join(experiment_path, file), join(new_experiment_path, file))
        
    
        for old_frame_uuid, new_frame_uuid in frame_uuid_map.items():
            os.mkdir(join(new_experiment_path, str(new_frame_uuid)))
    
    
    segment_uuid_map = {}
    segment_insert = []
    async for s in tx.cursor("SELECT segment, number FROM Segment WHERE experiment = $1", experiment_uuid):
        segment_uuid = uuid4()
        segment_uuid_map[s["segment"]] = {"segment": segment_uuid, "number": s["number"]}
        segment_insert.append((segment_uuid, experiment_uuid, s["number"]))
    
    await tx.executemany("INSERT INTO Segment (segment, experiment, number) VALUES ($1, $2, $3)", segment_insert)
    
    frame_segment_map = {}
    async for f in tx.cursor("select frame, segment From Frame WHERE experiment = $1", experiment_uuid):
        frame_segment_map[f["frame"]] = segment_uuid_map[f["segment"]]["segment"]
    
    
    
    await tx.executemany("""
            INSERT INTO Frame (frame, experiment, segment, number) 
            SELECT $1, $2, $3, number FROM Frame
            WHERE frame = $4
            """, [(frame_uuid_map[UUID(frame)], new_experiment_uuid, frame_segment_map[UUID(frame)], UUID(frame)) for frame in frames])
    
    if not testing:
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
    super-source/super-sink 'START'/'END', 
    and will be assigned demand and -demand respectively.
    
    Simplified for our purposes, the capacity will always have
    a lower bound zero, and can not be set explicitly.
    '''
    def __init__(self, verbose=True):
        self.nodes = dict()
        self.edges = []
        self.n_nodes = 0
        self.n_edges = 0
        self.demand = 0
        self.verbose = verbose
        
    def add_node(self, k):
        '''
        expects uuid
        pyMCFSimplex node names {1,2,...,n}
        returns true if the node was added, false
        if the node was added prior.
        '''
        if not k in self.nodes:
            self.nodes[k] = self.n_nodes+1
            self.nodes[self.n_nodes+1] = k
            self.n_nodes += 1
            return True
        else:
            return False
        
    def add_edge(self, start, end, capacity, weight):
        '''
        expects uuid start/end nodes
        '''
        self.edges.append((self.nodes[start], 
                           self.nodes[end], 
                           0, 
                           capacity,
                           weight))
        self.n_edges += 1
        
    def remove(self, k):
        self.d.pop(self.d.pop(k))
        
    def get_node(self, k):
        '''
        given an integer returns {'u_', 'v_'}+str(UUID)
        given {'u_', 'v_'}+str(UUID) returns integer
        '''
        
        if isinstance(k, int):
            return self.nodes[k]
        else:
            return self.nodes[k]
        
    def set_demand(self, demand):
        '''
        sets the "START"/"END" demand, 
        '''
        self.demand = demand
        
    def write(self, file):
        '''
        writes graph to file for input to pyMCFSimplex
        '''
        file.write('p min %s %s\n' % (self.n_nodes, self.n_edges))
        file.write('n %s %s\n' % (self.nodes['START'], self.demand,))
        file.write('n %s %s\n' % (self.nodes['END'], -self.demand,))
        
        for (start, end, low, high, weight) in self.edges:
            file.write('a %s %s %s %s %s\n' % (start, end, low, high, weight))

    def solve(self):
        self.mcf = pyMCFSimplex.MCFSimplex()
        fp = tempfile.TemporaryFile('w+')
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
                print("Optimal solution: %s" %self.mcf.MCFGetFO())
                print("Time elapsed: %s sec " %(self.mcf.TimeMCF()))
            return min_cost
        else:
            if self.verbose:
                print("Problem unfeasible!")
                print("Time elapsed: %s sec " %(self.mcf.TimeMCF()))
            raise Exception('Network Unfeasible')
        
    def flowdict(self):
        mcf_flow_dict = dict()
        # Build flowdict
        # BEGIN FROM EXAMPLE
        mmx     = self.mcf.MCFmmax()
        pSn     = []
        pEn     = []
        startNodes = pyMCFSimplex.new_uiarray(mmx)
        endNodes = pyMCFSimplex.new_uiarray(mmx)
        self.mcf.MCFArcs(startNodes,endNodes)
        
        for i in range(0,mmx):
           pSn.append(pyMCFSimplex.uiarray_get(startNodes,i)+1)
           pEn.append(pyMCFSimplex.uiarray_get(endNodes,i)+1)
    
        length = self.mcf.MCFm()
    
        cost_flow = pyMCFSimplex.new_darray(length)
        self.mcf.MCFGetX(cost_flow)
        # END FROM EXAMPLE
        
        for i in range(0,length):
            startNode   = pSn[i]
            endNode     = pEn[i]
            flow        = pyMCFSimplex.darray_get(cost_flow,i)
            
            if flow > 0:
                if not self.get_node(startNode) in mcf_flow_dict:
                    mcf_flow_dict[self.get_node(startNode)] = []
                mcf_flow_dict[self.get_node(startNode)].append(self.get_node(endNode))
                # print("Flow on arc %s from node %s to node %s: %s " %(i,startNode,endNode,flow,))
        return mcf_flow_dict

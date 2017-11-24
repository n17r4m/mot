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
from scipy.optimize import golden

import time

from uuid import uuid4, UUID

import pyMCFSimplex


async def main(args):
    
    if len(args) < 1: 
        
        print("What you want to track?")
        print("USING: experiment-uuid [method]")
    else:
        start = time.time()
        print(await track_experiment(*args))
        print('Total time:',time.time()-start)

async def track_experiment(experiment_uuid, method='Tracking'):
    '''
    
    '''
    cpus = multiprocessing.cpu_count()
    loop = asyncio.get_event_loop()
    db = Database()
    # Clone the experiment
    
    try:
        start = time.time()
        tx, transaction = await db.transaction()
        new_experiment_uuid, frame_uuid_map, track_uuid_map = await clone_experiment(experiment_uuid, tx, testing=False, method=method)
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
            costs = []
            
            async for edges in db.query("""
                                        SELECT f1.frame as fr1, f2.frame as fr2, tr1, tr2, cost, location1, bbox1, latent1, area1, intensity1, radius1, perimeter1, category1, location2, bbox2, latent2, area2, intensity2, radius2, perimeter2, category2
                                        FROM frame f1, frame f2, segment s
                                        JOIN LATERAL (
                                            SELECT t1.track AS tr1, tr2, cost, t1.location as location1, t1.bbox as bbox1, t1.latent as latent1, p1.area as area1, p1.intensity as intensity1, p1.radius as radius1, p1.perimeter as perimeter1, p1.category as category1, location2, bbox2, latent2, area2, intensity2, radius2, perimeter2, category2
                                            FROM track t1
                                            LEFT JOIN Particle p1 USING(Particle)
                                            JOIN LATERAL (
                                                SELECT 
                                                    t2.track AS tr2, t2.location as location2, t2.bbox as bbox2, t2.latent as latent2, p2.area as area2, p2.intensity as intensity2, p2.radius as radius2, p2.perimeter as perimeter2, p2.category as category2,
                                                    ((1 + (t1.latent <-> t2.latent))
                                                    *(1 + (t1.location <-> t2.location))) AS cost
                                                FROM track t2
                                                LEFT JOIN Particle p2 USING(Particle)
                                                WHERE t2.frame = f2.frame
                                                ORDER BY cost ASC
                                                LIMIT 5
                                            ) C ON TRUE
                                            WHERE t1.frame = f1.frame) E on true
                                        WHERE f1.number = f2.number-1
                                        AND f1.segment = $1
                                        AND f2.segment = $1
                                        AND s.segment = f1.segment
                                        AND s.number >= 0
                                        ORDER BY f1.number ASC
                                        """, segment['segment']):
                if  edges['tr1'] not in edge_data:
                    edge_data[edges['tr1']] = {'track': edges['tr1'],
                                               'frame': edges['fr1'],
                                               'location': edges['location1'],
                                               'bbox': edges['bbox1'],
                                               'latent': edges['latent1'],
                                               'area': edges['area1'],
                                               'intensity': edges['intensity1'],
                                               'radius': edges['radius1'],
                                               'perimeter': edges['perimeter1'],
                                               'category': edges['category1']
                                              }
                edge_data[edges['tr2']] = {'track': edges['tr2'],
                                           'frame': edges['fr2'],
                                           'location': edges['location2'],
                                           'bbox': edges['bbox2'],
                                           'latent': edges['latent2'],
                                           'area': edges['area2'],
                                           'intensity': edges['intensity2'],
                                           'radius': edges['radius2'],
                                           'perimeter': edges['perimeter2'],
                                           'category': edges['category2']
                                          }                                          
                
                u1, v1 = "u_"+str(edges["tr1"]), "v_"+str(edges["tr1"])
                u2, v2 = "u_"+str(edges["tr2"]), "v_"+str(edges["tr2"])
                

                
                # create ui, create vi, create edge (ui, vi), cost CI(ui,vi), cap = 1
                if mcf_graph.add_node(u1):
                    mcf_graph.add_node(v1)
                    
                    # Heuristic reward for larger, darker; penalize undefined
                    larger = 500
                    darker = 0
                    area = edge_data[edges["tr1"]]["area"] 
                    intensity = edge_data[edges["tr1"]]["intensity"]
                    nodeCi = Ci * (1 + (area / larger) * ((255-intensity) / 255))
                    # if not edge_data[edges["tr1"]]["category"]:
                        # nodeCi = 10
                    # End heuristic reward
                    
                    mcf_graph.add_edge(u1, v1, capacity=1, weight=int(nodeCi))
                    mcf_graph.add_edge("START", u1, capacity=1, weight=Cen)
                    mcf_graph.add_edge(v1, "END", capacity=1, weight=Cex)
                
                if mcf_graph.add_node(u2):
                    mcf_graph.add_node(v2)
                    
                    # Heuristic reward for larger, darker; penalize undefined
                    larger = 500
                    darker = 0
                    area = edge_data[edges["tr2"]]["area"] 
                    intensity = edge_data[edges["tr2"]]["intensity"]
                    nodeCi = Ci * (1 + (area / larger) * ((255-intensity) / 255))
                    # if not edge_data[edges["tr1"]]["category"]:
                        # nodeCi = 10
                    # End heuristic reward
                    
                    mcf_graph.add_edge(u2, v2, capacity=1, weight=int(nodeCi))
                    mcf_graph.add_edge("START", u2, capacity=1, weight=Cen)
                    mcf_graph.add_edge(v2, "END", capacity=1, weight=Cex)
                
                # Cij = -Log(Plink(xi|xj)), Plink = Psize*Pposiiton*Pappearance*Ptime
                Cij = int(edges["cost"])
                costs.append(Cij)
                mcf_graph.add_edge(v1, u2, weight=Cij, capacity=1)
            
        
            if mcf_graph.n_nodes == 2: # only START and END nodes present (empty)
                print("Nothing in segment")    
                continue
            # print("nodes:", mcf_graph.n_nodes)
            # print("min cost", np.min(costs))
            # print("average cost", np.average(costs))
            # print("max cost", np.max(costs))
            print("Solving min-cost-flow for segment")

            demand = goldenSectionSearch(mcf_graph, 0, mcf_graph.n_nodes//4, mcf_graph.n_nodes, 2, memo=None)
            # (min_cost, demand, nEval) = golden(mcf_graph.solve, 
            #                                   (), 
            #                                   brack=(0,512,2048), 
            #                                   tol=10, 
            #                                   full_output=True)
            
            print("Optimal number of tracks", demand)
            min_cost = mcf_graph.solve(demand)
            print("Min cost", min_cost)
            
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
           
            print('Tracks reconstructed', len(tracks))
            
            
            start = time.time()
            particle_inserts = []
            track_inserts = []
            for new_particle_uuid, track in tracks.items():
                mean_area = 0.0
                mean_intensity = 0.0
                mean_perimeter = 0.0
                mean_radius = 0.0
                category = []
                
                for data in [edge_data[i] for i in track]:
                    mean_area += data["area"] / len(track)
                    mean_intensity += data["intensity"] / len(track)
                    mean_perimeter += data["perimeter"] / len(track)
                    mean_radius += data["radius"] / len(track)
                    category.append(data["category"])
                    
                    new_frame_uuid = frame_uuid_map[data["frame"]]
                    new_track_uuid = track_uuid_map[data["track"]]
                    
                    track_inserts.append((new_track_uuid,
                                         new_frame_uuid,
                                         new_particle_uuid,
                                         data["location"],
                                         data["bbox"],
                                         data["latent"]))

                category = np.argmax(np.bincount(category))
                particle_inserts.append((new_particle_uuid, new_experiment_uuid, mean_area, mean_intensity, mean_perimeter, mean_radius, category))
                
            await tx.executemany("""
                INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                VALUES ($1, $2, $3, $4 ,$5, $6, $7)
            """, particle_inserts)
            
            await tx.executemany("""
                INSERT INTO Track (track, frame, particle, location, bbox, latent)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, track_inserts)
                
            print('Tracks inserted', time.time()-start, 's')

        
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

    
async def clone_experiment(experiment_uuid, tx, method, testing=False):

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
            SELECT $1, day, name, $3, notes FROM Experiment
            WHERE experiment = $2
            """, new_experiment_uuid, experiment_uuid, method)
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
        segment_insert.append((segment_uuid, new_experiment_uuid, s["number"]))
    
    # Create null segment for frames with no segment.
    # A workaround until segment is improved
    segment_uuid = uuid4()
    segment_uuid_map[None] = {"segment": segment_uuid, "number": -1}
    segment_insert.append((segment_uuid, new_experiment_uuid, -1))
    
    
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
    def __init__(self, verbose=False):
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
        
    def write(self, file):
        '''
        writes graph to file for input to pyMCFSimplex
        '''
        file.write('p min %s %s\n' % (self.n_nodes, self.n_edges))
        file.write('n %s %s\n' % (self.nodes['START'], self.demand,))
        file.write('n %s %s\n' % (self.nodes['END'], -self.demand,))
        
        for (start, end, low, high, weight) in self.edges:
            file.write('a %s %s %s %s %s\n' % (start, end, low, high, weight))

    def solve(self, demand):
        self.demand = demand
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
            return float('inf')
        
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

phi = (1 + np.sqrt(5))/2
resphi = 2 - phi
# a and b are the current bounds; the minimum is between them.
# c is the center pointer pushed slightly left towards a
def goldenSectionSearch(f, a, c, b, absolutePrecision, memo=None):
    if memo is None:
        memo = dict()
        
    if abs(a - b) < absolutePrecision:
        return int((a + b)/2)
    # Create a new possible center, in the area between c and b, pushed against c
    d = int(c + resphi*(b - c))
    
    
    if d in memo:
        f_d = memo[d]
    else:
        f_d = f.solve(d)
        memo[d] = f_d
        # print(d, f_d)
        
    if c in memo:
        f_c = memo[c]
    else:
        f_c = f.solve(c)
        memo[c] = f_c    
        # print(c, f_c)
        
    if f_d < f_c:
        return goldenSectionSearch(f, c, d, b, absolutePrecision, memo)
    else:
        return goldenSectionSearch(f, d, c, a, absolutePrecision, memo)

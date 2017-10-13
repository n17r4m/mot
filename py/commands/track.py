

import config


from lib.Database import Database

import numpy as np
import networkx as nx

import traceback
import multiprocessing
import subprocess
import threading
import concurrent.futures

import queue
import asyncio


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
    
    
    async for experiment in db.query("SELECT * FROM Experiment WHERE experiment = $1", experiment_uuid):
        
        pg, transaction = await db.transaction()
        
        G = nx.DiGraph()
        G.add_node("START", demand=-150)
        G.add_node("END", demand=150)
        
        
        frame_costs = []
        
        top_costs = [[], [], [], [], []]
        
        
        frame1 = None
        
        
        
        
        async for frame2 in db.query("SELECT * FROM Frame WHERE experiment = $1 ORDER BY number ASC ", experiment["experiment"]):
            if frame1 is None: 
                frame1 = frame2;
                async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame1["frame"]):
                    G.add_edge("START", str(track["track"]), capacity=1)
                continue;
            
            frame_cost = 0
            print(frame1["frame"], frame1["number"])
            
            async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame1["frame"]):
            
                #print(track["track"])
                top = 0
                
                
                async for candidate in db.query("""
                    SELECT track, 
                          ((1 + cube_distance(latent, $2))
                        * (1 + ABS(location[0] - $3))
                        * (1 + ABS(location[1] - $4))
                        * (1 + ABS(area - $5))
                        * (1 + ABS(intensity - $6))
                        * (1 + ABS(perimeter - $7))
                        * (1 + (10 * BOOL(category - $8)::INTEGER))) AS cost
                    FROM Track LEFT JOIN Particle USING(particle) 
                    WHERE frame = $1 
                    ORDER BY cost ASC 
                    LIMIT 5
                    """, frame2["frame"], track["latent"], track["location"][0], track["location"][1], track["area"], track["intensity"], track["perimeter"], track["category"]):
                    
                    if top == 0:
                        frame_cost += candidate["cost"]
                    
                    
                    
                    top_costs[top].append(candidate["cost"])
                    top += 1
                    
                    #print(candidate)
                    
                    G.add_edge(str(track["track"]), str(candidate["track"]), weight=int(candidate["cost"]), capacity=1)
                    
                """
                This seems to slow down things a lot. maybe use a hot-cache lookup?
                if len(nx.ancestors(G, str(track["track"]))) == 0:
                    G.add_edge("START", str(track["track"]), capacity=1)
                
                G.add_edge(str(track["track"]), "END", capacity=1)
                """ 
                    
            
            
            
            
            """
            Example one:
            ae800a5e-d985-4a0e-8bfe-d50a13ab770c
            <Record track=UUID('f10abc00-79e9-4db6-b4ad-31fd8dd5f5aa') cost=5.8678526183297395>
            <Record track=UUID('a8d356ff-914e-4207-a815-f3c657c358e4') cost=2028595.2226618128>
            <Record track=UUID('f16d96cc-b50e-4979-8f05-0a7e0f956a8d') cost=4334082.638343262>
            <Record track=UUID('3995107c-8114-44d8-b2a9-eef591e53f3d') cost=7407534.280565019>
            <Record track=UUID('4be8e602-b3b1-4fb9-a645-f781f02a3cab') cost=7977970.845299974>
            
            Example two:
            6900d1fb-6c85-40a2-b819-19ff98c0f9c9
            <Record track=UUID('14dd46b8-fdd0-476e-b348-9d70d2192c33') cost=16.62705296523085>
            <Record track=UUID('1cc6ab9d-ceed-4730-a18a-e67fcae2ba2a') cost=7804459.600819013>
            <Record track=UUID('134adf1b-103f-4e24-85a5-e1efa82d3ee6') cost=9586882.640224773>
            <Record track=UUID('c119f490-fe66-4dd8-b57c-d4d30d6aeba3') cost=9639379.349052807>
            <Record track=UUID('70a5a15a-8c61-43ff-bcdf-6249797cb3fd') cost=10741994.296600373>
            """
            
            frame_costs.append(frame_cost)
            
            frame1 = frame2
            #endof track
            
           
        
        async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame2["frame"]):
            G.add_edge(str(track["track"]), "END", capacity=1)
        
        
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
        
        
        mflow = nx.maximum_flow(G, "START", "END")
        
        print(mflow[0])
        
        G.node["START"]["demand"] = -mflow[0]
        G.node["END"]["demand"] = mflow[0]
        
        nx.write_graphml(G, "test.graphml")
        
        
        min_cost, flow_dict = nx.network_simplex(G)
        
        for u in flow_dict:
            print(u, flow_dict[u])
        print(min_cost)
        
        
        mu = np.median(top_costs, axis=1)
        std = np.std(top_costs, axis=1)
        
        print(len(top_costs[0]))
        print(mu)
        print(std)
        
        
        """
        what is the sample size... n = ?
        [  1.18161018e+02   1.96167244e+06   5.58250181e+06   9.68133977e+06  1.46586190e+07]
        [  3.78273080e+07   4.08500494e+08   9.72344528e+08   1.52232527e+09  2.05291818e+09]
        """
        
        
        #print(frame_costs)
        
        
    return "Complete."
    """
    async for next_frame in db.query("")
        
    async for track in db.query("SELECT * FROM Track LEFT JOIN Particle USING(particle) WHERE frame = $1", frame["frame"]):
            
        print(track)
            
    """     
    
    
    
    
"""
DESCRIPTION

USING

As a command line utility

$ 

As a module

import 

Author: Kevin Gordon
"""
import cv2
import numpy as np
from argparse import ArgumentParser
from DataBag import DataBag
from Query import Query
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import time
import json
import matplotlib.pyplot as plt

# try:
#     import keras
# except ImportError:
#     print "System is not configured for Keras, Tracker V3 will not work correctly..."

class Tracker(object):

    def __init__(self, component_data, filt, burst, fg, verbose=False, bagName=":memory:"):
        self.G = nx.DiGraph()
        self.component_data = component_data
        self.filt = filt
        self.burst = burst
        self.fg = fg
        self.no_frames = len(burst)
        self.verbose = verbose
        self.bagName = bagName

    def build(self, similarity_map=None):
        self.similarity_map = similarity_map
        self.G.add_node('s')
        self.G.add_node('t')

        start = time.time()

        # Detector error rate
        #  Cost for an object to go from frame i to frame i+1
        beta = 0.03
        C_i = 10

        # Cost for object entering frame
        # C_en = -np.log(eps)
        C_en_factor = 10 # some multiplier
        C_en_ratio = 20 # roughly the expected number to stay in frame to entering/exiting

        # Cost for object exiting frame
        # C_ex = -np.log(eps)
        C_ex_factor = 10
        C_ex_ratio = 20

        # For every detected object x_i
        for i in range(self.no_frames):
            for j in self.filt[i]:
                L, T, W, H, A = self.component_data['comp'][i][j]
                centre = self.component_data['cent'][i][j]
                u = 'u_'+str(i)+'_'+str(j)
                v = 'v_'+str(i)+'_'+str(j)


                crop = self.fg[i][T:T+H,L:L+W]
                mask = self.component_data['img'][i][T:T+H,L:L+W]
                intensity = float(np.sum(crop[mask==j]) / A)

                #  create two nodes u_i v_i
                self.G.add_node(u, area=float(A), centre=centre, intensity=intensity)
                self.G.add_node(v, area=float(A), centre=centre, intensity=intensity)

                #  create edge (u_i, v_i)
                #   with cost c(u_i, v_i) = C_i
                #   and flow f(u_i, v_i) = f_i
                self.G.add_edge(u, v, weight=C_i, capacity=1)

                #  create edge (s, u_i)
                #   with cost c(s, u_i) = C_en,_i
                #   and flow f(s, u_i) = f_en,_i
                C_en = i * C_en_factor * C_en_ratio
                self.G.add_edge('s', u, weight=C_en, capacity=1)

                #  create and edge (v_i, t)            
                #   with cost c(v_i, t) = C_ex,_i
                #   and flow f(v_i, t) = f_ex,_i
                C_ex = (self.no_frames-i-1) * C_ex_factor * C_ex_ratio
                self.G.add_edge(v, 't', weight=C_ex, capacity=1)
                # G.add_edge(u, 't', weight=C_ex, capacity=1)

        if self.verbose:
            print "graph nodes created ..."
            print "sink and source edges connected ...", str(time.time()-start), ' seconds'
            start = time.time()

        # For every transition P_link(x_j|x_i) != 0
        for i in range(self.no_frames-1):
            for j in self.filt[i]:
                for k in self.filt[i+1]:
                    v = 'v_'+str(i)+'_'+str(j)                
                    # v = 'u_'+str(i)+'_'+str(j)
                    u = 'u_'+str(i+1)+'_'+str(k)

                    # Pruning step, returns True to prune (skip adding)                
                    if self.prune(u, v):
                        continue

                    #  create edge (v_i, u_j)
                    #   with cost c(v_i, u_j) = C_i,_j
                    #   and flow f(v_i, u_j) = f_i,_j
                    C_i_j = self.get_cost(v, u)
                    self.G.add_edge(v, u, weight=C_i_j, capacity=1)

        if self.verbose:
            print "graph construction complete ...", str(time.time()-start), ' seconds'

    def solve(self, no_tracks):
        self.no_tracks = no_tracks
        # Compute the min cost and retrieve flows
        start = time.time()

        self.G.node['s']['demand'] = -no_tracks
        self.G.node['t']['demand'] = no_tracks
        try:
            self.min_cost, self.flowDict = nx.network_simplex(self.G)
        except nx.NetworkXUnfeasible:
            self.flowDict = {'s':{}}
            print "No flow satisfies constraints ..."


        if self.verbose:
            print "min cost flow computed ...", str(time.time()-start), ' seconds'

    def reconstruct_paths(self):
        start = time.time()
        # Reconstruct paths
        self.paths = []
        self.full_paths = []
        self.path_costs = []

        for k,v in self.flowDict['s'].iteritems():        
            if v:
                self.path_costs.append([self.G.edge['s'][k]['weight']])
                self.full_paths.append([])
                buf = []
                curr = k
                buf.append(curr)            
                while (curr != 't'):
                    for k,v in self.flowDict[curr].iteritems():
                        if v:
                            cost = self.G.edge[curr][k]['weight']
                            self.path_costs[-1].append(cost)
                            self.full_paths[-1].append(curr)
                            curr = k

                            if curr[0] != 'v':
                                buf.append(curr)
                            break
                # take off that sink node
                if len(buf)==3:
                    print buf

                # _ = buf.pop()
                _ = buf.pop()

                if len(buf)==1 or len(buf) ==0:                    
                    continue

                self.paths.append(buf)

        if self.verbose:
            print "paths reconstructed ...", str(time.time()-start), ' seconds'
            print "reconstructed ", str(len(self.paths)), " paths"

    def draw_paths(self):
        start = time.time()
        # Draw paths on video
        self.result_img = [cv2.cvtColor(i, cv2.COLOR_GRAY2RGB) for i in self.burst]
        for path in self.paths:
            for j in range(len(path)-1):
                burst_idx = int(path[j].split('_')[1])
                compondent_idx1 = int(path[j].split('_')[2])
                compondent_idx2 = int(path[j+1].split('_')[2])
                centre1 = self.component_data['cent'][burst_idx][compondent_idx1]
                centre2 = self.component_data['cent'][burst_idx+1][compondent_idx2]
                L, T, W, H, A = self.component_data['comp'][burst_idx][compondent_idx1]

                centre1 = (int(round(centre1[0])), 
                          int(round(centre1[1])))
                centre2 = (int(round(centre2[0])), 
                          int(round(centre2[1])))

                line_width = 1
                if A > 50:
                    line_width = 2
                elif A > 100:
                    line_width = 3
                elif A > 500:
                    line_width = 4

                for k in range(self.no_frames):
                    if j == self.no_frames-2:
                        cv2.arrowedLine(self.result_img[k], centre1, centre2, (0,255,0), line_width)
                    else:
                        cv2.line(self.result_img[k], centre1, centre2, (255-burst_idx*255/self.no_frames, burst_idx*255/self.no_frames,0), line_width)

        if self.verbose:
            print "paths drawn ...", str(time.time()-start), ' seconds'


        return self.result_img

    def save_paths(self, filename):
        self.bag = DataBag(self.bagName, verbose=True)

        self.ground_truth = [{'frames':[], 'class':'video', 'filename': str(filename)}]

        for i in range(self.no_frames):
            self.bag.insertFrame(i+1)            
            self.ground_truth[0]["frames"].append({'timestamp':i, 'num': i, 'class':'frame', 'hypotheses':[]})

        last_pid = self.bag.query('select max(particle) from assoc')[0][0]
        if last_pid is None:
            pid = 0
        else:
            pid = last_pid + 1
            
        for path in self.paths:
            mean_area = 0

            for j in range(len(path)):
                burst_idx = int(path[j].split('_')[1])
                compondent_idx = int(path[j].split('_')[2])
                centre = self.component_data['cent'][burst_idx][compondent_idx]
                L, T, W, H, A = self.component_data['comp'][burst_idx][compondent_idx]

                mean_area += A / len(path)

                x,y = centre[0], centre[1]

                # x,y = int(round(centre[0])), int(round(centre[1]))

                self.ground_truth[0]['frames'][burst_idx]['hypotheses'].append({'dco': False,
                                                                                'height': int(H),
                                                                                'width': int(W),
                                                                                'id': pid,
                                                                                'y': y,
                                                                                'x': x})

                self.bag.insertAssoc(burst_idx+1, pid, x, y)

            self.bag.insertParticle(mean_area, pid)

            pid += 1

        with open(str(filename)+'.json', 'w') as outfile:
            json.dump(self.ground_truth, outfile)


    def is_bitumen(self, u):
        threshold = 110
        return self.G.node[u]['intensity'] < threshold

    def prune_transmission(self ,u, v):
        return False
        return self.is_bitumen(self.G,u) ^ self.is_bitumen(self.G,v)

    def prune_size(self, u, v):
        # This should be based on some statistics of the size variation
        # eg. prune anything > | +/- 3 std dev |
        threshold = 0.3
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            den = float(self.G.node[u]['area'])
            num = float(self.G.node[v]['area'])
        else:
            den = float(self.G.node[v]['area'])
            num = float(self.G.node[u]['area'])

        # print num/den
        if num/den < threshold:
            return True
        else:
            return False

    def prune_appearance(G, u, v):
        return self.prune_transmission(G, u, v) or self.prune_size(G, u, v)

    def euclidD(self, point1, point2):
        '''
        Computes the euclidean distance between two points and 
        returns this distance.
        '''
        sum = 0
        for index in range(len(point1)):
            diff = (point1[index]-point2[index]) ** 2
            sum = sum + diff

        return np.sqrt(sum)

    def prune_motion(self, u, v):
        return self.prune_velocity(u,v)

    def prune_velocity(self, u, v):
        # perhaps confusingly, velocity pruning considers
        #  the position of a node, and prunes nodes outside
        #  a defined radius. This should be based on some statistics...
        threshold = 100
        if self.euclidD(self.G.node[u]['centre'], self.G.node[v]['centre']) > threshold:
            return True
        else:
            return False

    def prune(self, u, v):
        # prune_size(G, u, v) or \
        #prune_transmission(G, u, v) or \
        return self.prune_velocity(u,v)
        
    def similarity_size(self, u, v):
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            similarity = self.G.node[v]['area'] / self.G.node[u]['area']
        else:
            similarity = self.G.node[u]['area'] / self.G.node[v]['area']
        return similarity

    def similarity_transmission(self, u, v):
        if self.G.node[u]['intensity'] > self.G.node[v]['intensity']:
            similarity = self.G.node[v]['intensity'] / self.G.node[u]['intensity']        
        else:
            if self.G.node[v]['intensity'] == 0:
                similarity = 1
            else:
                similarity = self.G.node[u]['intensity'] / self.G.node[v]['intensity']
        return similarity

    def similarity_appearance(self, u, v):
        if self.similarity_map:
            pass
        else:
            w1 = 0.8
            w2 = 0.2
            return w1*self.similarity_size(u, v) + w2*self.similarity_transmission(u, v)

    def similarity_motion(self, u, v):
        return 0.0

    def similarity(self, u, v):
        w1 = 1.0
        w2 = 0.0
        return w1*self.similarity_appearance(u, v) + w2*self.similarity_motion(u, v) 

    def get_cost(self, u, v):
        w1 = 0.45#similarity 
        w2 = 0.35#distance - prefer closer
        w3 = 0.05#intensity - prefer darker
        w4 = 0.15#size - prefer bigger
        scale = 1000
        distance = self.euclidD(self.G.node[u]['centre'], self.G.node[v]['centre'])
        # what is the magic number for prune_velocity, ensure they match
        distance_prune = 100
        bigger = 100
        area = self.G.node[u]['area']
        intensity = self.G.node[u]['intensity']

        return int(w1*scale*( 1 - (self.similarity(u, v)) )) + \
               int(w2*scale*( distance / distance_prune )) + \
               int(w3*scale*( intensity/255 )) + \
               int(w4*scale*( max(bigger-area,0) / bigger ))
    
##
# Tracker V2 uses the Databag for loading/storing detection/tracking results
##
class TrackerV2(object):

    def __init__(self, bag, verbose=False):
        self.G = nx.DiGraph()
        self.verbose = verbose
        self.bag = bag
        self.areas = []

        # for debugging
        self.total_edges_considered = 0
        self.pruned_edges = 0

    def build(self, start_frame, end_frame):
        self.G.clear()
        self.G.add_node('s')
        self.G.add_node('t')

        self.start_frame = start_frame
        self.end_frame = end_frame

        self.no_frames = end_frame - start_frame

        start = time.time()

        # Detector error rate
        #  Cost for an object to go from frame i to frame i+1
        beta = 0.03
        C_i = 0

        # Cost for object entering frame
        # C_en = -np.log(eps)
        C_en_factor = 200 # some multiplier

        # Cost for object exiting frame
        # C_ex = -np.log(eps)
        C_ex_factor = 200

        ### Get ALL particles
        # particles = self.bag.query('select id, frame, area, intensity, x, y \
        #     from particles, assoc where particles.id == assoc.particle and \
        #     frame >= ' + str(start_frame) + ' and frame < ' + str(end_frame))
        # all_particles = particles


        ### Get TOP N particles in a bag by: area desc
        n = 200

        # Store the results frame-wise, as list of lists
        particles = []

        for i in range(start_frame, end_frame):
            buf = self.bag.query('select id, frame, area, intensity, x, y \
            from particles, assoc where particles.id == assoc.particle and \
            frame == ' + str(i) + ' order by area desc limit ' + str(n))

            particles.append(buf)

        # Get the single list of all particles
        # all_particles = [item for sublist in particles for item in sublist]
        all_particles = []
        for l in particles:
            all_particles.extend(l)

        # For every detected object x_i
        for particle in all_particles:
            pid, frame, area, intensity, x, y = particle
            centre = (x, y)

            u = 'u_' + str(pid)
            v = 'v_' + str(pid)

            #  create two nodes u_i v_i
            self.G.add_node(u, area=float(area), centre=centre, intensity=intensity, frame=frame)
            self.G.add_node(v, area=float(area), centre=centre, intensity=intensity, frame=frame)

            #  create edge (u_i, v_i)
            #   with cost c(u_i, v_i) = C_i
            #   and flow f(u_i, v_i) = f_i
            self.G.add_edge(u, v, weight=C_i, capacity=1)

            #  create edge (s, u_i)
            #   with cost c(s, u_i) = C_en,_i
            #   and flow f(s, u_i) = f_en,_i
            C_en = frame * C_en_factor 
            self.G.add_edge('s', u, weight=C_en, capacity=1)

            #  create and edge (v_i, t)            
            #   with cost c(v_i, t) = C_ex,_i
            #   and flow f(v_i, t) = f_ex,_i
            C_ex = (self.no_frames-frame-1) * C_ex_factor
            self.G.add_edge(v, 't', weight=C_ex, capacity=1)
            # G.add_edge(u, 't', weight=C_ex, capacity=1)

 
        if self.verbose:
            print "graph nodes created ..."
            print "sink and source edges connected ...", str(time.time()-start), ' seconds'
            start = time.time()

        # For every transition P_link(x_j|x_i) != 0
        for i in range(0, end_frame - start_frame - 1):
            ### Get ALL particles in a particular frame            
            # v_ids = self.bag.query('select id from particles, assoc \
            #     where particles.id == assoc.particle \
            #     and frame == ' + str(i))
            # u_ids = self.bag.query('select id from particles, assoc \
            #     where particles.id == assoc.particle \
            #     and frame == ' + str(i+1))

            ### Get TOP N particles in a frame, using our earlier query
            v_ids = particles[i]
            u_ids = particles[i+1]

            for j in v_ids:
                for k in u_ids:
                    v = 'v_' + str(j[0])
                    u = 'u_' + str(k[0])

                    # Pruning step, returns True to prune (skip adding) 
                    self.total_edges_considered += 1            
                    if self.prune(u, v):
                        self.pruned_edges += 1
                        continue

                    #  create edge (v_i, u_j)
                    #   with cost c(v_i, u_j) = C_i,_j
                    #   and flow f(v_i, u_j) = f_i,_j
                    C_i_j = self.get_cost(v, u)
                    self.G.add_edge(v, u, weight=C_i_j, capacity=1)

        if self.verbose:
            print "graph construction complete ...", str(time.time()-start), ' seconds'

    def solve(self, no_tracks):
        self.no_tracks = no_tracks
        # Compute the min cost and retrieve flows
        start = time.time()

        self.G.node['s']['demand'] = -no_tracks
        self.G.node['t']['demand'] = no_tracks
        try:
            self.min_cost, self.flowDict = nx.network_simplex(self.G)
        except nx.NetworkXUnfeasible:
            self.flowDict = {'s':{}}
            print "No flow satisfies constraints ..."


        if self.verbose:
            print "min cost flow computed ...", str(time.time()-start), ' seconds'

    def reconstruct_paths(self):
        start = time.time()
        # Reconstruct paths
        self.paths = []
        self.full_paths = []
        self.path_costs = []

        for k,v in self.flowDict['s'].iteritems():        
            if v:
                self.path_costs.append([self.G.edge['s'][k]['weight']])
                self.full_paths.append([])
                buf = []
                curr = k
                buf.append(curr)            
                while (curr != 't'):
                    for k,v in self.flowDict[curr].iteritems():
                        if v:
                            cost = self.G.edge[curr][k]['weight']
                            self.path_costs[-1].append(cost)
                            self.full_paths[-1].append(curr)
                            curr = k

                            if curr[0] != 'v':
                                buf.append(curr)
                            break
                # take off that sink node

                if len(buf)==3:
                    pass
                    # print buf

                # _ = buf.pop()
                _ = buf.pop()

                if len(buf)==1 or len(buf) ==0:
                    continue

                self.paths.append(buf)

        if self.verbose:
            print "paths reconstructed ...", str(time.time()-start), ' seconds'
            print "reconstructed ", str(len(self.paths)), " paths"


    def save_paths(self, filename):
        self.out_bag = DataBag(filename, verbose=True)
        # used to test a hypothesis regarding particle areas over time/ camera problems
    
        last_pid = self.out_bag.query('select max(particle) from assoc')[0][0]
        if last_pid is None:
            pid = 0
        else:
            pid = last_pid + 1

        for i in range(self.start_frame, self.end_frame):
            d = {'number':i}
            self.out_bag.insertFrame(d)        

        for path in self.paths:
            mean_area = 0.0
            mean_intensity = 0.0
            mean_perimeter = 0.0

            # ### BEGIN OLD ###
            # # I think this loop can be optimized with an "IN" query and 
            # #  vector computation of the means
            # for pid in path:
            #     pid = pid.split('_')[1]
            #     res = self.bag.query('select frame, x, y, area, intensity, perimeter\
            #                               from assoc, particles\
            #                               where assoc.particle == particles.id\
            #                               and particles.id == ' + str(pid) \
            #                               + ' and assoc.frame < ' + str(self.end_frame) \
            #                               + ' and assoc.frame >= ' + str(self.start_frame))[0]

            #     frame, x, y, area, intensity, perimeter = res

            #     mean_area += area / len(path)
            #     mean_intensity += intensity / len(path)
            #     mean_perimeter += perimeter / len(path)

            #     self.out_bag.batchInsertAssoc(frame, self.new_pid, x, y)

            # ### END OLD ###
            ## BEGIN NEW ###
            pids = [i.split('_')[1] for i in path]
            res = self.bag.query('select frame, x, y, area, intensity, perimeter\
                                          from assoc, particles\
                                          where assoc.particle == particles.id\
                                          and particles.id in ' + str(tuple(pids)) \
                                          + ' and assoc.frame < ' + str(self.end_frame) \
                                          + ' and assoc.frame >= ' + str(self.start_frame)\
                                          + ' order by frame')

            for frame, x, y, area, intensity, perimeter in res:
                mean_area += area / len(path)
                mean_intensity += intensity / len(path)
                mean_perimeter += perimeter / len(path)
                d = {'frame': frame, 'particle': pid, 'x': x, 'y': y}
                self.out_bag.batchInsertAssoc(d)

            # Debug area deltas, remove eventually
            res = zip(*res)
            if len(path) == 10:
                self.areas.append(res[3])
            # end debug area deltas

            ## END NEW ###
            d = {'id': pid, 
                 'area': mean_area, 
                 'perimeter': mean_perimeter, 
                 'intensity': mean_intensity
                }

            self.out_bag.batchInsertParticle(d)
            pid += 1

        self.out_bag.commit()

    def is_bitumen(self, u):
        threshold = 110
        return self.G.node[u]['intensity'] < threshold

    def prune_transmission(self ,u, v):
        return False
        return self.is_bitumen(self.G,u) ^ self.is_bitumen(self.G,v)

    def prune_size(self, u, v):
        # This should be based on some statistics of the size variation
        # eg. prune anything > | +/- 3 std dev |
        threshold = 0.3
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            den = float(self.G.node[u]['area'])
            num = float(self.G.node[v]['area'])
        else:
            den = float(self.G.node[v]['area'])
            num = float(self.G.node[u]['area'])

        # print num/den
        if num/den < threshold:
            return True
        else:
            return False

    def prune_appearance(G, u, v):
        return self.prune_transmission(G, u, v) or self.prune_size(G, u, v)

    def euclidD(self, point1, point2):
        '''
        Computes the euclidean distance between two points and 
        returns this distance.
        '''
        sum = 0
        for index in range(len(point1)):
            diff = (point1[index]-point2[index]) ** 2
            sum = sum + diff

        return np.sqrt(sum)

    def prune_motion(self, u, v):
        return self.prune_velocity(u,v)

    def prune_velocity(self, u, v):
        # perhaps confusingly, velocity pruning considers
        #  the position of a node, and prunes nodes outside
        #  a defined radius. This should be based on some statistics...
        threshold = 100
        if self.euclidD(self.G.node[u]['centre'], self.G.node[v]['centre']) > threshold:
            return True
        else:
            return False

    def prune(self, u, v):
        # prune_size(G, u, v) or \
        #prune_transmission(G, u, v) or \
        return self.prune_velocity(u,v)
        
    def similarity_size(self, u, v):
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            similarity = self.G.node[v]['area'] / self.G.node[u]['area']
        else:
            similarity = self.G.node[u]['area'] / self.G.node[v]['area']
        return similarity

    def similarity_transmission(self, u, v):
        if self.G.node[u]['intensity'] > self.G.node[v]['intensity']:
            similarity = self.G.node[v]['intensity'] / self.G.node[u]['intensity']        
        else:
            if self.G.node[v]['intensity'] == 0:
                similarity = 1
            else:
                similarity = self.G.node[u]['intensity'] / self.G.node[v]['intensity']
        return similarity

    def similarity_appearance(self, u, v):
            w1 = 0.8
            w2 = 0.2
            return w1*self.similarity_size(u, v) + w2*self.similarity_transmission(u, v)

    def similarity_motion(self, u, v):
        return 0.0

    def similarity(self, u, v):
        w1 = 1.0
        w2 = 0.0
        return w1*self.similarity_appearance(u, v) + w2*self.similarity_motion(u, v) 

    def get_cost(self, u, v):
        w1 = 0.45#similarity 
        w2 = 0.35#distance - prefer closer
        w3 = 0.20#intensity*area - prefer bigger and darker

        scale = 1000
        distance = self.euclidD(self.G.node[u]['centre'], self.G.node[v]['centre'])
        # what is the magic number for prune_velocity, ensure they match
        distance_prune = 100
        bigger = 250
        area = self.G.node[u]['area']
        intensity = self.G.node[u]['intensity']

        return int(w1*scale*( 1 - (self.similarity(u, v)) )) + \
               int(w2*scale*( distance / distance_prune )) + \
               int(w3*scale*( intensity/255 ) * ( max(bigger-area,0) / bigger ))               

##
# Tracker V3 uses the Databag for loading/storing detection/tracking results
#            Uses Keras to modify network graph weights.
##
class TrackerV3(object):

    def __init__(self, bag, DV, CC, verbose=False):
        self.G = nx.DiGraph()
        self.verbose = verbose
        self.bag = bag
        self.q = Query(self.bag)
        self.new_pid = 0
        self.DV = DV
        self.CC = CC
        
        # For debugging only
        self.sim_appearance = []
        self.hyp_costs = []
        self.deltas = []
        self.motion_probs = []
        self.appearance_probs = []
        self.total_edges_considered = 0
        self.pruned_edges = 0

    def build(self, start_frame, end_frame):
        self.G.clear()
        self.G.add_node('s')
        self.G.add_node('t')

        self.start_frame = start_frame
        self.end_frame = end_frame

        self.no_frames = end_frame - start_frame

        start = time.time()


        # Detector error rate
        #  Cost for an object to go from frame i to frame i+1
        C_i = np.int32(100 * np.log(0.40))


        ### Notes: should be low entry cost for first frame
        ###        low exit cost for last frame.
        ###        Might play with these later...
        ###        For now it's ~#tracks/(#det*#frames)
        # Cost for object entering frame
        # C_en = -np.log(eps)
        C_en_factor = np.int32(-100 * np.log(150 / (200*10.0)))
        # Cost for object exiting frame
        # C_ex = -np.log(eps)
        C_ex_factor = np.int32(-100 * np.log(150 / (200*10.0)))


        # Store the results frame-wise, as list of lists
        particles = []
        
        for i in range(start_frame, end_frame):
            buf = self.q.deepTrackingNodeData(i)
            particles.append(buf)

        crops = []
        for ps in particles:
            for p in ps:
                crop = np.frombuffer(p.crop, dtype="uint8").reshape(64, 64)
                crop = self.CC.preproc(crop)
                crops.append(crop)

        crops = np.array(crops)
        shape = crops.shape
        crops = crops.reshape(shape[0], shape[1], shape[2], 1)
        lats = self.CC.encoder.predict(crops)

        buf = self.q.getScreenFeatures()
        screenFeatures = dict()
        for r in buf:
            screenFeature = np.float64(np.frombuffer(r.screen_feature, dtype='uint8').reshape(64,64))
            screenFeatures[int(r.frame)] = screenFeature / 255.0

        print "latent vectors computed ...", time.time()-start
        start = time.time()

        count = 0
        # For every detected object x_i
        for ps in particles:
            for p in ps:
                pid = p.particle
                frame = int(p.frame)
                area = p.area
                intensity = p.intensity
                lat = lats[count]
                x = p.x
                y = p.y

                u = 'u_' + str(pid)
                v = 'v_' + str(pid)

                screenFeature = screenFeatures[frame]

                #  create two nodes u_i v_i
                self.G.add_node(u,
                                id=u,
                                area=float(area), 
                                x=x,
                                y=y,
                                intensity=intensity, 
                                enc=lat,
                                screenFeature=screenFeature)
                self.G.add_node(v,
                                id=v,
                                area=float(area), 
                                x=x,
                                y=y, 
                                intensity=intensity, 
                                enc=lat,
                                screenFeature=screenFeature)

                #  create edge (u_i, v_i)
                #   with cost c(u_i, v_i) = C_i
                #   and flow f(u_i, v_i) = f_i
                self.G.add_edge(u, v, weight=C_i, capacity=1)

                #  create edge (s, u_i)
                #   with cost c(s, u_i) = C_en,_i
                #   and flow f(s, u_i) = f_en,_i
                # C_en = (frame - start_frame + 1) * C_en_factor 
                C_en = C_en_factor
                self.G.add_edge('s', u, weight=C_en, capacity=1)

                #  create and edge (v_i, t)            
                #   with cost c(v_i, t) = C_ex,_i
                #   and flow f(v_i, t) = f_ex,_i
                # C_ex = (self.no_frames - (frame - start_frame)) * C_ex_factor
                C_ex = C_ex_factor
                self.G.add_edge(v, 't', weight=C_ex, capacity=1)
                # G.add_edge(u, 't', weight=C_ex, capacity=1)

                count += 1
 
        if self.verbose:
            print "graph nodes created ..."
            print "sink and source edges connected ...", str(time.time()-start), ' seconds'
            start = time.time()

        # For every transition P_link(x_j|x_i) != 0
        for i in range(0, end_frame - start_frame - 1):
            ### Get ALL particles in a particular frame            
            # v_ids = self.bag.query('select id from particles, asn_particlessoc \
            #     where particles.id == assoc.particle \
            #     and frame == ' + str(i))
            # u_ids = self.bag.query('select id from particles, assoc \
            #     where particles.id == assoc.particle \
            #     and frame == ' + str(i+1))

            ### Get TOP N particles in a frame, using our earlier query
            v_particles = particles[i]
            u_particles = particles[i+1]

            for j in v_particles:
                for k in u_particles:
                    v_id = 'v_' + str(j.particle)
                    u_id = 'u_' + str(k.particle)

                    v = self.G.node[v_id]
                    u = self.G.node[u_id]

                    # Pruning step, returns True to prune (skip adding)    
                    self.total_edges_considered += 1            
                    if self.prune(u, v):
                        self.pruned_edges += 1
                        continue

                    #  create edge (v_i, u_j)
                    #   with cost c(v_i, u_j) = C_i,_j
                    #   and flow f(v_i, u_j) = f_i,_j
                    C_i_j = self.get_cost(v, u)

                    # 2147483647 is max in32 in numpy, using this to prevent overflow during cast
                    C_i_j = np.int32( min( -100 * np.log(C_i_j), 2147483647) )    

                    # if C_i_j > 110:
                    #     continue

                    self.hyp_costs.append(C_i_j)

                    self.G.add_edge(v['id'], u['id'], weight=C_i_j, capacity=1)

        if self.verbose:
            print "graph construction complete ...", str(time.time()-start), ' seconds'

    def solve(self, no_tracks):
        self.no_tracks = no_tracks
        # Compute the min cost and retrieve flows
        start = time.time()

        self.G.node['s']['demand'] = -no_tracks
        self.G.node['t']['demand'] = no_tracks
        try:
            self.min_cost, self.flowDict = nx.network_simplex(self.G)
        except nx.NetworkXUnfeasible:
            self.flowDict = {'s':{}}
            print "No flow satisfies constraints ..."


        if self.verbose:
            print "min cost flow computed ...", str(time.time()-start), ' seconds'  

    def reconstruct_paths(self):
        start = time.time()
        # Reconstruct paths
        self.paths = []
        self.full_paths = []
        self.path_costs = []

        for k,v in self.flowDict['s'].iteritems():        
            if v:
                self.path_costs.append([self.G.edge['s'][k]['weight']])
                self.full_paths.append([])
                buf = []
                curr = k
                buf.append(curr)            
                while (curr != 't'):
                    for k,v in self.flowDict[curr].iteritems():
                        if v:
                            cost = self.G.edge[curr][k]['weight']
                            self.path_costs[-1].append(cost)
                            self.full_paths[-1].append(curr)
                            curr = k

                            if curr[0] != 'v':
                                buf.append(curr)
                            break
                # take off that sink node

                if len(buf)==3:
                    pass
                    # print buf

                # _ = buf.pop()
                _ = buf.pop()

                if len(buf)==1 or len(buf) ==0:                    
                    continue

                self.paths.append(buf)

        if self.verbose:
            print "paths reconstructed ...", str(time.time()-start), ' seconds'
            print "reconstructed ", str(len(self.paths)), " paths"


    def save_paths(self, filename):
        self.out_bag = DataBag(filename, verbose=True)
        # used to test a hypothesis regarding particle areas over time/ camera problems

        for i in range(self.start_frame, self.end_frame):
            d = {'number':i}
            self.out_bag.batchInsertFrame(d)        

        for path in self.paths:
            mean_area = 0.0
            mean_intensity = 0.0
            mean_perimeter = 0.0

            # ### BEGIN OLD ###
            # # I think this loop can be optimized with an "IN" query and 
            # #  vector computation of the means
            # for pid in path:
            #     pid = pid.split('_')[1]
            #     res = self.bag.query('select frame, x, y, area, intensity, perimeter\
            #                               from assoc, particles\
            #                               where assoc.particle == particles.id\
            #                               and particles.id == ' + str(pid) \
            #                               + ' and assoc.frame < ' + str(self.end_frame) \
            #                               + ' and assoc.frame >= ' + str(self.start_frame))[0]

            #     frame, x, y, area, intensity, perimeter = res

            #     mean_area += area / len(path)
            #     mean_intensity += intensity / len(path)
            #     mean_perimeter += perimeter / len(path)

            #     self.out_bag.batchInsertAssoc(frame, self.new_pid, x, y)

            # ### END OLD ###
            ## BEGIN NEW ###
            pids = [i.split('_')[1] for i in path]
            res = self.bag.query('select frame, x, y, area, intensity, perimeter\
                                          from assoc, particles\
                                          where assoc.particle == particles.id\
                                          and particles.id in ' + str(tuple(pids)) \
                                          + ' and assoc.frame < ' + str(self.end_frame) \
                                          + ' and assoc.frame >= ' + str(self.start_frame)\
                                          + ' order by frame')

            for frame, x, y, area, intensity, perimeter in res:
                mean_area += area / len(path)
                mean_intensity += intensity / len(path)
                mean_perimeter += perimeter / len(path)
                d = {'frame': frame, 'particle': self.new_pid, 'x': x, 'y': y}
                self.out_bag.batchInsertAssoc(d)

            # Debug area deltas, remove eventually
            # res = zip(*res)
            # if len(path) == 10:
            #     self.areas.append(res[3])
            # end debug area deltas

            ## END NEW ###
            d = {'id': self.new_pid, 
                 'area': mean_area, 
                 'perimeter': mean_perimeter, 
                 'intensity': mean_intensity
                }

            self.out_bag.batchInsertParticle(d)
            self.new_pid += 1

        self.out_bag.commit()

    def gkern(self, l=5, sig=1.):
        """
        creates gaussian kernel with side length l and a sigma of sig
        https://stackoverflow.com/questions/29731726/how-to-calculate-a-gaussian-kernel-matrix-efficiently-in-numpy
        """

        ax = np.arange(-l // 2 + 1., l // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)

        kernel = np.exp(-(xx**2 + yy**2) / (2. * sig**2))

        return kernel / np.sum(kernel)

    def getHeatMap(self, delta):
      large_value = 1
      shape = (256, 256)
      kernel = self.gkern(256, 3)

      origin = (np.array(shape) - 1) / 2.0
      
      dx = 128 * np.tanh(delta[0]/3.)
      dy = 128 * np.tanh(delta[1]/3.)

      x = int(round(origin[1] + dx))
      y = int(round(origin[0] + dy))

      dx = int(round(dx))
      dy = int(round(dy))

      # buf[y-10:y+10, x-10:x+10] = 32768 * kernel
      # buf[y, x] = large_value
      buf = large_value * np.roll(kernel, (dy,dx), (0,1))

      return buf

    def is_bitumen(self, u):
        threshold = 110
        return self.G.node[u]['intensity'] < threshold

    def prune_transmission(self ,u, v):
        return False
        return self.is_bitumen(self.G,u) ^ self.is_bitumen(self.G,v)

    def prune_size(self, u, v):
        # This should be based on some statistics of the size variation
        # eg. prune anything > | +/- 3 std dev |
        threshold = 0.3
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            den = float(self.G.node[u]['area'])
            num = float(self.G.node[v]['area'])
        else:
            den = float(self.G.node[v]['area'])
            num = float(self.G.node[u]['area'])

        # print num/den
        if num/den < threshold:
            return True
        else:
            return False

    def prune_appearance(G, u, v):
        return self.prune_transmission(G, u, v) or self.prune_size(G, u, v)

    def euclidD(self, point1, point2):
        '''
        Computes the euclidean distance between two points and 
        returns this distance.
        '''
        sum = 0
        for index in range(len(point1)):
            diff = (point1[index]-point2[index]) ** 2
            sum = sum + diff

        return np.sqrt(sum)

    def prune_motion(self, u, v):
        return self.prune_velocity(u,v)

    def prune_velocity(self, u, v):
        # perhaps confusingly, velocity pruning considers
        #  the position of a node, and prunes nodes outside
        #  a defined radius. This should be based on some statistics...
        threshold = 42
        if self.euclidD([u['x'], u['y']], [v['x'], v['y']]) > threshold:
            return True
        else:
            return False

    def prune(self, u, v):
        # prune_size(G, u, v) or \
        #prune_transmission(G, u, v) or \
        return self.prune_velocity(u,v)

    def similarity_size(self, u, v):
        if self.G.node[u]['area'] > self.G.node[v]['area']:
            similarity = self.G.node[v]['area'] / self.G.node[u]['area']
        else:
            similarity = self.G.node[u]['area'] / self.G.node[v]['area']
        return similarity

    def similarity_transmission(self, u, v):
        if self.G.node[u]['intensity'] > self.G.node[v]['intensity']:
            similarity = self.G.node[v]['intensity'] / self.G.node[u]['intensity']        
        else:
            if self.G.node[v]['intensity'] == 0:
                similarity = 1
            else:
                similarity = self.G.node[u]['intensity'] / self.G.node[v]['intensity']
        return similarity

    def probability_appearance(self, u, v):
            w1 = 0.8
            w2 = 0.2
            probability = w1*self.similarity_size(u, v) + w2*self.similarity_transmission(u, v)
            self.appearance_probs.append(probability)
            return probability

    def probability_motion(self, u, v):
        dx = np.array([v['x'] - u['x']])
        dy = np.array([v['y'] - u['y']])
        enc = u['enc']
        f1 = u['screenFeature']
        f2 = v['screenFeature']
        structured_data = np.array([np.concatenate([enc, dx, dy])])
        screen_data = np.array([np.array([f1,f2]).T])

        probability = self.DV.deep_velocity.predict([structured_data, screen_data])[:,0][0]

        return probability

    def get_cost(self, u, v):
        # probability = self.probability_appearance(u, v) * self.probability_motion(u, v)
        probability = self.probability_motion(u, v)

        return probability

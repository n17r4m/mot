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
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
import time
import json

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

        pid = 0
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
    
class TrackerV2(object):

    def __init__(self, bag, verbose=False):
        self.G = nx.DiGraph()
        self.verbose = verbose
        self.bag = bag

    def build(self, start_frame, end_frame):
        self.G.clear()
        self.G.add_node('s')
        self.G.add_node('t')

        self.no_frames = end_frame - start_frame

        start = time.time()

        # Detector error rate
        #  Cost for an object to go from frame i to frame i+1
        beta = 0.03
        C_i = 10

        # Cost for object entering frame
        # C_en = -np.log(eps)
        C_en_factor = 30 # some multiplier
        C_en_ratio = 20 # roughly the expected number to stay in frame to entering/exiting

        # Cost for object exiting frame
        # C_ex = -np.log(eps)
        C_ex_factor = 30
        C_ex_ratio = 20

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

        count = 0
        # For every detected object x_i
        for particle in all_particles:
            pid, frame, area, intensity, x, y = particle
            centre = (x, y)

            u = 'u_' + str(pid)
            v = 'v_' + str(pid)

            #  create two nodes u_i v_i
            self.G.add_node(u, area=float(area), centre=centre, intensity=intensity)
            self.G.add_node(v, area=float(area), centre=centre, intensity=intensity)

            #  create edge (u_i, v_i)
            #   with cost c(u_i, v_i) = C_i
            #   and flow f(u_i, v_i) = f_i
            self.G.add_edge(u, v, weight=C_i, capacity=1)

            #  create edge (s, u_i)
            #   with cost c(s, u_i) = C_en,_i
            #   and flow f(s, u_i) = f_en,_i
            C_en = count * C_en_factor * C_en_ratio
            self.G.add_edge('s', u, weight=C_en, capacity=1)

            #  create and edge (v_i, t)            
            #   with cost c(v_i, t) = C_ex,_i
            #   and flow f(v_i, t) = f_ex,_i
            C_ex = (self.no_frames-count-1) * C_ex_factor * C_ex_ratio
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


    def save_paths(self, filename):
        self.out_bag = DataBag(filename, verbose=True)


        for i in range(self.no_frames):
            self.out_bag.insertFrame(i)

        new_pid = 0

        for path in self.paths:
            mean_area = 0.0
            mean_intensity = 0.0
            mean_perimeter = 0.0

            for pid in path:
                pid = pid.split('_')[1]
                res = self.bag.query('select frame, x, y, area, intensity, perimeter\
                                          from assoc, particles\
                                          where assoc.particle == particles.id\
                                          and particles.id == ' + str(pid))[0]

                frame, x, y, area, intensity, perimeter = res

                mean_area += area / len(path)
                mean_intensity += intensity / len(path)
                mean_perimeter += perimeter / len(path)

                self.out_bag.insertAssoc(frame, new_pid, x, y)

            new_pid += 1

            self.out_bag.insertParticle(mean_area, mean_intensity, mean_perimeter, new_pid)

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
        w3 = 0.05#intensity - prefer darker
        w4 = 0.15#size - prefer bigger
        scale = 1000
        distance = self.euclidD(self.G.node[u]['centre'], self.G.node[v]['centre'])
        # what is the magic number for prune_velocity, ensure they match
        distance_prune = 100
        bigger = 250
        area = self.G.node[u]['area']
        intensity = self.G.node[u]['intensity']

        return int(w1*scale*( 1 - (self.similarity(u, v)) )) + \
               int(w2*scale*( distance / distance_prune )) + \
               int(w3*scale*( intensity/255 )) + \
               int(w4*scale*( max(bigger-area,0) / bigger ))
    

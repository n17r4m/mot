import numpy as np
from uuid import uuid4
from lib.Database import Database
from lib.util.store_args import store_args
import itertools as it
import traceback
import time

class Corruption:
    @store_args
    def __init__(self, experimentName, model = "linear", profile = "simple", frames = 1000, width = 2336, height = 1729, segment_size = 10):
        self.motion = getattr(Motion, model)(profile, width, height)
        self.experimentName = experimentName
        
    async def go(self):
        
        tx, transaction = await Database().transaction()
        
        q = """
            SELECT experiment, method
            FROM experiment
            WHERE name = '{experimentName}'
            """
        s = q.format(experimentName=self.experimentName)    
        
        detectionExperiment = ""
        trackingExperiment = ""
        
        async for row in tx.cursor(s):
            if row["method"].lower().find('detection') >= 0:
                print("detection experiment", row["experiment"])
                detectionExperiment = row["experiment"]
                
            if row["method"].lower().find('tracking') >= 0:
                print("tracking experiment", row["experiment"])
                trackingExperiment = row["experiment"]            
        
        try:
        
            latent_samples = []
            for c in range(5):
                latent_cat_samples = []
                async for track in tx.cursor("""
                    SELECT latent 
                    FROM Track LEFT JOIN Particle USING(particle) 
                    WHERE category = $1 
                    AND experiment = '5a9b6f60-dcae-40ad-8bc8-c19c14854836'
                    limit 50000
                    """, c):
                    latent_cat_samples.append(track["latent"])
                latent_samples.append(latent_cat_samples)
        
            experiment_name = self.experimentName

            segment_number = 0; 
            
            q = """
                SELECT fd.number, fd.frame fd, ft.frame ft
                FROM frame fd, frame ft
                WHERE fd.experiment = '{detectionExperiment}' 
                AND ft.experiment = '{trackingExperiment}'
                AND fd.number=ft.number
                ORDER BY fd.number
                """
            s = q.format(detectionExperiment=detectionExperiment,
                         trackingExperiment=trackingExperiment)
                         
            async for row in tx.cursor(s):
                f = row["number"]
                ft_uuid = row["ft"]
                fd_uuid = row["fd"]
                print("Frame", f)
                
                # NOTE: change how often the corruption is randomized
                #        if left untouched, it simply doubles the number of tracks
                #        which isn't really corruption.
                if True or f % self.segment_size == 0:

                    self.motion.initialize()
                    segment_number += 1
                    
                    particle_tracking_uuids = [uuid4() for i in range(self.motion.quantity)]
                    
                    # particle_latents = []
                    # for p in self.motion.particles:
                    #     particle_latents.append(np.random.choice(latent_samples[int(p[6])]))
                    
                    ### New code to get latents - faster?
                    nParticles = len(self.motion.particles)
                   
                    particle_latents = [0]*nParticles
                    
                    # categories
                    for cat in [2,3,4]:
                        bParticleCats = self.motion.particles[:,6] == cat
                        particleCats = self.motion.particles[:,6][bParticleCats]

                        latents = np.random.choice(latent_samples[cat],
                                                   size=particleCats.shape)
                        
                        count = 0
                        for i in range(nParticles):
                            if bParticleCats[i]:
                                particle_latents[i] = latents[count]
                                count += 1

                    ### End New code 
                    
                    particles_uuids_inserted = []

                
                self.motion.tick()
                
                
                
                for i, p in enumerate(self.motion.particles):
                    
                    # check if particle is in frame
                    if p[0] > 0 and p[0] < self.width and p[1] > 0 and p[1] < self.height:
                        
                        
                        #messy
                        radius = max(2, np.random.normal(6, 2))
                        area = np.pi * radius ** 2
                        perimeter = 2 * np.pi * radius
                        intensity = min(254, max(1, np.random.normal(127, 50)))
                        latent = particle_latents[i]
                        location = (p[0], p[1])
                        bbox = ((p[0]-radius, p[1]-radius), (p[0]+radius, p[1]+radius))
                        
                        
                        particle_detection = (uuid4(), detectionExperiment, area, intensity, perimeter, radius, p[6])
                        # We don't want to add  corrupted particles to ground truth
                        # particle_tracking = (particle_tracking_uuids[i], trackingExperiment, area, intensity, perimeter, radius, p[6])
                        
                        particle_inserts = [particle_detection]
                        
                        # We don't want to add  corrupted tracks to ground truth
                        # if particle_tracking[0] not in particles_uuids_inserted:
                        #     particle_inserts.append(particle_tracking)
                        #     particles_uuids_inserted.append(particle_tracking[0])
                        # start = time.time()
                        await tx.executemany("""
                            INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, particle_inserts)
                        # print("4", start-time.time())
                            
                        
                        track_detection = (uuid4(), fd_uuid, particle_detection[0], location, bbox, latent)
                        # We don't want to add  corrupted tracks to ground truth
                        # track_tracking = (uuid4(), ft_uuid, particle_tracking[0], location, bbox, latent)
                        
                        
                        
                        # start = time.time()
                        await tx.executemany("""
                            INSERT INTO Track (track, frame, particle, location, bbox, latent)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, [track_detection])
                        # print("5", start-time.time())
                        
                        
        except Exception as e:
            print("Uh oh. Something went wrong")
            traceback.print_exc()
            await transaction.rollback()
            
        else:
            await transaction.commit()
            
        finally:
            print("Fin.")
            
        return

class Motion:
    
    class linear:
        @store_args
        def __init__(self, profile = "simple", width = 2336, height = 1729):
            self.profiles = getattr(self.profiles, profile)(self.profiles) 
            self.quantity = sum([p.quantity for p in self.profiles])

        def initialize(self):
            self.particles = np.zeros((self.quantity, 7))
            self.particles[:, 0] = np.random.uniform(0, self.width, (self.quantity,))
            #messy 
            self.particles[:, 1] = np.random.uniform(-self.height, self.height*2, (self.quantity,))
            c = 0; 
            for p in self.profiles:
                self.particles[c:c+p.quantity, 2] = np.random.normal(p.dxμ, p.dxσ, (p.quantity,))
                self.particles[c:c+p.quantity, 3] = np.random.normal(p.dyμ, p.dyσ, (p.quantity,))
                self.particles[c:c+p.quantity, 4] = np.random.normal(p.axμ, p.axσ, (p.quantity,))
                self.particles[c:c+p.quantity, 5] = np.random.normal(p.ayμ, p.ayσ, (p.quantity,))
                self.particles[c:c+p.quantity, 6] = p.category
                c += p.quantity

        def tick(self):
            self.particles[:, 2:4] += self.particles[:, 4:6]
            self.particles[:, 0:2] += self.particles[:, 2:4]

        class profiles: # overwritten on instantiation by return of below return
            
            class ParticleClass:
                @store_args
                def __init__(self, name = "undefined", 
                               category = 0, quantity = 0, 
                                    dxμ = 0, dxσ = 0, dyμ = 0, dyσ = 0,
                                    axμ = 0, axσ = 0, ayμ = 0, ayσ = 0):
                    pass
            
            # Deprecated, but still have DV models trained with these params
            # def simple(self):
            #     PC = self.ParticleClass; return [
            #     #   name      c   qty  dxμ  dxσ    dyμ  dyσ  axμ  axσ  ayμ  ayσ 
            #     PC("bitumen", 2,  200, 0.0, 0.5,   5.0, 3.0, 0.0, 0.0, 0.0, 0.0),
            #     PC("sand",    3,  200, 0.0, 0.5,  -3.0, 2.0, 0.0, 0.0, 0.0, 0.0),
            #     PC("bubble",  4,   50, 0.0, 0.5,  10.0, 4.0, 0.0, 0.0, 0.0, 0.0)]
                
            def simple(self):
                PC = self.ParticleClass; return [
                #   name      c   qty  dxμ  dxσ    dyμ  dyσ  axμ  axσ  ayμ  ayσ 
                PC("bitumen", 2,  200, 0.0, 0.5, -10.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                PC("sand",    3,  200, 0.0, 0.5,  10.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                PC("bubble",  4,   50, 0.0, 0.5, -50.0, 4.0, 0.0, 0.0, 0.0, 0.0)]
                
            def sandy(self):
                PC = self.ParticleClass; return [
                #   name      c    qty  dxμ  dxσ   dyμ  dyσ  axμ  axσ  ayμ  ayσ
                PC("bitumen", 2,   200, 0.0, 1.0,  5.0, 3.0, 0.0, 0.0, 0.0, 0.0),
                PC("sand",    3,   500, 0.0, 3.0, -4.0, 6.0, 0.0, 0.0, 0.0, 0.0),
                PC("bubble",  4,   100, 0.0, 1.0, 10.0, 4.0, 0.0, 0.0, 0.0, 0.0)]
            
            def acceleration(self):
                PC = self.ParticleClass; return [
                #   name      c    qty  dxμ  dxσ   dyμ  dyσ   axμ  axσ   ayμ  ayσ
                PC("bitumen", 2,  1000, 0.0, 1.0,  5.0, 3.0,  0.0, 0.1,  0.1, 0.1),
                PC("sand",    3,  1000, 0.0, 3.0, -4.0, 6.0,  0.0, 0.1, -0.1, 0.1),
                PC("bubble",  4,   100, 0.0, 1.0, 10.0, 4.0,  0.0, 0.1,  0.2, 0.1)]
            




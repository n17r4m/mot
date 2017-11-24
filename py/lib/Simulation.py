import numpy as np
from uuid import uuid4
from lib.Database import Database
from lib.util.store_args import store_args
import itertools as it
import traceback

class Simulation:
    @store_args
    def __init__(self, model = "linear", profile = "simple", frames = 1000, width = 2336, height = 1729, segment_size = 10):
        self.motion = getattr(Motion, model)(profile, width, height)
        
    async def go(self):
        
        tx, transaction = await Database().transaction()
        
        
        try:
        
            latent_samples = []
            for c in range(5):
                latent_cat_samples = []
                async for track in tx.cursor("""
                    SELECT latent 
                    FROM Track LEFT JOIN Particle USING(particle) 
                    WHERE category = $1 
                    AND experiment = '5a9b6f60-dcae-40ad-8bc8-c19c14854836'
                    """, c):
                    latent_cat_samples.append(track["latent"])
                latent_samples.append(latent_cat_samples)
        
            experiment_name = str(uuid4())
            
            experiment_detection = (uuid4(), experiment_name, "simulation_detection", " ".join((self.model, self.profile)))
            experiment_tracking  = (uuid4(), experiment_name, "simulation_tracking", " ".join((self.model, self.profile)))
            
            await tx.executemany("""
                INSERT INTO Experiment (experiment, day, name, method, notes)
                VALUES ($1, NOW(), $2, $3, $4)
            """, [experiment_detection, experiment_tracking])
            
            segment_number = 0; 
            
            
            for f in range(self.frames):
                
                print("Frame", f)
                
                if f % self.segment_size == 0:
                    segment_detection = (uuid4(), experiment_detection[0], segment_number)
                    segment_tracking  = (uuid4(),  experiment_tracking[0], segment_number)
                    
                    await tx.executemany("""
                        INSERT INTO Segment (segment, experiment, number)
                        VALUES ($1, $2, $3)
                    """, [segment_detection, segment_tracking])
                    
                    
                    self.motion.initialize()
                    segment_number += 1
                    
                    
                    particle_tracking_uuids = [uuid4() for i in range(self.motion.quantity)]
                    
                    
                    particle_latents = []
                    for p in self.motion.particles:
                        particle_latents.append(np.random.choice(latent_samples[int(p[6])]))
                    
                    
                    particles_uuids_inserted = []
                    
                    
                frame_detection = (uuid4(), experiment_detection[0], segment_detection[0], f)
                frame_tracking  = (uuid4(),  experiment_tracking[0],  segment_tracking[0], f)
                
                await tx.executemany("""
                    INSERT INTO Frame (frame, experiment, segment, number)
                    VALUES ($1, $2, $3, $4)
                """, [frame_detection, frame_tracking])
                
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
                        
                        
                        particle_detection = (uuid4(), experiment_detection[0], area, intensity, perimeter, radius, p[6])
                        particle_tracking = (particle_tracking_uuids[i], experiment_tracking[0], area, intensity, perimeter, radius, p[6])
                        
                        particle_inserts = [particle_detection]
                        if particle_tracking[0] not in particles_uuids_inserted:
                            particle_inserts.append(particle_tracking)
                            particles_uuids_inserted.append(particle_tracking[0])
                        await tx.executemany("""
                            INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """, particle_inserts)
                            
                        
                        track_detection = (uuid4(), frame_detection[0], particle_detection[0], location, bbox, latent)
                        track_tracking = (uuid4(), frame_tracking[0], particle_tracking[0], location, bbox, latent)
                
                        await tx.executemany("""
                            INSERT INTO Track (track, frame, particle, location, bbox, latent)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, [track_detection, track_tracking])
                        
                        
        except Exception as e:
            print("Uh oh. Something went wrong")
            traceback.print_exc()
            await transaction.rollback()
            
        else:
            await transaction.commit()
            
        finally:
            print("Fin.")
            
        return experiment_name

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
            
            def simple(self):
                PC = self.ParticleClass; return [
                #   name      c   qty  dxμ  dxσ   dyμ  dyσ  axμ  axσ  ayμ  ayσ 
                PC("bitumen", 2,  200, 0.0, 1.0,  5.0, 3.0, 0.0, 0.0, 0.0, 0.0),
                PC("sand",    3,  200, 0.0, 3.0, -3.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                PC("bubble",  4,   50, 0.0, 1.0, 10.0, 4.0, 0.0, 0.0, 0.0, 0.0)]
                
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
            




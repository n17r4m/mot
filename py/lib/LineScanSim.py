import numpy as np
from uuid import uuid4
from lib.Database import Database
from lib.util.store_args import store_args
import itertools as it
import traceback

class Simulation:
    @store_args
    def __init__(self, model = "linear", profile = "simple", frames = 1, width = 2336, time = 1, method='simulation_linescan'):
        self.motion = getattr(Motion, model)(profile, width, time)
        self.method = method
        
    async def go(self):
        
        tx, transaction = await Database().transaction()
        
        try:
            print("0")
            latent_samples = []
            area_samples = []
            for c in range(5):
                latent_cat_samples = []
                area_cat_samples = []
                curr_particle = None
                prev_particle = None
                async for track in tx.cursor("""
                    SELECT particle, latent, area
                    FROM Track LEFT JOIN Particle USING(particle) 
                    WHERE category = $1
                    AND experiment = '727ca46c-6c35-4d5a-85b9-59dc716674fd'
                    ORDER BY particle
                    """, c):
                    curr_particle = str(track["particle"])
                    if curr_particle != prev_particle:
                        if prev_particle is not None:
                            latent_cat_samples.append(particle_latents)
                            area_cat_samples.append(particle_areas)
                        prev_particle = curr_particle
                        particle_latents = []
                        particle_areas = []
                    particle_latents.append(track["latent"])
                    particle_areas.append(track["area"])
                        
                latent_samples.append(latent_cat_samples)
                area_samples.append(area_cat_samples)
        
            print("1")
            
            experiment_name = str(uuid4())
            
            experiment_detection = (uuid4(), experiment_name, self.method, " ".join((self.model, self.profile)))

            await tx.executemany("""
                INSERT INTO Experiment (experiment, day, name, method, notes)
                VALUES ($1, NOW(), $2, $3, $4)
            """, [experiment_detection])
            
            self.motion.initialize()
            
            particle_tracking_uuids = [uuid4() for i in range(self.motion.quantity)]

            nParticles = len(self.motion.particles)
            particle_latents = [0]*nParticles
            particle_areas = [0]*nParticles
            # categories
            print("2")
            for cat in [2,3,4]:
                bParticleCats = self.motion.particles[:,6] == cat
                particleCats = self.motion.particles[:,6][bParticleCats]
                state = np.random.get_state()
                latents = np.random.choice(latent_samples[cat],
                                           size=particleCats.shape,
                                           replace=False)
                np.random.set_state(state)
                areas = np.random.choice(area_samples[cat],
                                         size=particleCats.shape,
                                         replace=False)
                count = 0
                for i in range(nParticles):
                    if bParticleCats[i]:
                        particle_latents[i] = latents[count]
                        particle_areas[i] = areas[count]
                        count += 1
            print("3")
            particles_uuids_inserted = []
                
                
            frame_detection = (uuid4(), experiment_detection[0], 0)
            
            await tx.executemany("""
                INSERT INTO Frame (frame, experiment, number)
                VALUES ($1, $2, $3)
            """, [frame_detection])
            print("4")
            
            for i, p in enumerate(self.motion.particles):
                #messy
                lat_idx = np.random.randint(0,len(particle_latents[i]))
                latent = particle_latents[i][lat_idx]
                
                area = particle_areas[i][lat_idx]
                
                radius = np.sqrt( area / np.pi )
                perimeter = 2 * np.pi * radius
                
                intensity = min(254, max(1, np.random.normal(127, 50)))
                
                location = (p[0], p[1])
                bbox = ((p[0]-radius, p[1]-radius), (p[0]+radius, p[1]+radius))
                
                
                particle_detection = (uuid4(), experiment_detection[0], area, intensity, perimeter, radius, p[6])
                await tx.executemany("""
                    INSERT INTO Particle (particle, experiment, area, intensity, perimeter, radius, category)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, [particle_detection])
                    
                
                track_detection = (uuid4(), frame_detection[0], particle_detection[0], location, bbox, latent)
                await tx.executemany("""
                    INSERT INTO Track (track, frame, particle, location, bbox, latent)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, [track_detection])
                        
                        
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
        def __init__(self, profile = "simple", width = 2336, time = 1729):
            self.profiles = getattr(self.profiles, profile)(self.profiles) 
            self.quantity = sum([p.quantity for p in self.profiles])

        def initialize(self):
            # Initialize the array to store particle data
            self.particles = np.zeros((self.quantity, 7))
            
            # Particle x location
            self.particles[:, 0] = np.random.uniform(0, self.width, (self.quantity,))
            
            # particle appeared in front of sensor at time...
            self.particles[:, 1] = np.random.uniform(0, self.time, (self.quantity,))
            c = 0; 
            for p in self.profiles:
                self.particles[c:c+p.quantity, 2] = np.random.normal(p.dxμ, p.dxσ, (p.quantity,))
                self.particles[c:c+p.quantity, 3] = np.random.normal(p.dyμ, p.dyσ, (p.quantity,))
                self.particles[c:c+p.quantity, 4] = np.random.normal(p.axμ, p.axσ, (p.quantity,))
                self.particles[c:c+p.quantity, 5] = np.random.normal(p.ayμ, p.ayσ, (p.quantity,))
                self.particles[c:c+p.quantity, 6] = p.category
                c += p.quantity

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
                #   name      c   qty  dxμ  dxσ    dyμ  dyσ  axμ  axσ  ayμ  ayσ 
                PC("bitumen", 2,  200, 0.0, 0.2, -10.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                PC("sand",    3,  200, 0.0, 0.2,  10.0, 2.0, 0.0, 0.0, 0.0, 0.0),
                PC("bubble",  4,   50, 0.0, 0.2, -50.0, 4.0, 0.0, 0.0, 0.0, 0.0)]
                

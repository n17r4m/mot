
import numpy as np
from uuid import UUID, uuid4

from lib.Database import Database

async def main(args):
    
    db = Database()
    

        
    print("")
    print("")
    c = 3
    
    print("Category", c)
    
    latents = []
    
    async for track in db.query("""
        SELECT (latent) 
        FROM Track LEFT JOIN particle USING(particle) 
        WHERE category = $1 
        AND experiment = '727ca46c-6c35-4d5a-85b9-59dc716674fd'
        ORDER BY RANDOM() 
        """, c):
        
        latents.append([float(i) for i in track["latent"][1:-1].split(',')])
    
    print("Found", len(latents))
    print("")
    latents = np.array(latents)
    
    mu = np.mean(latents, axis=0)
    std = np.std(latents, axis=0)
    
    print("Mean")
    print(list(mu.astype("float16")))
    
    print("")
    print("Std")
    print(list(std.astype("float16")))
        
        
    
    
    
    latents = []
    
    async for track in db.query("""
        SELECT (latent) 
        FROM Track LEFT JOIN particle USING(particle) 
        WHERE category = $1 
        AND experiment = 'c06d2e89-7fd5-4e02-9c4c-544902b5db82'
        ORDER BY RANDOM() 
        """, c):
        
        latents.append([float(i) for i in track["latent"][1:-1].split(',')])
    
    print("Found", len(latents))
    print("")
    latents = np.array(latents)
    
    mu = np.mean(latents, axis=0)
    std = np.std(latents, axis=0)
    
    print("Mean")
    print(list(mu.astype("float16")))
    
    print("")
    print("Std")
    print(list(std.astype("float16")))
        
    
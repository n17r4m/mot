
import config

from lib.Database import Database

import shutil
import asyncio
import os
import sys


async def main(args):
    print(await clean_experiments_dir(*args))
    


async def clean_experiments_dir():
    
    
    exp_dirs = set([f for f in os.listdir(config.experiment_dir) if os.path.isdir(os.path.join(config.experiment_dir, f))])
    print("Found", len(exp_dirs), "experiment directories")
    
    exp_db = set()
    async for exp in Database().query("SELECT * FROM experiment ORDER BY experiment"):
        exp_db.add(str(exp["experiment"]))
    
    print("Found", len(exp_db), "experiment database entries")
    
    
    removed = 0
    for to_remove in (exp_dirs - exp_db):
        print("Removing", to_remove)
        path = os.path.join(config.experiment_dir, to_remove)
        shutil.rmtree(path)
        removed += 1
        
    return "Removed {} invalid directories".format(removed)
    
    
    
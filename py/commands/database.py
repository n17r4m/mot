
from lib.Database import Database

async def main(args):
    
    if len(args) == 0: print("What you want to do? [reset]")
        
    else:
        if   args[0] == "reset":      await database_reset()
        

async def database_reset():

        db = Database()
        await db.reset()
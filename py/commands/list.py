

from lib.Database import Database


async def main(args):
    
    if len(args) == 0:                await list_experiments()
    else:
        if   len(args) == 1:          await list_frames(args)
        elif len(args) == 2:          await get_frame(args)
        else:                         print("Invalid list sub-command")


async def list_experiments():
    
    db = Database()
    
    async for record in db.query("""
        SELECT experiment, day, name, count(frame) as frames, notes
        FROM Experiment
        LEFT JOIN Frame USING (experiment)
        GROUP BY experiment"""):
        print(record["experiment"], record["day"], record["name"], record["frames"], "frames", record["notes"])


async def list_frames(args):
    
    db = Database()
    experiment = args[0]
    
    async for record in db.query("""
        SELECT frame
        FROM Frame
        LEFT JOIN Experiment USING (experiment)
        WHERE experiment = $1
        ORDER BY number ASC""", experiment):
        print(record["frame"])

async def get_frame(args):
    
    db = Database()
    experiment   = args[0]
    frame_number = int(args[1])
    
    async for record in db.query("""
        SELECT frame
        FROM Frame
        LEFT JOIN Experiment USING (experiment)
        WHERE experiment = $1
        AND number = $2""", experiment, frame_number):
        print(record["frame"])
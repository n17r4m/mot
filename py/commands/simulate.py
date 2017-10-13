
from lib.Simulator import Simulator


async def main(args):

    sim = Simulator(args)
    
    print(sim)
    
    print(await sim.go())
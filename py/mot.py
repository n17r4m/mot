#! /usr/bin/env python
"""
Command Runner

Author: Martin Humphreys
"""

from argparse import ArgumentParser
import asyncio





def build_parser():
    parser = ArgumentParser()
    parser.add_argument('args', help='Command(s)', nargs="+")
    return parser



async def main():
    parser = build_parser()
    opts = parser.parse_args()
    
    try:
        
        command, args = opts.args[0], opts.args[1:]
        module = __import__("commands." + command)
        await getattr(module, command).main(args)
        
    except ImportError as e:
        
        print("Unknown command specified", command, e)
        print("Known commands are:")
        print("grab, insert, show, dump, simulate, import")
        


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
#!/usr/bin/env python
"""
Command Runner

Author: Martin Humphreys
"""

from argparse import ArgumentParser
import asyncio

def build_parser():
    # pass args into the command...
    parser = ArgumentParser()
    parser.add_argument('args', help='Command(s)', nargs="+")
    return parser

async def main():
    parser = build_parser()
    opts = parser.parse_args()
    try:
        command, args = opts.args[0], opts.args[1:]
        module = __import__("commands." + command)
        print(await getattr(module, command).main(args))
    except ImportError as e:
        print("Unknown command specified", command, e)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

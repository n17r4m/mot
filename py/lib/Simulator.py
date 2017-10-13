#! /usr/bin/env python
"""
Database simulation engine

Author: Martin Humphreys
"""

from lib.Database import Database

class Simulator(object):
    
    def __init__(self, args):
        self.eg = "Example"
        self.db = Database()
        print("My args", args)
        
    async def go(self):
        await self.db.test()
        return self.eg

    
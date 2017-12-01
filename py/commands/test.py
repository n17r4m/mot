import os

async def main(args):
    if len(args) == 0: print("What you want to test? [process|]")
    __import__("test.{}".format(args[0]))
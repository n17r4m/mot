import os

async def main(args):
    if len(args) == 0: print("What you want to test?")
    module = __import__("test.{}".format(args[0]))
    
    try:
        command = args[0]
        print(await getattr(module, command).main(args[1:]))
    except Exception as e:
        print(e)
        print("Failed to run test file main...")
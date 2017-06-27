#! /usr/bin/env python
"""
Generate html documentation

"""

import os
import pydoc
from argparse import ArgumentParser

class Documentor(object):
    
    def __init__(self, thing, forceload=0):
        self.object, self.name = pydoc.resolve(thing, forceload)
        self.html = pydoc.HTMLDoc()
    
    def page(self):
        return self.html.page(pydoc.describe(self.object), self.html.document(self.object, self.name))



def build_parser():
    parser = ArgumentParser()
    parser.add_argument('pyfile', help='python file to generate documentation about', default="Documentor.py", nargs="?")
    return parser


def main(opts):
    if not os.path.isfile(opts.pyfile):
        parser.error("Python file %s does not exist." % opts.pyfile)
    
    thing = pydoc.importfile(opts.pyfile)
    d = Documentor(thing)
    
    print(d.page())


if __name__ == '__main__':
    parser = build_parser()
    main(parser.parse_args())
    
    

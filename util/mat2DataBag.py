#! /usr/bin/env python
"""
Convert between MATLAB .mat and DataBag 
USING:

    As a command line utility:
    
        $ mat2DataBag.py file.mat file.db
    
    As a module:
    
        import mat2DataBag
        mat2DataBag(mat, 'file.db')

Author: Kevin Gordon
"""

import scipy.io
from DataBag import DataBag
import numpy as np
from argparse import ArgumentParser
import os

def mat2DataBag(mat, dbName):
    bag = DataBag(dbName)   
    
    B = mat['B']

    pids = np.unique(B[:,2])
    fids = np.unique(B[:,1])

    for fid in fids:
       f = fid - 1;
       bag.batchInsertFrame(f)

    for pid in pids:
        indexes = B[:,2] == pid
        
        averageArea = np.mean(B[indexes,3])
        averageIntensity = np.mean(B[indexes,4])
        averagePerimeter = np.mean(B[indexes,5])
        
        bag.batchInsertParticle(averageArea, averageIntensity, averagePerimeter, pid)

    for i in range(B.shape[0]):
        row = B[i,:]
        fid = row[0] - 1
        pid = row[1]
        x = row[5]
        y = row[6]
        bag.batchInsertAssoc(fid, pid, x, y)
    
    bag.batchCommit()
    

def build_parser():
    parser = ArgumentParser()
    
    parser.add_argument('mat', help='The matlab .mat file with detection/tracking results')
    parser.add_argument('databag', help='name of new database to save to')      

    return parser


def main(opts):
    if not os.path.isfile(opts.mat):
        parser.error(".mat file %s does not exist." % opts.mat)

    mat = scipy.io.loadmat(opts.mat)

    mat2DataBag(mat, opts.databag)


if __name__ == '__main__':
    main(build_parser().parse_args())
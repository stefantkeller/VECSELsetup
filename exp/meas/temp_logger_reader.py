#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division


import csv
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

'''
Display logged heat sink temperatures with temp_logger.py
'''

def main():

    logfile_path = r'templogger/20150226_temp_logger.csv'

    t = []
    T = []

    with open(logfile_path, 'rb') as logfile:
        logfile.readline() # skip header
        f = csv.reader(logfile,delimiter=',')
        for row in f:
            t.append(float(row[0]))
            T.append(float(row[1]))
    
    t, T = np.array(t), np.array(T)
    
    plt.plot((t-t[0])/3600,T,'.-b')

    hms = lambda t: datetime.fromtimestamp(t).strftime('%H:%M:%S')
    hmsa = lambda tarray: [hms(t) for t in tarray]
    locs, labels = plt.xticks()
    plt.xticks(locs, hmsa(3600*locs+t[0]))
    
    ttl = lambda t: datetime.fromtimestamp(t).strftime('%a: %Y-%m-%d')
    plt.title('{0} -- {1}'.format(ttl(t[0]),ttl(t[-1])))
    
    tstart = datetime.fromtimestamp(t[0])
    tend = datetime.fromtimestamp(t[-1])
    tmidnight = datetime(year=tstart.year, month=tstart.month, day=tstart.day, hour=0, minute=0, second=0)
    j = 0
    while (tmidnight < tend):
        plt.axvline((float(tmidnight.strftime('%s'))-t[0])/3600, c='k', linestyle='--')
        j+=1
        tmidnight = datetime(year=tstart.year, month=tstart.month, day=tstart.day+j, hour=0, minute=0, second=0)
    
    plt.xlim( (np.array([t[0],t[-1]])-t[0])/3600 )
    plt.grid('on')
    plt.show()


if __name__ == '__main__': main()

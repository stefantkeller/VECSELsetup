#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import csv
import numpy as np
import matplotlib.pyplot as plt
from sys import exit

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import load, sanitize, split2dict, find_random_duplicates

'''
Plot the heat sink temperature present during the measurements.
For each set temperature the plot assignes one row of subplots.
Each row shows two plots:
Left is the measured temperature versus time (in units of measurement sample).
Right displays the temperature versus pump current; of which there are multiple repetitions.
'''


def main():
    logfile = '20150124_detailed/spot333um_noOC.csv'
    
    
    current_set = {}
    ths_chrono = {}
    ths_current = {}
    ths_current_err = {}
    
    with open(logfile,'rb') as lf:
        rootpath = '/'.join(logfile.split('/')[:-1])
        header = lf.readline() # read and thus skip header
        
        hdict = split2dict(header, ';','=')
        columns = hdict['columns'].split(',')
        cid = dict( zip(columns,range(len(columns))) ) # easily accessible dict with instructions of what the columns refer to
        
        pwr_folder = sanitize(hdict['pwr_folder'])
        pwr_root = rootpath+'/'+pwr_folder+'/'
        
        r = csv.reader(lf,delimiter=',')
        for row in r:
            if row[0].startswith('#'): continue # a commented entry => skip
            
            T = float(row[cid['Temp_set']])
            
            tf = pwr_root+row[cid['Temp_live']]
            tcurr, ths = load(tf)
            tcurr, ths_chrono[T] = map(float,tcurr), map(float,ths) # in chronological order
            
            ordered = find_random_duplicates(tcurr)
            current_set[T] = np.array(sorted(ordered.keys()))
            
            index_list = np.array([ordered[c] for c in current_set[T]]).transpose() # look up table with indices corresponding to same set current, in ascending order!
            LUT = lambda x, indices: np.array([[x[i] for i in duplicate] for duplicate in indices])
            
            ths_current[T] = LUT(ths_chrono[T],index_list)
            ths_current_err[T] = ev.stderrvallist(ths_current[T])
            
            #return current_set, ths_chrono, ths_current
    
    T_set = sorted(current_set.keys())
    N = len(T_set)
    
    cnt = 1
    
    for T in T_set:

        # chnonological temp
        plt.subplot(N,2,cnt)
        plt.plot(ths_chrono[T],c='k',marker='.',linestyle=' ')
        plt.axhline(y=np.mean(ths_chrono[T]),c='k')
        plt.xlim([0,len(ths_chrono[T])])
        plt.ylabel('Heat sink ($^\circ$C)')
        if cnt==N*2-1:
            plt.xlabel('Time')
        

        # by current
        plt.subplot(N,2,cnt+1)
        plt.plot(current_set[T], ths_current[T].transpose(),c='k',marker='.',linestyle=' ')
        plt.axhline(y=np.mean(ths_chrono[T]),c='k')
        #plt.errorbar(current_set[T], ths_current_err[T].v(),
        #             yerr=ths_current_err[T].e(), c='r', linestyle=' ')
        #plt.axhline(y=ev.wmean(ths_current_err[T]).v(),c='r')
        
        plt.xlim([0,np.max(current_set[T])])
        if cnt==N*2-1:
            plt.xlabel('Current set (A)')
        cnt += 2
    
    plt.show()



if __name__ == "__main__":
    main()

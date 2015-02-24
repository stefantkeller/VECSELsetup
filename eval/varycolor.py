#! /usr/bin/python2.7
# -*- coding: utf-8 -*-


import numpy as np
import matplotlib.pyplot as plt

"""
Based on varycolor.m Created by Daniel Helmick 8/12/2008
ported to .py by Stefan Keller 2014/09/11

run this module to see a plot with all the colors.
"""

def varycolor(n_colors):
    '''
    Produces colors with maximum variation on plots with multiple
    lines.

    Returns a matrix of dimension n_colors by 3; an RGB entry per line.
    Yellow and White are avoided because of their poor performance
    for presentation.
    
    '''
    small_set = [(0,1,0),(0,1,1),(0,0,1),(1,0,1),(1,0,0),(0,0,0)]
    if n_colors<=6: color_set = small_set[:n_colors]
    else: # default, and where this function has an actual advantage
        # init (just an array of right length, type doesn't matter to python)
        color_set = range(n_colors)
        # say to have n_seg segments to distribute the plots
        n_seg = 5
        each_sec = np.floor(n_colors/n_seg)
        # how many extra lines are there?
        extra_plots = n_colors%n_seg

        # number of plots per color section (equal parts plus residu)
        section = [int(each_sec+1*(extra_plots>sec)) for sec in range(n_seg)]
        
        s=0
        for m in range(section[s]):
            color_set[int(m+np.sum(section[:s]))] = (0,1,float(m)/(section[s]-1))
        s=1
        for m in xrange(section[s]):
            color_set[int(m+np.sum(section[:s]))] = (0,float(section[s]-(m+1))/(section[s]),1)
        s=2
        for m in xrange(section[s]):
            color_set[int(m+np.sum(section[:s]))] = (float(m+1)/section[s],0,1)
        s=3
        for m in xrange(section[s]):
            color_set[int(m+np.sum(section[:s]))] = (1,0,float(section[s]-(m+1))/section[s])
        s=4
        for m in xrange(section[s]):
            color_set[int(m+np.sum(section[:s]))] = (float(section[s]-(m+1))/section[s],0,0)

    return color_set


def llist(instr,outtype=list):
    '''
    returns a long, flat list of type outtype,
    whose entries are of value a with multiplicity b

    example 1:
    instr = [(a1,b1),(a2,b2),...]
    out = [a1,a1,a1,...,a2,a2,...]
            \- b1 -/    \- b2 -/
    
    example 2:
    what_i_want = [(1,2), # 1,1
                   (2,3), # 2,2,2
                   (1,5)] # 1,1,1,1,1
    llist(what_i_want)
    >>> [1,1,2,2,2,1,1,1,1,1]

    example 3:
    in MATLAB it is:
    a = [0*ones(1,250),8*ones(1,1000),6.5*ones(1,1000)]
    with llist it is:
    a = llist([(0,250),(8,1000),(6.5,1000)])
    see github.com/stefantkeller/STK_py_generals/general_functions.py
    '''
    out = []
    for i in instr:
        if len(i)==2 and isinstance(i[1],int):
            # note for when bored: benchmark the following
            out += [i[0]]*i[1]
            #out += [i[0] for k in xrange(i[1)]
    return outtype(out)

def main():
    n_colors = 20
    color_set = varycolor(n_colors)
    for p in xrange(n_colors):
        plt.plot(range(20),llist([(p,20)]),c=color_set[p])

    plt.ylim([-1,n_colors])
    plt.show()

if __name__ == "__main__":
    main()

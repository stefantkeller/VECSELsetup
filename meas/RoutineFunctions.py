#! /usr/bin/python2.7
# -*- coding: utf-8 -*-


'''
This module provides some stand-alone functions
that may be useful for a measurement routine.
See exp/ for examples, what I mean with this statement.
'''


import time

import numpy as np


def shuffle_list(L):
    if isinstance(L,(list,np.ndarray)):
        n = len(L)
        for j in range(n):
            k = np.random.randint(j, n)
            L[j], L[k] = L[k], L[j]

def split_list(L,direction='ud'):
    # L: an ordered (ascending) list (i.e. values go from low->high)
    # direction: 'ud' .. up-down; /\ start at first entry (a low one) go 'up' to highest and 'down' again
    #            'du' .. down-up; \/
    if isinstance(L,(list,np.ndarray)):
        n = len(L)
        if n%2==0:
            # start at 1 for up means:
            # the very first entry is skipped
            # (basically leaving an odd number of entries)
            # account for it on the way down
            up = [L[t] for t in xrange(1,n,2)]
            dwn =  [L[t] for t in xrange((n-1)-1,-1,-2)]
        else:
            up = [L[t] for t in xrange(0,n,2)]
            dwn = [L[t] for t in xrange((n-1)-1,-1,-2)]
    if direction=='ud': L_ = up+dwn
    elif direction=='du': L_ = dwn+up
    else: L_ = []
    return L_

def find_closest_index(L,value):
    # find closest >= value (if there is an entry closer but below, it is ignored)
    # L must be sorted in ascending order (i.e. from low to high)
    idx = L.searchsorted(value)
    idx = np.min([np.max([idx,0]), len(L)-1]) # or: np.clip(idx, 0, len(L)-1)
    return idx

def wrap_around(L,value):
    # L: an ordered (ascending) list (i.e. values go from low->high)
    # value: returned list starts at value closest to this, goes up, down and back to the start
    #        choose value = room temperature to save time with heating cycle
    i = find_closest_index(L,value)
    if i is None: raise ValueError, 'Incompatible value to wrap around!'
    frst = split_list(L[i:],'ud')
    scnd = split_list(L[:i],'du')
    retlist = frst+scnd # looks sth like: ^v
    if i==0 and L[0]==retlist[-1]: retlist = retlist[::-1] # if start was the first value, return a list whose first value is that start!
    return retlist




one_decimal = lambda L: np.floor(np.array(L)*10)/10.0

def main():

    n_repetitions = 3 # at each temperature each pump power will be applied this often; to get errorbars, to know how reliable the result is

    room_temperature = 20 # deg C
    # heat sink instructions
    heatsink_start = 10 # deg C
    heatsink_end = 45 # deg C
    heatsink_npoints = 8


    # pump power, in A:
    pump_start = 0 # A
    pump_end = 20 # A
    pump_npoints = 5



    temperatures = one_decimal( np.linspace(heatsink_start, heatsink_end, heatsink_npoints) )
    T = wrap_around(temperatures,room_temperature)
    print T

    import matplotlib.pyplot as plt
    plt.subplot(121)
    plt.plot(temperatures,'.--b',markersize=12)
    plt.axhline(room_temperature,c='k')
    plt.title('Original temperature range')
    plt.xlabel('Steps')
    plt.ylabel('Temperature ($^\circ$C)')
    plt.subplot(122)
    plt.plot(T,'.--r',markersize=12)
    plt.axhline(room_temperature,c='k')
    plt.title('Wrapped around {0} $^\circ$C'.format(room_temperature))
    plt.xlabel('Steps')
    plt.show()

    laser_current = one_decimal( np.linspace(pump_start, pump_end, pump_npoints) )
    laser_current = list(laser_current)*n_repetitions # dirty but quick; works only for list's, numpy.array's actually multiply the value!
    shuffle_list(laser_current)
    print laser_current





if __name__ == '__main__': main()

#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import  extract


'''
Simple example to demonstrate extraction of measurements from logfile.
It plots the pump current vs. emitted laser power.
'''


def main():

    logfile = '20150123_spotsizeAC/spot222um.csv'


    
    current_set, current, pump, refl, laser, spectra, meantemp = extract(logfile, identifiers=['Current','Pump','Refl','Laser','Spectra', 'Temperature'])
    Temperatures = sorted(current_set.keys())
    
    T_out = dict((T,meantemp[T].round(1).v()) for T in Temperatures)

    cols = varycolor(3*len(Temperatures))

    cnt = 0 # color counter


    for T in Temperatures:
        plt.errorbar(current[T].v(),laser[T].v(),
                     xerr=current[T].e(),yerr=laser[T].e(),
                     c=cols[cnt],linestyle=' ')
        cnt+=3

    plt.title('Title')
    plt.xlabel('Current (A)')
    plt.ylabel('Emited power (W)')
    #plt.xlim(xlim)
    #plt.ylim(ylim)
    plt.grid('on')
    
    plt.show()


if __name__ == "__main__":
    main()

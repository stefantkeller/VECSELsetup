#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract, lut_from_calibfolder, lut_interp_from_calibfolder


def main():
    logfile = '20150204_sample21-1-d6/spot333um.csv'
    calib_folder = '20150204_calib_333um_s21-1-d6'


    # calibration
    #pump_lut, refl_lut, emis_lut = lut_from_calibfolder(calib_folder)
    emis_lut = lut_from_calibfolder(calib_folder,identifiers=['Laser'],ignore_error=False) # emission has constant value solely due to BS, no ND in front of detector etc.
    pump_lut, refl_lut = lut_interp_from_calibfolder(calib_folder,identifiers=['Pump','Refl'])
    
    #------------------------------------
    # load measurement
    current_set, current, pump, refl, laser, meantemp = extract(logfile, identifiers=['Current','Pump','Refl','Laser','Temperature'])
    Temperatures = sorted(current_set.keys())

    absorbed, reflected, emitted, pumped, dissipated, relref = {}, {}, {}, {}, {}, {}
    for T in Temperatures:
        reflected[T] = refl_lut(refl[T])
        pumped[T] = pump_lut(pump[T])
        absorbed[T] = pumped[T] - reflected[T]
        emitted[T] = emis_lut(laser[T])
        dissipated[T] = absorbed[T] - emitted[T]
        relref[T] = reflected[T]/pumped[T]*100



    cols = varycolor(3*len(Temperatures))
    cnt = 0

    #plt.subplot(1,2,1)

    baserefl = ev.errvallist()
    for T in Temperatures:
        
        # plot

        pstart, pend = 1, 9 # W pumped
        istart, iend = np.sum([pumped[T].v()<pstart]), np.sum([pumped[T].v()<pend])
        baserefl.append(ev.wmean(relref[T][istart:iend]))

        xplot = current
        xlabel = 'Pump current (A)'

        plt.errorbar(xplot[T].v(),relref[T].v(),
                     xerr=xplot[T].e(),yerr=relref[T].e(),
                     c=cols[cnt],linestyle=' ',
                     label='$({0})^\circ$C'.format(meantemp[T].round(2)))
        plt.plot(xplot[T][istart:iend].v(), (iend-istart)*[baserefl[-1].v()],color='k')

        cnt+=3

    plt.xlabel(xlabel)
    plt.ylabel('Reflectivity (%)')
    #plt.xlim([0, 20])
    reflylim = [25, 70]
    plt.ylim(reflylim)
    plt.legend(loc='best',prop={'size':12},labelspacing=-0.4)
    plt.grid('on')
    plt.show()

    ##

    #plt.subplot(1,2,2)

    templist = [meantemp[T] for T in Temperatures]
    Temp = ev.errvallist(templist)

    q,m = ev.linreg(Temp.v(),baserefl.v(),baserefl.e())

    plt.errorbar(Temp.v(),baserefl.v(),
                 xerr=Temp.e(),yerr=baserefl.e(),
                 color='r',linestyle=' ')
    plt.plot(Temp.v(),q.v()+Temp.v()*m.v(),'k')
    plt.text((Temp[0].v()+Temp[1].v())/2.0,baserefl[0].v()+2,
             r'$({})+({})T_{{hs}}$'.format(q.round(2),m.round(2)))
    plt.ylim(reflylim)
    plt.xlabel('Heat sink temperature ($^\circ$C)')
    plt.ylabel('Reflectivity (%)')
    plt.grid('on')

    ##
    plt.show()


    

if __name__ == "__main__":
    main()

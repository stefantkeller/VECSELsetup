#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract

def plot_current_current(logfile,colors,textxy):
    current_set, current = extract(logfile, identifiers=['Current'])
    T = current_set.keys()[0] # we care only about one temperature, actually, for calibration Temp is irrelevant anyway
    xymin, xymax = np.min(current_set[T]), np.max(current_set[T])
    textx, texty = textxy[0], textxy[1]
    
    # linreg
    q0,m0 = ev.linreg(current_set[T],current[T].v(),current[T].e(),overwrite_zeroerrors=True)

    # plot
    plt.errorbar(current_set[T],current[T].v(),
                 yerr=current[T].e(),
                 c=colors[0],linestyle=' ')
    plt.plot(current_set[T],m0.v()*current_set[T]+q0.v(),c=colors[1])

    summary = r'(${0}$) $\times$ c_set + (${1}$) A'.format(m0.round(2),q0.round(2))
    plt.text(textx,texty, summary,color='k')
    
    return xymin, xymax

def check_current_integrity(logfiles,calibplot_c):

    cols = varycolor(3*len(logfiles)) # 3 per to have decent distinction

    textx, texty = 5, 15
    xymin, xymax = 0, 0

    plt.clf()
    plt.subplot(1,1,1)

    for ls in range(len(logfiles)):
        xymin_, xymax_ = plot_current_current(logfiles[ls],cols[ls*3:],(textx,texty-2*ls))
        if xymin_ < xymin: xymin = xymin_
        if xymax_ > xymax: xymax = xymax_

    xlim = [xymin,xymax]
    ylim = xlim


    title = 'Current -- set vs get'
    plt.title(title)
    plt.xlabel('Current set (A)')
    plt.ylabel('Current actually applied (A)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #plt.show()
    plt.savefig(calibplot_c)
    
    print u'Current calibration finished:\n{0}'.format(calibplot_c)


def main():
    logfile1 = '20141128_calib/1_pump_calib.csv' # thermal PM at sample pos
    logfile2 = '20141128_calib/2_refl_calib.csv' # thermal PM behind refl lens, before beam sampler; sees what is incident on BS
    logfile3 = '20141128_calib/3_emission_calib.csv' # PM_th behind lens without BS
    logfile4 = '20141128_calib/4_emission_calib.csv' # PM_th with lens
    
    rootpath = '/'.join(logfile1.split('/')[:-1])
    lut_folder = '/LUTs'
    calibplot_c = rootpath+lut_folder+'/calib_current.png'
    
    #logfile1 = '../1_pump_calib.csv' # from here: take 'Current'
    #logfile2 = '../2_refl_calib.csv' # ...
    #logfile3 = '../3_emission_calib.csv' # ...
    #logfile4 = '../4_emission_calib.csv' # ...

    check_current_integrity([logfile1,logfile2,logfile3,logfile4],calibplot_c)

if __name__ == "__main__":
    main()

#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract


def calibrate_emission(logfile3,logfile4,calibfile_e,calibplot_e):

    #------------------------------------
    #current_set,current,pump,reflection,emission,absorption = extract(logfile,identifiers=['Current','Pump','Refl','Laser'])
    current_set3, current3, thermal3 = extract(logfile3, identifiers=['Current','Laser'])
    current_set4, current4, thermal4 = extract(logfile4, identifiers=['Current','Laser'])

    #------------------------------------
    # plot instructions

    title = 'emission'
    Tt3, Tt4 = thermal3.keys()[0], thermal4.keys()[0] # we care only about one temperature, actually, for calibration Temp is irrelevant anyway
    xmin, xmax = ev.min(thermal4[Tt4],False), ev.max(thermal4[Tt4],False)
    ymin, ymax = ev.min(thermal3[Tt3],False), ev.max(thermal3[Tt3],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3

    cols = varycolor(3*len(thermal4)) # 3 per temperature

    plt.clf()
    plt.subplot(1,1,1)

    # linreg
    q0,m0 = ev.linreg(thermal4[Tt4].v(),thermal3[Tt3].v(),thermal3[Tt3].e())

    # plot
    plt.errorbar(thermal4[Tt4].v(),thermal3[Tt3].v(),
                 xerr=thermal4[Tt4].e(),yerr=thermal3[Tt3].e(),
                 c=cols[0],linestyle=' ')
    plt.plot(thermal4[Tt4].v(),m0.v()*thermal4[Tt4].v()+q0.v(),c=cols[1])

    summary = r'(${0}$) $\times$ real_pos + (${1}$) W'.format(m0.round(2),q0.round(2))
    plt.text(textx,texty, summary,color='k')


    plt.title(title)
    plt.xlabel('Power seen behind optical elements (W)')
    plt.ylabel('Power seen directly after OC (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #plt.show()
    plt.savefig(calibplot_e)
    
    #
    #------------------------------------
    # write file with evaluation as LUT
    with open(calibfile_e,'wb') as ef:
        ef.write(u'columns=PM_realpos(W),PM_realpos_sterr(W),PM_reference(W),PM_reference_sterr(W);linreg={0}*real_pos+{1}\n'.format(ev.errval(m0,printout='cp!'),ev.errval(q0,printout='cp!')))
        for entry in range(len(thermal4[Tt4])):
            ef.write(u'{0},{1},{2},{3}\n'.format( thermal4[Tt4].v()[entry],thermal4[Tt4].e()[entry],
                                                  thermal3[Tt3].v()[entry],thermal3[Tt3].e()[entry] ))

    print u'Emission calibration finished:\n{0}\n{1}'.format(calibfile_e,calibplot_e)


def main():
    logfile3 = '20141128_calib/3_emission_calib_nofilter.csv' # PM_th directly behind OC 
    logfile4 = '20141128_calib/3_emission_calib.csv' # PM_th behind OC and lens
    
    rootpath = '/'.join(logfile3.split('/')[:-1])
    lut_folder = '/LUTs'
    calibfile_e = rootpath+lut_folder+'/calib_emission_longpass-filter.csv'
    calibplot_e = rootpath+lut_folder+'/calib_emission_longpass-filter.png'
    
    #logfile3 = '../3_pump_calib.csv' # from here: take 'Current' and 'Laser'
    #logfile4 = '../4_pump_calib.csv' # from here: also take 'Current' and 'Laser'
    
    calibrate_emission(logfile3,logfile4,calibfile_e,calibplot_e)


if __name__ == "__main__":
    main()

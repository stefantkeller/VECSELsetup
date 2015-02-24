#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract



def calibrate_reflection(logfile2,logfile3,calibfile_r,calibplot_r):

    #------------------------------------
    #current,pump,reflection,emission,absorption = extract(logfile,identifiers=['Current','Pump','Refl','Laser'])
    current_set2, current2, thermal = extract(logfile2, identifiers=['Current','Laser'])
    current_set3, current3, reflection = extract(logfile3, identifiers=['Current','Refl'])


    #------------------------------------
    # plot instructions

    title = 'Reflection'
    Tr, Tt = reflection.keys()[0], thermal.keys()[0] # we care only about one temperature, actually, for calibration Temp is irrelevant anyway
    xmin, xmax = ev.min(reflection[Tr],False), ev.max(reflection[Tr],False)
    ymin, ymax = ev.min(thermal[Tt],False), ev.max(thermal[Tt],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3

    cols = varycolor(3*len(reflection)) # 3 per temperature

    plt.clf()
    plt.subplot(1,1,1)

    # linreg
    q0,m0 = ev.linreg(reflection[Tr].v(),thermal[Tt].v(),thermal[Tt].e())

    # plot
    plt.errorbar(reflection[Tr].v(),thermal[Tt].v(),
                 xerr=reflection[Tr].e(),yerr=thermal[Tt].e(),
                 c=cols[0],linestyle=' ')
    plt.plot(reflection[Tr].v(),m0.v()*reflection[Tr].v()+q0.v(),c=cols[1])

    summary = r'(${0}$) $\times$ refl + (${1}$) W'.format(m0.round(2),q0.round(2))
    plt.text(textx,texty, summary,color='k')


    plt.title(title)
    plt.xlabel('Power seen by S121C (photodiode) (W)')
    plt.ylabel('Power seen by S314C (thermal PM) (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #plt.show()
    plt.savefig(calibplot_r)
    
    
    #------------------------------------
    # write file with evaluation as LUT
    with open(calibfile_r,'wb') as rf:
        rf.write(u'columns=PM_refl(W),PM_refl_sterr(W),PM_reference(W),PM_reference_sterr(W);linreg={0}*r+{1}\n'.format(ev.errval(m0,printout='cp!'),ev.errval(q0,printout='cp!')))
        for entry in range(len(reflection[Tr])):
            rf.write(u'{0},{1},{2},{3}\n'.format( reflection[Tr].v()[entry],reflection[Tr].e()[entry],
                                                  thermal[Tt].v()[entry],thermal[Tt].e()[entry] ))
    
    print u'Reflection calibration finished:\n{0}\n{1}'.format(calibfile_r,calibplot_r)

def main():
    logfile2 = '20141128_calib/2_refl_calib.csv' # thermal PM behind refl lens pos (w/o lens), before beam sampler; sees what is incident on BS
    logfile3 = '20141128_calib/3_emission_calib.csv' # thermal PM removed, with lens

    rootpath = '/'.join(logfile2.split('/')[:-1])
    lut_folder = '/LUTs'
    calibfile_r = rootpath+lut_folder+'/calib_reflection.csv'
    calibplot_r = rootpath+lut_folder+'/calib_reflection.png'
    
    #logfile2 = '../2_refl_calib.csv' # from here: take 'Current' and 'Laser'
    #logfile3 = '../3_emission_calib.csv' # from here: take 'Current' and 'Refl'
    #logfile3 = '../4_emission_calib.csv' # take 3_ or 4_, difference is in position of thermal PM, we don't care about that

    calibrate_reflection(logfile2,logfile3,calibfile_r,calibplot_r)

if __name__ == "__main__":
    main()

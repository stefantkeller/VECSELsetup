#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract



def calibrate_pump(logfile1,calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp):


    #------------------------------------
    #current_set,current,pump,reflection,emission,absorption = extract(logfile,identifiers=['Current','Pump','Refl','Laser'])
    current_set1, current, pump, thermal = extract(logfile1, identifiers=['Current','Pump','Laser'])

    #------------------------------------
    # plot instructions

    title = 'Pump'
    Tp, Tt = pump.keys()[0], thermal.keys()[0] # we care only about one temperature, actually, for calibration Temp is irrelevant anyway
    xmin, xmax = ev.min(pump[Tp],False), ev.max(pump[Tp],False)
    ymin, ymax = ev.min(thermal[Tt],False), ev.max(thermal[Tt],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3

    cols = varycolor(3*len(pump)) # 3 per temperature

    plt.clf()
    plt.subplot(1,1,1)

    # linreg
    q0,m0 = ev.linreg(pump[Tp].v(),thermal[Tt].v(),thermal[Tt].e())

    # plot
    plt.errorbar(pump[Tp].v(),thermal[Tt].v(),
                 xerr=pump[Tp].e(),yerr=thermal[Tt].e(),
                 c=cols[0],linestyle=' ')
    plt.plot(pump[Tp].v(),m0.v()*pump[Tp].v()+q0.v(),c=cols[1])

    summary = r'(${0}$) $\times$ pump + (${1}$) W'.format(m0.round(2),q0.round(2))
    plt.text(textx,texty, summary,color='k')


    plt.title(title)
    plt.xlabel('Power seen by S121C (photodiode) (W)')
    plt.ylabel('Power seen by S314C (thermal PM) (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #
    plt.savefig(calibplot_pp)
    #plt.show()
    #
    #
    
    title = 'Pump (wrt current)'
    Tc = current.keys()[0]
    xmin, xmax = ev.min(current[Tp],False), ev.max(current[Tp],False)
    ymin, ymax = ev.min(thermal[Tt],False), ev.max(thermal[Tt],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3
    start_linreg_at = 6 #A
    #end_linreg_at = ..
    
    sind = sum(current[Tc].v()<start_linreg_at)
    #eind = sum(current[Tc].v()<end_linreg_at)
        
    plt.clf()
    plt.subplot(1,1,1)

    # linreg
    q1,m1 = ev.linreg(current[Tc].v()[sind:],thermal[Tt].v()[sind:],thermal[Tt].e()[sind:])

    # plot
    plt.errorbar(current[Tc].v(),thermal[Tt].v(),
                 xerr=current[Tc].e(),yerr=thermal[Tt].e(),
                 c=cols[0],linestyle=' ')
    plt.plot(current[Tc].v(),m1.v()*current[Tc].v()+q1.v(),c=cols[1])

    summary = r'(${0}$) $\times$ current (${1}$) W'.format(m1.round(2),q1.round(2))
    plt.text(textx,texty, summary,color='k')


    plt.title(title)
    plt.xlabel('Achieved current setting (A)')
    plt.ylabel('Power seen by S314C (thermal PM) (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #plt.show()
    plt.savefig(calibplot_cp)
    
    #------------------------------------
    # write file with evaluation as LUT
    with open(calibfile_pp,'wb') as pf:
        pf.write(u'columns=PM_pump(W),PM_pump_sterr(W),PM_reference(W),PM_reference_sterr(W);linreg={0}*p+{1}\n'.format(ev.errval(m0,printout='cp!'),ev.errval(q0,printout='cp!')))
        for entry in range(len(pump[Tp])):
            pf.write(u'{0},{1},{2},{3}\n'.format( pump[Tp].v()[entry],pump[Tp].e()[entry],
                                                  thermal[Tt].v()[entry],thermal[Tt].e()[entry] ))
    with open(calibfile_cp,'wb') as cf:
        cf.write(u'columns=current(A),current_sterr(A),PM_reference(W),PM_reference_sterr(W);linreg={0}*c+{1}\n'.format(ev.errval(m1,printout='cp!'),ev.errval(q1,printout='cp!')))
        for entry in range(len(current[Tc])):
            cf.write(u'{0},{1},{2},{3}\n'.format( current[Tc].v()[entry],current[Tc].e()[entry],
                                                  thermal[Tt].v()[entry],thermal[Tt].e()[entry] ))
    
    print u'Pump calibration finished:\n{0}\n{1}\n{2}\n{3}'.format(calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp)


def main():
    logfile1 = '20141128_calib/1_pump_calib.csv' # thermal PM at sample pos
    
    rootpath = '/'.join(logfile1.split('/')[:-1])
    lut_folder = '/LUTs'
    calibfile_pp = rootpath+lut_folder+'/calib_pump.csv'
    calibplot_pp = rootpath+lut_folder+'/calib_pump.png'
    calibfile_cp = rootpath+lut_folder+'/calib_pump_current.csv'
    calibplot_cp = rootpath+lut_folder+'/calib_pump_current.png'
    
    #logfile1 = '../1_pump_calib.csv' # from here: take 'Current', 'Pump', and 'Laser'

    calibrate_pump(logfile1,calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp)
    

if __name__ == "__main__":
    main()

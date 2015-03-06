#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import extract

#from sys import exit


def calibrate_pump(logfile1,logfile2,calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp):

    # logfile0 w/ directly attached P-I measurement
    #  here we assume the P-I relation to be constant
    
    # logfile1 w/ P-I measurement after BS
    #  (logfile0 and 1 give BS-fraction assumed to be constant)
    # logfile2 w/ "emission" measurement for whole I-range
    #  from 2 find P-I relation, transform I into P with results from 1
    #  this gives a P-P relation for pump.
    #
    # drop 0-measurement and work with P-I relation from logfile1

    #------------------------------------
    #current_set,current,pump,reflection,emission,absorption = extract(logfile,identifiers=['Current','Pump','Refl','Laser'])
    current_set1, current1, thermal1 = extract(logfile1, identifiers=['Current','Laser'])
    current_set2, current2, pump2 = extract(logfile2, identifiers=['Current','Pump'])

    T1, T2 = current1.keys()[0], current2.keys()[0] # because the protocol writes HS temperature that we're not interested in during calibration (lazy.)
    

    #------------------------------------
    cols = varycolor(3*len(current1)) # 3 per temperature
    
    
    # P-I (1)
    xmin, xmax = ev.min(current1[T1],False), ev.max(current1[T1],False)
    ymin, ymax = ev.min(thermal1[T1],False), ev.max(thermal1[T1],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3
    
    start_linreg_at = 6 #A
    
    sind1 = sum(current1[T1].v()<start_linreg_at)
    
    q1,m1 = ev.linreg(current1[T1].v()[sind1:],thermal1[T1].v()[sind1:],thermal1[T1].e()[sind1:])
    
    if False:
        plt.clf()
        plt.subplot(1,1,1)
        
        plt.errorbar(current1[T1].v(),thermal1[T1].v(),
                     xerr=current1[T1].e(),yerr=thermal1[T1].e(),
                     c=cols[0],linestyle=' ')
        plt.plot(current1[T1].v(),m1.v()*current1[T1].v()+q1.v(),c=cols[1])
        summary = r'(${0}$) $\times$ pump + (${1}$) W'.format(m1.round(2),q1.round(2))
        plt.text(textx,texty, summary,color='k')
        plt.title('P-I pos1 -- supposed to be linear relation!')
        plt.xlabel('Pump current (A)')
        plt.ylabel('Power seen by S314C (thermal PM) (W)')
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.grid('on')
        plt.show()
    
    
    # P-I (2)
    xmin, xmax = ev.min(current2[T2],False), ev.max(current2[T2],False)
    ymin, ymax = ev.min(pump2[T2],False), ev.max(pump2[T2],False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3
    
    start_linreg_at = 6 #A
    
    sind2 = sum(current2[T2].v()<start_linreg_at)
    
    q2,m2 = ev.linreg(current2[T2].v()[sind2:],pump2[T2].v()[sind2:],pump2[T2].e()[sind2:])
    
    if False:
        plt.clf()
        plt.subplot(1,1,1)
    
        plt.errorbar(current2[T2].v(),pump2[T2].v(),
                     xerr=current2[T2].e(),yerr=pump2[T2].e(),
                     c=cols[0],linestyle=' ')
        plt.plot(current2[T2].v(),m2.v()*current2[T2].v()+q2.v(),c=cols[1])
        summary = r'(${0}$) $\times$ pump + (${1}$) W'.format(m2.round(2),q2.round(2))
        plt.text(textx,texty, summary,color='k')
        plt.title('P-I pump')
        plt.xlabel('Pump current (A)')
        plt.ylabel('Power seen by S121C (photodiode) (W)')
        plt.xlim(xlim)
        plt.ylim(ylim)
        plt.grid('on')
        plt.show()
        
    
    # ----------------------------------
    # with m1,q1 scale current from 2
    
    plt.clf()
    plt.subplot(1,1,1)
    

    pump_ = ev.errvallist([ev.max(ev.errvallist([0,p]),False) for p in current2[T2]*m1+q1]) # ignore values below pump threshold
    nzeros = np.sum(pump_.v()==0)

    
    xmin, xmax = ev.min(pump2[T2],False), ev.max(pump2[T2],False)
    ymin, ymax = ev.min(pump_,False), ev.max(pump_,False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3
    
    
    q3,m3 = ev.linreg(pump2[T2].v()[nzeros:],pump_.v()[nzeros:],pump_.e()[nzeros:])
    
    plt.errorbar(pump2[T2].v(),pump_.v(),
                 xerr=pump2[T2].e(),yerr=pump_.e(),
                 c=cols[0],linestyle=' ')
    plt.plot(pump2[T2].v(),m3.v()*pump2[T2].v()+q3.v(),c=cols[1])
    
    summary = r'(${0}$) $\times$ pump + (${1}$) W'.format(m3.round(2),q3.round(2))
    plt.text(textx,texty, summary,color='k')
    
    plt.title('Pump')
    plt.xlabel('Power seen by S121C (photodiode) (W)')
    plt.ylabel('Power at sample (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')
    
    #plt.show()
    plt.savefig(calibplot_pp)
    
    #
    #
    # P-I (scaled)
    
    plt.clf()
    plt.subplot(1,1,1)
    
    xmin, xmax = ev.min(current2[T2],False), ev.max(current2[T2],False)
    ymin, ymax = ev.min(pump_,False), ev.max(pump_,False)
    xlim = [xmin.v()-2*xmin.e(),xmax.v()+2*xmax.e()]
    ylim = [ymin.v()-2*ymin.e(),ymax.v()+2*ymax.e()]
    textx, texty = xmax.v()/4, ymax.v()*2/3
    start_linreg_at = 20 #A
    #end_linreg_at = ..
    
    sind = sum(current2[T2].v()<start_linreg_at)
    #eind = sum(current[Tc].v()<end_linreg_at)
        

    # linreg
    q4,m4 = ev.linreg(current2[T2].v()[sind:],pump_.v()[sind:],pump_.e()[sind:])

    # plot
    plt.errorbar(current2[T2].v(),pump_.v(),
                 xerr=current2[T2].e(),yerr=pump_.e(),
                 c=cols[0],linestyle=' ')
    plt.plot(current2[T2].v(),m4.v()*current2[T2].v()+q4.v(),c=cols[1])

    summary = r'(${0}$) $\times$ current (${1}$) W'.format(m4.round(2),q4.round(2))
    plt.text(textx,texty, summary,color='k')


    plt.title('Pump (wrt current)')
    plt.xlabel('Achieved current setting (A)')
    plt.ylabel('Power at sample (W)')
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.grid('on')

    #plt.show()
    plt.savefig(calibplot_cp)
    
    #exit()
    
    #------------------------------------
    # write file with evaluation as LUT
    with open(calibfile_pp,'wb') as pf:
        pf.write(u'columns=PM_pump(W),PM_pump_sterr(W),PM_reference(W),PM_reference_sterr(W);linreg={0}*p+{1}\n'.format(ev.errval(m3,printout='cp!'),ev.errval(q3,printout='cp!')))
        for entry in range(len(pump_)):
            pf.write(u'{0},{1},{2},{3}\n'.format( pump2[T2].v()[entry],pump2[T2].e()[entry],
                                                  pump_.v()[entry],pump_.e()[entry] ))
    with open(calibfile_cp,'wb') as cf:
        cf.write(u'columns=current(A),current_sterr(A),PM_reference(W),PM_reference_sterr(W);linreg={0}*c+{1}\n'.format(ev.errval(m4,printout='cp!'),ev.errval(q4,printout='cp!')))
        for entry in range(len(current2[T2])):
            cf.write(u'{0},{1},{2},{3}\n'.format( current2[T2].v()[entry],current2[T2].e()[entry],
                                                  pump_.v()[entry],pump_.e()[entry] ))
    
    print u'Pump calibration finished:\n{0}\n{1}\n{2}\n{3}'.format(calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp)


def main():
    logfile1 = '20150112_calib/1_pump_calib.csv' # thermal PM at sample pos
    logfile2 = '20150112_calib/2_refl_calib.csv'
    
    rootpath = '/'.join(logfile1.split('/')[:-1])
    lut_folder = '/LUTs'
    calibfile_pp = rootpath+lut_folder+'/calib_pump.csv'
    calibplot_pp = rootpath+lut_folder+'/calib_pump.png'
    calibfile_cp = rootpath+lut_folder+'/calib_pump_current.csv'
    calibplot_cp = rootpath+lut_folder+'/calib_pump_current.png'
    
    #logfile1 = '../1_pump_calib.csv' # from here: take 'Current', 'Pump', and 'Laser'

    calibrate_pump(logfile1,logfile2,calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp)
    

if __name__ == "__main__":
    main()

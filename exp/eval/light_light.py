#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import load, extract, plotinstructions_write, plotinstructions_read, lut_from_calibfolder, lut_interp_from_calibfolder, thermal_impedance, thermal_resistance


def main():
    # before running this script:
    #   run eval_spectrum.py to provide the .._eval.csv files required for the spectra
    #   run calibration.py (with appropriate calib measurements)
    # and don't forget temperature_heatsink (this is not necessary for this script here, but it provides interesting insights for the measurement at hand)
    logfile = '20150204_calib_333um_s21-1-d6/4_emission_calib.csv'
    calib_folder = '20150204_calib_333um_s21-1-d6'
    
    
    #------------------------------------
    # calibration
    emis_lut = lut_from_calibfolder(calib_folder,identifiers=['Laser'],ignore_error=False) # emission has constant value solely due to BS, no ND in front of detector etc.
    pump_lut, refl_lut = lut_interp_from_calibfolder(calib_folder,identifiers=['Pump','Refl'])
    
    
    #------------------------------------
    # load measurement
    current_set, current, pump, refl, laser, spectra, meantemp = extract(logfile, identifiers=['Current','Pump','Refl','Laser','Spectra', 'Temperature'])
    Temperatures = sorted(current_set.keys()) # set temperatures (round numbers like 15.0 or 22.5 etc)
    T_out = dict((T,meantemp[T].round(1)) for T in Temperatures) # real temperatures for display in plot, including +-uncertainty


    #------------------------------------
    # calculate using calibration
    absorbed, reflected, emitted, pumped, dissipated = {}, {}, {}, {}, {}
    for T in Temperatures:
        reflected[T] = refl_lut(refl[T])
        pumped[T] = pump_lut(pump[T])
        absorbed[T] = pumped[T] - reflected[T]
        emitted[T] = emis_lut(laser[T])
        dissipated[T] = absorbed[T] - emitted[T]

        
    #
    #------------------------------------
    # invoke instructions for plot and fit
    # plotting the data can be tricky to reproduce, store the plot properties in a text file and read from there!
    # (easy to repeat the plot at a later time)
    # open the instruction file in a text editor, edit the instructions and run this module again; it will use the new instructions
    instrfile = logfile[:-4]+'_instr.csv'
    plotinstructions_write(instrfile,Temperatures,calib_folder)
    
    #------------------------------------
    # retrieve instructions
    instr = plotinstructions_read(instrfile)
    
    #
    #------------------------------------
    # translate instructions
    str2lst = lambda s: map(float,s[1:-1].split(','))

    textx = float(instr['textx']) # x coordinate for text; same for first two subplots (absorbed-emitted and absorbed-reflectivity)
    fontsize = float(instr['fontsize'])
    title = instr['title']
    xlim = str2lst(instr['xlim']) # range of x-axis; same for first two subplots
    ylim1 = str2lst(instr['ylim1']) # range of y-axis of first (aborbed-emitted) plot
    ylim2 = str2lst(instr['ylim2']) # range of second y-axis (absorbed-reflectivity)
    xlim3 = str2lst(instr['xlim3']) # third x-axis; (dissipated-wavelength)
    ylim3 = str2lst(instr['ylim3']) # 3rd y-axis
    plot_temps_for_3 = str2lst(instr['plot_temps_for_3']) # which ones to plot? you may have measured a heat sink temperature without lasing output, whose data will confuse the reader, so you don't plot it.
    textx3 = float(instr['textx3']) # x-coordinate of text in 3rd plot
    texty3 = str2lst(instr['texty3']) # 3rd y-coordinate
    llow0 = {}
    lhigh0 = {}
    texty1 = {}
    for T in Temperatures:
        llow0[T] = sum(absorbed[T].v()<float(instr['llow0[{0}]'.format(T)])) # index indicating start of lasing activity
        lhigh0[T] = sum(absorbed[T].v()<float(instr['lhigh0[{0}]'.format(T)])) # index corresponding to where linear segment stops
        texty1[T] = float(instr['texty1[{0}]'.format(T)])

    
    
    #
    #
    #------------------------------------
    #------------------------------------
    # plot
    cols = varycolor(3*len(Temperatures))


    plt.subplot(3,1,1)
    cnt = 0 # color counter

    q0,m0 = {},{} # for linreg
    for T in Temperatures:

        # linreg
        q0[T],m0[T] = ev.linreg(absorbed[T].v()[llow0[T]:lhigh0[T]],
                                emitted[T].v()[llow0[T]:lhigh0[T]],
                                emitted[T].e()[llow0[T]:lhigh0[T]],
                                overwrite_zeroerrors=True)

        emax,emaxi = ev.max(emitted[T],True)
        amax = absorbed[T][emaxi]
        print 'Max emission at ({}) degC at ({}) W absorbed power: ({}) W'.format(T_out[T],amax,emax)
        # plot
        plt.errorbar(absorbed[T].v(),emitted[T].v(),
                     xerr=absorbed[T].e(),yerr=emitted[T].e(),
                     c=cols[cnt],linestyle=' ')
        plt.plot(absorbed[T].v(),m0[T].v()*absorbed[T].v()+q0[T].v(),c=cols[cnt+1])

        plt.text(textx,texty1[T],
                 '${0}$$^\circ$C: ${1}$ %'.format(T_out[T],m0[T].round(3)*100),
                 color=cols[cnt],fontsize=fontsize)
        cnt+=3

    plt.title(title)
    plt.xlabel('Absorbed power (W)')
    plt.ylabel('Emited power (W)')
    plt.xlim(xlim)
    plt.ylim(ylim1)
    plt.grid('on')
    
    #plt.show()

    
    #------------------------------------
    plt.subplot(3,1,2)
    cnt = 0 # reset color counter

    q1,m1 = {},{}
    for T in Temperatures:
        relref = reflected[T]/pumped[T]*100
        
        # plot
        plt.errorbar(absorbed[T].v(),relref.v(),
                     xerr=absorbed[T].e(),yerr=relref.e(),
                     c=cols[cnt],linestyle=' ')
        cnt+=3

    plt.title(title)
    plt.xlabel('Absorbed power (W)')
    plt.ylabel('Reflectivity (%)')
    plt.xlim(xlim)
    plt.ylim(ylim2)
    plt.grid('on')

    #plt.show()
    
    #------------------------------------
    # plot dissipation and spectra
    plt.subplot(3,1,3)
    cnt = 0 # reset
    
    q3,m3 = {},{}
    for T in Temperatures:
        if T in plot_temps_for_3:
            # lambda_short
            #plt.errorbar(dissipated[T].v(),spectra[T][0].v(), 
            #             xerr=dissipated[T].e(),yerr=spectra[T][0].e(),
            #             c=cols[cnt],linestyle=' ')
        
            # lambda_long
            # lin reg for range that lases (>threshold, <roll over), hence instr from subplot 1
            q3[T],m3[T] = ev.linreg(dissipated[T].v()[llow0[T]:lhigh0[T]],
                                    spectra[T][1].v()[llow0[T]:lhigh0[T]],
                                    spectra[T][1].e()[llow0[T]:lhigh0[T]],
                                    overwrite_zeroerrors=True)
            
            # show only a part, not to confuse reader
            #plt.errorbar(dissipated[T].v()[llow0[T]:lhigh0[T]],spectra[T][1].v()[llow0[T]:lhigh0[T]], 
            #             xerr=dissipated[T].e()[llow0[T]:lhigh0[T]],yerr=spectra[T][1].e()[llow0[T]:lhigh0[T]],
            #             c=cols[cnt],linestyle=' ')
            
            # show the whole range
            plt.errorbar(dissipated[T].v(),spectra[T][1].v(), 
                         xerr=dissipated[T].e(),yerr=spectra[T][1].e(),
                         c=cols[cnt],linestyle=' ')
            
        cnt += 3

    plt.title(title)
    plt.xlim(xlim3)
    plt.ylim(ylim3)
    plt.xlim()
    plt.xlabel('Dissipated power (W)')
    plt.ylabel('Wavelength (nm)')
    plt.grid('on')
    cnt = 0 # reset
    
    
    wavelength = ev.errvallist([q3[T] for T in plot_temps_for_3]) # wavelength offsets
    slopes = ev.errvallist([m3[T] for T in plot_temps_for_3]) # slopes
    T_active = ev.errvallist([T_out[T] for T in plot_temps_for_3])
    # Z = thermal_impedance(T_active,wavelength,slopes) # brute force approach
    #print T_active, wavelength, slopes
    
    dldD, dldT, l0 = thermal_resistance(T_active,wavelength,slopes) #, R_th
    R_th = dldD/dldT
    for T in Temperatures:
        if T in plot_temps_for_3:
            plt.plot(dissipated[T].v(),l0.v() + dldT.v()*T_out[T].v() + dldD.v()*dissipated[T].v(),c=cols[cnt+1])
        cnt+=3
    
    plt.text(textx3,texty3[0],
             '$\lambda=$'+'$({})$'.format(dldT.round(3))+'$T_{hs}+$'+'$({})$'.format(dldD.round(3))+'$D+$'+'${}$'.format(l0.round(3)),
             color='k')
    
    R_th = R_th.round(2)
    therm_imp = 'Thermal impedance: $({0})$ K/W'.format(R_th)
    plt.text(textx3,texty3[1],
             therm_imp,color='k')
    print therm_imp

    
    if use_realtemperatures:
        for T in Temperatures:
            print meantemp[T]
    
    plt.show()



if __name__ == "__main__":
    main()

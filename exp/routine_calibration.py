#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division # python 2.7 uses int-division, i.e. 3/4=0, python 3.x uses float division, what we want!

import sys
from os import path, makedirs
import time

import numpy as np
import matplotlib
import matplotlib.pyplot as plt


from VECSELsetup.meas import VECSELSetup as V
#from VECSELsetup.meas import VECSELSetupFake as V # activate in order to run a test round, without actually connecting the devices

from VECSELsetup.meas import RoutineFunctions as F
from VECSELsetup.meas import MeasurementProtocol as MP


#=======================================================================================

"""
IMPORTANT:
Note, this example routine is set up for a Windows machine.
For Mac and Linux you have to replace the r'\\' by r'/'; the two systems name directories differently.

Routine:

    User input:
        * samplename and folder where to store the measurement results;
          see documentation (or further below) what to do and how to name it
        * provide additional information about the particular measurement
        * define delay time between measurements
        * define number of repetitions; each pump power will be set this often, to get errorbars, to see how reliable the results are!
        * select laser_current (sth like range(0,N,st))
          note: you don't specify a temperature, because
            * calibration assumes to be performed at same temperature
            * don't need multiple temperatures.
        * define measurement experience:
          show plot before closing, or directly closing (data are saved beforehand)

    Storage principles:
        * measurements are logged in a logfile, in a main folder
        * measured data are stored in files, collected in a separate (sub-)folder
          this way the main folder looks clean: only the logfile and the corresponding (sub-)folders
          the files of measured data are large in number, humans don't need to dig through that:
          the logfile knows the filenames of these measurement files, during evaluation the eval-script will work with this

    Parameter preparation
        * duplicate laser_current by the number of repetition

    Init power meters (PMs) and power source (PS):
        PM: set number of averages, power auto range, wavelength
        PS: nothing to configure
            (set default values in VECSELSetup.py appropriately! (especially _max_curr))

    Actual routine:

    read temperatures
    for c in laser_current:
        set c
        read current (should be ==c)
        wait remaining delay
        measure PMs
    save measured values each in a separate file


    !!!    at any point of this routine the measurement has to be able to be cancled,       !!!
    !!!    on interruption, either willingly or because of what ever, the pump must go off! !!!
"""


def main():

    # for example calibration in eval/calibration.py we need the following 4 files, see documentation for what it means
    # '1_pump_calib.csv'
    # '2_refl_calib.csv'
    # '3_emission_calib.csv'
    # '4_emission_calib.csv'
    logfilename = '1_pump_calib.csv'
    path_to_meas_folder = r'C:\Users\KamilP\Desktop\VECSEL-LL\20150123_calib_333um'

    additional_info = 'thermal PM at pos 1, pump setting as ramp to decrease heat sink noise'

    # -----

    additional_info = additional_info.replace(';',',') # ; is reserved for separating the different header entries!
    pwr_folder = logfilename[:-4]+r'_pwr'

    delay_between_meas = 1 # s; between each pump power setting, pump irradiates during this time (i.e. heats!)
    n_repetitions = 3 # at each temperature each pump power will be applied this often; to get errorbars, to know how reliable the result is

    # pump power, in A:
    pump_start = 0 # A
    pump_end = 49 # A
    pump_npoints = 41

    # wavelengths (for power meters)
    lambda_pump = 980 # nm
    lambda_laser = 1265 # nm; 1270, 1530
    lambda_thermalpm = lambda_laser if (logfilename=='3_emission_calib.csv' or logfilename=='4_emission_calib.csv') else lambda_pump # settings for thermal power meter?

    plot_results = True # if True: plots results after every temperature AND BLOCKS WHILE DISPLAYING! (hence set to False when you want it to measure automated!)

    # ==========================================================================
    #
    # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
    #                      ! NO SETTINGS BELOW HERE !
    #                                 --
    #                    ! SPECIFY MEASUREMENT ABOVE !
    # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
    #
    # ==========================================================================
    t0 = time.time()

    # File name of log-file
    # individual measurements go in separate folder; to keep a clean directory.

    #path_to_meas_files = path_to_meas_folder+r'/pwr' # for Mac and Linux
    path_to_meas_files = path_to_meas_folder+r'\\'+pwr_folder
    if not path.exists(path_to_meas_files):
        makedirs(path_to_meas_files)


    laser_current = F.one_decimal( np.linspace(pump_start, pump_end, pump_npoints) )
    laser_current = list(laser_current)*n_repetitions # dirty but quick; works only for list's, numpy.array's actually multiply the value!
    #print laser_current


    # ==========================================================================
    #                           INIT
    # ==========================================================================

    rm = V.ResourceManager()

    hs = V.HeatSink(rm,u'GPIB0::5::INSTR')

    ps = V.PowerSource(rm,'ASRL1::INSTR')
    ps.set_max_current(pump_end) #in A


    # pump power
    pm_p = V.PowerMeter(rm,'USB0::0x1313::0x8072::P2003818::INSTR')
    pm_p.set_wavelength(lambda_pump)
    # reflected power
    pm_r = V.PowerMeter(rm,'USB0::0x1313::0x8072::P2003817::INSTR')
    pm_r.set_wavelength(lambda_pump)
    # emitted power
    pm_e = V.PowerMeter(rm,'USB0::0x1313::0x8078::P0004893::INSTR')
    pm_e.set_wavelength(lambda_thermalpm) # lambda_laser


    m_p = MP.Meter(pm_p,identifier='Pump',file_path=path_to_meas_files)
    m_r = MP.Meter(pm_r,identifier='Refl',file_path=path_to_meas_files)
    m_e = MP.Meter(pm_e,identifier='Laser',file_path=path_to_meas_files)

    meter_battery = [m_p,m_r,m_e] # m_p,m_r,m_e



    # ==========================================================================
    #                           ROUTINE
    # ==========================================================================

    try:
        print 'Start Routine.'
        logfile = open(path_to_meas_folder+r'\\'+logfilename,'wb')
        # logfile header: (order has to match order of writing in the end!)
        # `;` separates different sections of the header
        headstr = u'columns=Temp,Current,'
        for meter in meter_battery:
            headstr += u'{0},'.format(meter.identifier)
        headstr += u'Time_stamp'
        headstr += u';delay_between_meas={0}'.format(delay_between_meas)
        headstr += u';n_repetitions={0}'.format(n_repetitions)
        headstr += u';n_powermeters={0}'.format(len(meter_battery))
        headstr += u';pwr_folder={0}'.format(pwr_folder)
        headstr += u';logfile_version={0}'.format(1)
        headstr += u';add_info={0}'.format(additional_info)
        logfile.write(headstr+u'\n')


        T = hs.read_temperature()
        print 'At temperature', T


        # open new files to save the measurements; prepare with header.
        filename_prefix = '{0:03}_'.format(int(T*10)) # if this leads to non unique names you're scanning the temp unrealisticly tightly!
        for meter in meter_battery:
            print meter
            meter.open_file(filename_prefix)
        print 'Meter open.',
        ps_filename, ps_file = MP.open_power_source_file(ps,path_to_meas_files,T)
        print 'All files are open.'


        # measure to files
        print 'Measurement progress [%]:',
        j, ctot = 0, len(laser_current)
        t_m0 = time.time()
        ps.on()
        for c in laser_current: # note: for calibration we do not shuffle laser_current
            c_ = ps.set_current(c)
            print int(j/ctot*100*10)/10,
            j += 1
            ps_file.write(u'{0:.3f},{1:.3f}\n'.format(c,c_))
            time.sleep(np.max([0,delay_between_meas-(t_m0-time.time())]))
            for meter in meter_battery:
                meter.measure_to_file()
            t_m0 = time.time()
        ps.off()
        print ''
        print 'Written to files.',


        # write logfile and close files
        ps_file.close()
        logstr = u'{0},{1},'.format( T,ps_filename )
        for meter in meter_battery:
            logstr += '{0},'.format(meter.close_file()) # closing returns filename
        logstr += u'{0}'.format( time.time() )
        logfile.write(logstr+u'\n')
        logfile.close() # force it to write the buffer to the file; reopen with option 'a'!
        print 'Logfile writen, the calibration was measured in {0:.1f} s'.format(time.time()-t0)


        # Show results of this temperature
        # when doing so, wait for user interaction to continue
        if plot_results:
            fig = plt.figure()
            n = len(meter_battery)
            j = 1
            for meter in meter_battery:
                full_file_path = meter.full_file_path()
                res = MP.read_from_file(full_file_path,col=0,foo=float)
                ax = fig.add_subplot(n,1,j)
                ax.axis([pump_start, pump_end, min(res), max(res)])
                if j ==1: ax.set_title('Temperature: {0} $^\circ$C'.format(T))
                ax.scatter(laser_current, res)
                j += 1
            print 'Close plot to continue.'
            plt.show()



    except Exception, e:
        # whatever might go wrong, shut down the power source!
        # ... and raise the exception again, so we can see what went wrong.
        ps.close()
        raise Exception, e

    finally:
        logfile.close()
        ps.close()
        print 'Measurement finished in {0:.1f} s'.format(time.time()-t0)



if __name__ == '__main__': main()

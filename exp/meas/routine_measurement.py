#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division # python 2.7 uses int-division, i.e. 3/4=0, python 3.x uses float division, what we want!

import sys
from os import path, makedirs
import time

import numpy as np

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
        * samplename and folder where to store the measurement results
        * provide additional information about the particular measurement
        * define delay time between measurements
        * define number of repetitions; each pump power will be set this often, to get errorbars, to see how reliable the results are!
        * select temperatures and laser_current (sth like range(0,N,st))
        * define measurement experience, how things go concerning plotting and pump shuffle (see below)

    Storage principles:
        * measurements are logged in a logfile, in a main folder
        * measured data are stored in files, collected in a separate (sub-)folder
          this way the main folder looks clean: only the logfile and the corresponding (sub-)folders
          the files of measured data are large in number, humans don't need to dig through that:
          the logfile knows the filenames of these measurement files, during evaluation the eval-script will work with this

    Parameter preparation
        * multiply laser_current by the number of repetition
        * arange temperatures such that half of the points are visited on way up, other half on the way down:
          measure half and 'verify' with second half; up and down should be on same line unless we underestimated the influence of temp cycle
          to save time: wrap around room temperature, i.e. start at room temperature, go up, go down, come back to room temperature

    Init power meters (PMs) and power source (PS):
        PM: set number of averages, power auto range, wavelength
        PS: nothing to configure (?)
            (set default values in VECSELSetup.py appropriately! (especially _max_curr))

    Actual routine:

    for t in temperatures:
        heat_sink.set_temperature(t)
        shuffle laser_current; with random order we're less susceptible to temporal effects (e.g. heating of super high pump)
        for c in laser_current:
            set c
            read current (should be ==c)
            wait delay
            measure PMs
            measure spectrum
        save measured values each in a separate file


    !!!    at any point of this routine the measurement has to be able to be cancled,       !!!
    !!!    on interruption, either willingly or because of what ever, the pump must go off! !!!
"""


def main():

    #
    #                   DEFINE MEASUREMENT PARAMETERS:
    #

    samplename = 'spot333um' # logfile will be `samplename`.csv
    path_to_meas_folder = r'C:\Users\KamilP\Desktop\VECSEL-LL\20150124_detailed' # will be created if it doesn't exist yet

    # store more info about ongoing measurement
    # like: special type of lenses used? other optical elements?
    # may help finding a particular setting later on
    # leave empty otherwise (add_info = '')
    add_info = 'investigating the reflectance without output coupler, 45:75 imaging of 200um fiber results in 333um spot'

    # -----

    # sanitize additional info to store, specify sub-folders for measured data (not to clutter the human reader friendly held main folder)
    add_info = add_info.replace(';',',') # `;` is reserved for separating the different header entries!
    pwr_folder = samplename+r'_pwr' # here go all the files with measured data
    spectr_folder = samplename+r'_spec' # here go the raw data from spectrometer, distinctly different from '_pwr'

    # time and repetition
    # note: VECSELSetup.PowerSource already has a built-in delay, to ensure the requested current is applied.
    delay_between_meas = 1 # s; between each pump power setting, while irrradiating (i.e. structure heats up)
    n_repetitions = 5 # at each temperature each pump power will be applied this often; to get errorbars, to know how reliable the result is

    # heat sink instructions
    room_temperature = 5 # deg C, temp of heat sink at start: helps to optimize heating cycle
    heatsink_start = 15 # deg C
    heatsink_end = 35 # deg C
    heatsink_npoints = 3 # set '1' if only heatsink_start requested
    heatsink_wait_after_setting = 4*60 # s; how long to wait between querying the heat sink whether it has reached the requested temperature

    # pump power, in A: (check with specifications of pump diode and calibration what this translates into!)
    pump_start = 0 # A
    pump_end = 80 # A
    pump_npoints = 41

    # wavelengths (for power meters and spectrometer)
    lambda_pump = 980 # nm
    lambda_laser = 1265 # nm; 1270, 1530

    # spectrometer
    use_spectrometer = True
    lambda_span = 30 # nm; sym around lambda_laser
    spectrometer_sensitivity = -60 # dBm; set None for default value

    # define the measurement experience
    # - plotting:
    #    if True the script plots measured results after every temperature
    #    AND BLOCKS WHILE DISPLAYING(!), requires user to close the plot
    #    (set to False when you want it to measure automated!)
    #    useful to have a quick check of performance of temperature and the connected power meters
    #    (and abort if something is obviously wrong (like temperature was not stabilized etc.))
    # - pump shuffle:
    #    without a shuffle, the pump is applied in a ramp.
    #    the found results may depend on this very ramp.
    #    by shuffling, the results are independent on what setting was measured before.
    #    consequentially, the shuffle is more reliable.
    #    Also: average thermal load on heat sink is lower by shuffling
    #    shuffle is uninteresting for something like a calibration: there you want to have identical conditions
    plot_results = True
    shuffle_pump = True


    # pump heats the heat sink
    # apply the following amount of seconds of 0A before setting a new pump
    # this helps in order to cool down
    extra_cooling_delay = 0 #s


    # ==========================================================================
    #
    # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\
    #                      ! NO SETTINGS BELOW HERE !
    #                                 --
    #                    ! SPECIFY MEASUREMENT ABOVE !
    # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
    #
    # ==========================================================================
    t0 = time.time() # keep track of over all time required

    # individual measurements go in separate folder; to keep a clean directory.
    #path_to_meas_files = path_to_meas_folder+r'/pwr_folder' # on Mac and Linux
    path_to_meas_files = path_to_meas_folder+r'\\'+pwr_folder
    if not path.exists(path_to_meas_files):
        makedirs(path_to_meas_files)
    path_to_spec_files = path_to_meas_folder+r'\\'+spectr_folder
    if use_spectrometer and not path.exists(path_to_spec_files):
        makedirs(path_to_spec_files)

    # logfilename can be arbitratily complicated, we don't do that.
    logfilename = samplename + '.csv'
    #today = time.gmtime() # note: NOT local time, we don't want daylight-savings-time to mess up the name!
    #timestamp = '%04d%02d%02d-%02d%02d%02d' % (today.tm_year,today.tm_mon,today.tm_mday,today.tm_hour,today.tm_min,today.tm_sec)
    #logfilename = timestamp + '_' + samplename + '.csv'
    #print logfilename

    # parameter preparation of temperature and pump current
    # 1. duplicate currents as specified via n_repetitions
    # 2. arange temp such that half while up, other half while cooling down
    # => save time and verify heating cycle while cooling down

    temperatures = F.one_decimal( np.linspace(heatsink_start, heatsink_end, heatsink_npoints) )
    temperatures = F.wrap_around(temperatures,room_temperature) # comment out if you don't want it to wrap around
    #temperatures = [10.0, 11.0, 25.0, 26.0, 40.0, 41.0] # for manual intervention: no temperature twice! script will overwrite the measurements!
    print 'requested temperatures in degC:',temperatures # verify after measurement has started

    laser_current = F.one_decimal( np.linspace(pump_start, pump_end, pump_npoints) )
    laser_current = list(laser_current)*n_repetitions # dirty but quick; works only for list's, numpy.array's actually multiply the value!
    #print laser_current # verify after measurement has started


    # ==========================================================================
    #                           INIT
    # ==========================================================================

    rm = V.ResourceManager()

    ps = V.PowerSource(rm,'ASRL1::INSTR')
    ps.set_max_current(pump_end) #in A

    hs = V.HeatSink(rm,u'GPIB0::5::INSTR')

    if use_spectrometer:
        osa = V.SpectroMeter(rm,u'GPIB0::9::INSTR')
        osa.set_wavelength_center(lambda_laser)
        osa.set_wavelength_span(lambda_span)
        osa.set_sensitivity(spectrometer_sensitivity)
        sc = MP.SpectrumCollector(osa,identifier='OSA',meas_path=path_to_meas_files,spect_path=path_to_spec_files)

    # pump power
    pm_p = V.PowerMeter(rm,'USB0::0x1313::0x8072::P2003818::INSTR')
    pm_p.set_wavelength(lambda_pump)
    # reflected power
    pm_r = V.PowerMeter(rm,'USB0::0x1313::0x8072::P2003817::INSTR')
    pm_r.set_wavelength(lambda_pump)
    # emitted power
    pm_e = V.PowerMeter(rm,'USB0::0x1313::0x8078::P0004893::INSTR')
    pm_e.set_wavelength(lambda_laser)


    m_p = MP.Meter(pm_p,identifier='Pump',file_path=path_to_meas_files)
    m_r = MP.Meter(pm_r,identifier='Refl',file_path=path_to_meas_files)
    m_e = MP.Meter(pm_e,identifier='Laser',file_path=path_to_meas_files)

    meter_battery = [m_p,m_r,m_e]

    assert id(m_p)==id(meter_battery[0])


    # ==========================================================================
    #                           ROUTINE
    # ==========================================================================

    try:
        if plot_results:
            # supervision is required, otherwise the script blocks after the first temperature
            # that's a waste of electricity!
            # hence request answer from user to ensure (s)he is around:
            ans = raw_input(u'You invoked the results to be plotted after every temperature,\nare you sure you\'re around to look at them?')
            # an empty 'enter' is enough to aknowledge his/her presence, without: the script stops right here.

        print 'Start measurement.'
        logfile = open(path_to_meas_folder+r'\\'+logfilename,'wb')
        # logfile header: (order has to match order of writing in the end!)
        headstr = u'columns=Temp_set,Temp_accepted,Temp_elapsed,Temp_live,Current,'
        for meter in meter_battery:
            headstr += u'{0},'.format(meter.identifier)
        if use_spectrometer: headstr += u'Spectra,'
        headstr += u'Time_stamp'
        headstr += u';delay_between_meas={0}'.format(delay_between_meas)
        headstr += u';extra_cooling_delay={0}'.format(extra_cooling_delay)
        headstr += u';heatsink_wait_after_setting={0}'.format(heatsink_wait_after_setting)
        headstr += u';n_repetitions={0}'.format(n_repetitions)
        headstr += u';pwr_folder={0}'.format(pwr_folder)
        if use_spectrometer: headstr += u';spectr_folder={0}'.format(spectr_folder)
        headstr += u';add_info={0}'.format(add_info)
        headstr += u';logfile_version={0}'.format(4)
        logfile.write(headstr+u'\n')
        # As long as we don't close the file, the written content is kept in a buffer.
        # This buffer is only actually 'written' once the buffer is full.
        # Consequentially, if there is a power black out, the logfile doesn't contain all the entries it is supposed to contain.
        logfile.close()

        for T in temperatures:
            logfile = open(path_to_meas_folder+r'\\'+logfilename,'ab') # option 'a' let's us append to the already existing file ('w' overwrites.)
            print 'Setting temperature:',T,
            T_, T_time_elapsed = MP.wait_for_temperature(hs,T,wait=heatsink_wait_after_setting,report_progress=True)
            t1 = time.time() # this time allows us to identify the single files
            print 'successfully set:',T_,

            # open new files to save the measurements; prepare with header.
            filename_prefix = '{0:03}_'.format(int(T*10)) # if this leads to non unique names you're scanning the temp unrealisticly tightly!
            for meter in meter_battery:
                meter.open_file(filename_prefix)
            ps_filename, ps_file = MP.open_power_source_file(ps,path_to_meas_files,T)
            T_filename, T_file = MP.open_temp_log_file(hs,path_to_meas_files,T)
            if use_spectrometer: sc.open_collection(filename_prefix)
            print 'Files are open.',


            # measure to files
            print 'Measurement progress [%]:',
            j, ctot = 0, len(laser_current)
            if shuffle_pump: F.shuffle_list(laser_current) # shuffle to not depend on time dependent effects, repeat for each temperature anew!
            t_m0 = time.time()
            ps.on()
            for c in laser_current:
                if extra_cooling_delay>0:
                    textra0 = time.time()
                    cextra = ps.set_current(0)
                    time.sleep(np.max([0,extra_cooling_delay-(textra0-time.time())]))
                c_ = ps.set_current(c)
                print int(j/ctot*100*10)/10, # show progress of measurement; shows script is still alive
                j += 1
                ps_file.write(u'{0:.3f},{1:.3f}\n'.format(c,c_))
                if use_spectrometer: sc.open_spectrum_file(spectrum_identifier=u'{0:03}_{1:03}'.format(int(T*10),int(c*10)))
                time.sleep(np.max([0,delay_between_meas-(t_m0-time.time())]))

                for meter in meter_battery:
                    meter.measure_to_file()
                T_file.write(u'{0:.3f},{1}\n'.format(c,hs.read_temperature()))
                if use_spectrometer: sc.write_spectrum_file()

                t_m0 = time.time()
                if use_spectrometer: sc.write_collection_entry(c)
            ps.off()
            print 'written to files.',


            # write logfile entry and close files
            ps_file.close()
            T_file.close()
            logstr = u'{0},{1},{2:.1f},{3},{4},'.format( T,T_,T_time_elapsed,T_filename,ps_filename )
            for meter in meter_battery:
                logstr += '{0},'.format(meter.close_file()) # closing returns filename
            if use_spectrometer: logstr += u'{0},'.format(sc.close_collection())
            logstr += u'{0}'.format( time.time() )
            logfile.write(logstr+u'\n')
            logfile.close() # force it to write the buffer to the file; reopen with option 'a'!
            print 'Logfile written, Temperature set was measured in {0:.1f} s'.format(time.time()-t1)


            # Show results of this temperature
            # when doing so, wait for user interaction to continue
            # first subplot is temperature, then there are the power meters, in order of initialization
            if plot_results:
                fig = plt.figure()
                n = len(meter_battery)+1
                j = 1
                full_file_path = u'\\'.join([path_to_meas_files,T_filename])
                res = MP.read_from_file(full_file_path,col=1)
                ax = fig.add_subplot(n,1,j)
                ax.set_title('Temperature')
                ax.scatter(xrange(len(res)), res)
                j += 1
                for meter in meter_battery:
                    full_file_path = meter.full_file_path()
                    res = MP.read_from_file(full_file_path)
                    ax = fig.add_subplot(n,1,j)
                    ax.set_title(meter.identifier)
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
        hs.close()
        ps.close()
        if use_spectrometer: osa.close()
        print 'Measurement finished in {0:.1f} s'.format(time.time()-t0)



if __name__ == '__main__': main()

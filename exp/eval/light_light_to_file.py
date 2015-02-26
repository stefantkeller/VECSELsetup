#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from os import listdir
from os.path import exists
from sys import exit

import numpy as np
import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from VECSELsetup.eval.varycolor import varycolor
from VECSELsetup.eval.gen_functions import split2dict, sanitize, load, extract, lut_from_calibfolder, lut_interp_from_calibfolder, thermal_resistance

from calibrate import calibrate
import eval_spectra

'''
Most basic evaluation:
After you have finished a measurement
tell this script where to find the logfile of said measurement.
Additionally provide the path to the calib_folder;
i.e. the folder containing the calibrations measurements
as described in the documentation.

In the end you are going to obtain a file easily readable by for example Excel.
The first line, the header line, tells you what the columns mean.
Plus, the header provides you with all sorts of additional information.
'''


def main():
    logfile = r'/path/24_LL_ev/20150204_sample21-1-d6/spot333um.csv' # note: the r in front of the string is important!
    calib_folder = r'/path/24_LL_ev/20150204_calib_333um_s21-1-d6' # with the r'' notation the string is interpreted raw; as opposed to interpreting e.g. '\t' as a tabulator
    
    
    #------------------------------------
    #------------------------------------
    #------------------------------------
    #------------------------------------
    #------------------------------------

    # Windows can also handle '/', which is easier to deal with than '\', which needs escaping every now and then (i.e. '\\')
    logfile = logfile.replace('\\','/')
    calib_folder = calib_folder.replace('\\','/')

    # see whether calibration is already evaluated, do it if not
    if not exists(calib_folder+'/LUTs'):
        calibrate(calib_folder)
    else:
        print 'using calibration',calib_folder

    # see whether spectra are evaluated, do it if not
    with open(logfile, 'rb') as lf:
        log_header = lf.readline()
        hdict = split2dict(log_header, ';','=')
        columns = hdict['columns'].split(',')
    use_spectra = 'Spectra' in columns
    if use_spectra:
        logfile_root = '/'.join(logfile.split('/')[:-1])
        pwr_folder = sanitize(hdict['pwr_folder'])
        pwr_folder = '/'.join([logfile_root,pwr_folder])
        spectra_evaluated = eval_spectra.spectra_evaluated(pwr_folder)
        if not spectra_evaluated:
            eval_spectra.eval_spectra(logfile)

    # calibration
    emis_lut = lut_from_calibfolder(calib_folder,identifiers=['Laser'],ignore_error=False) # emission has constant value solely due to BS, no ND in front of detector etc.
    pump_lut, refl_lut = lut_interp_from_calibfolder(calib_folder,identifiers=['Pump','Refl'])
    
    
    #------------------------------------
    # load measurement
    if use_spectra:
        current_set, current, pump, refl, laser, spectra, meantemp = extract(logfile, identifiers=['Current','Pump','Refl','Laser','Spectra','Temperature'])
    else:
        current_set, current, pump, refl, laser, meantemp = extract(logfile, identifiers=['Current','Pump','Refl','Laser','Temperature'])
    Temperatures = sorted(current_set.keys()) # set temperatures (round numbers like 15.0 or 22.5 etc)

    #------------------------------------
    # calculate using calibration
    absorbed, reflected, emitted, pumped, dissipated = {}, {}, {}, {}, {}
    for T in Temperatures:
        reflected[T] = refl_lut(refl[T])
        pumped[T] = pump_lut(pump[T])
        absorbed[T] = pumped[T] - reflected[T]
        emitted[T] = emis_lut(laser[T])
        dissipated[T] = absorbed[T] - emitted[T]



    #------------------------------------
    #--------- WRITE FILE ---------------
    #------------------------------------

    eval_file_name = '.'.join(logfile.split('.')[:-1]) # discart last '.csv'
    eval_file_name = ''.join([eval_file_name,'_eval.csv'])
    print eval_file_name

    with open(eval_file_name, 'wb') as ef:
        new_columns = ','.join(['T_set','T_mean(degC)','dT_mean(degC)',
                                'current_set(A)','current(A)','dcurrent(A)',
                                'pumped(W)','dpumped(W)',
                                'reflected(W)','dreflected(W)',
                                'absorbed(W)','dabsorbed(W)',
                                'dissipated(W)','ddissipated(W)',
                                'emitted(W)','demitted(W)'])
        if use_spectra:
            new_columns = ','.join([new_columns,'lambda_short','dlambda_short','lambda_long','dlambda_long'])
        header = ';'.join([ 'columns={}'.format(new_columns),
                            'delay_between_meas={}'.format(hdict['delay_between_meas']),
                            'heatsink_wait_after_setting={}'.format(hdict['heatsink_wait_after_setting']),
                            'n_repetitions={}'.format(hdict['n_repetitions']),
                            'calib_folder={}'.format(calib_folder),
                            'logfile={}'.format(logfile),
                            'add_info={}'.format(hdict['add_info'])
                           ])
        header = ''.join([header,'\n']) # finish line.
        ef.write(header)
        for T in Temperatures:
            for j in xrange(len(current[T])):
                # note: `` converts numbers into writable text
                line = ','.join([`T`,`meantemp[T].v()`,`meantemp[T].e()`,
                                 `current_set[T][j]`,`current[T][j].v()`,`current[T][j].e()`,
                                 `pumped[T][j].v()`,`pumped[T][j].e()`,
                                 `reflected[T][j].v()`,`reflected[T][j].e()`,
                                 `absorbed[T][j].v()`,`absorbed[T][j].e()`,
                                 `dissipated[T][j].v()`,`dissipated[T][j].e()`,
                                 `emitted[T][j].v()`,`emitted[T][j].e()`
                                ])
                if use_spectra:
                    line = ','.join([line,`spectra[T][0][j].v()`,`spectra[T][0][j].e()`, # shortest emitted wavelength
                                          `spectra[T][1][j].v()`,`spectra[T][1][j].e()` # longest emitted wavelength
                                    ])
                line = ''.join([line,'\n']) # finish line.
                ef.write(line)


if __name__ == "__main__":
    main()

#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from os import makedirs
from os.path import exists

#from calibration.calib_pump import calibrate_pump
from calibration.calib_highpower_pump import calibrate_pump
from calibration.calib_reflection import calibrate_reflection
from calibration.calib_emission import calibrate_emission
from calibration.calib_current import check_current_integrity
from calibration.calib_report import write_report # needs LaTeX

from sys import exit

'''
The calibration needs the following 4 files.
With the routine described in exp/meas/routine_calibration.py you're covered.
In order to write the report as a very last step, this script assumed LaTeX to be installed (pdflatex);
modify exp/eval/calibration/calib_report.py if you want to write it differently.
  * '1_pump_calib.csv'
  * '2_refl_calib.csv'
  * '3_emission_calib.csv'
  * '4_emission_calib.csv'

  '1_pump_calib.csv':
    Place the thermal power meter at the sample position; position 1.
    Choose the variable pump_end equal to the pump current corresponding to the maximally allowed pump power (or less, to be on the safe side).
    (Note: pump_end will be lower than the maximum pump during actual operation.
    This is made possible because there is a linear relation between pump current and the power seen at position 1.
    We're going to extrapolate based on this linear relationship. Ensure yourself, this is actually linear!
    (Otherwise you have to find a new solution how to do the job.))

  '2_refl_calib.csv':
    Thermal power meter goes in the reflection channel, between collimating lens and beam sampler; position 2.
    Variable pump_end now determines up to what power you can calibrate the setup over all.
    Make sure the power exposure at this point doesn't exceed the power range of the power meter.
    Caveat: If you replace the sample under test without changing the alignment you can in principle use an old calibration.
    But, if this sample has a higher reflectivity, you run the risk of entering an uncalibrated range.

  '3_emission_calib.csv':
    Thermal power meter goes at its final position in the laser emission path; position 3.

  '4_emission_calib.csv':
    Thermal power meter goes at its final position in the laser emission path; position 3.
    The difference to measurement 3: now there is also the beam sampler extracting a fraction of the light for the spectrometer.
    Measurement 3 and 4 allow you to find the influence of said beam sampler.

In practice you will probably gather these four measurement in reverse order.
After you have conducted the measurements (e.g. with routine_measurement.py), you run this script for 4, remove the spectrometer beam sampler and measure 3, and so on.
This way you're sure to account for the actual alignment present during the measurements.
'''

def calibrate(calib_folder):

    # ---------------------------------------------
    
    
    logfile1 = calib_folder+'/1_pump_calib.csv' # thermal PM at sample pos (pos 1)
    logfile2 = calib_folder+'/2_refl_calib.csv' # thermal PM detecting full reflection (no optical elements in between; pos 2)
    logfile3 = calib_folder+'/3_emission_calib.csv' # thermal PM directly behind OC (no additional opt. el.; pos 3)
    logfile4 = calib_folder+'/4_emission_calib.csv' # thermal PM at real pos (pos 4)
    
    pumplog2 = logfile2 # which file contains the full range for pump P-I conversion?
    
    lut_folder = calib_folder+'/LUTs'
    
    # calibrate pump
    # calibrate refl
    # calibrate emission
    # check current integrity
    # give:
    #   logfile with data needed for the calib
    #   names for output files
    # return:
    #   void, it prints out a message about what files were written
    
    if not exists(lut_folder):
        makedirs(lut_folder)
        
    calibfile_pp = lut_folder+'/calib_pump.csv'
    calibplot_pp = lut_folder+'/calib_pump.png'
    calibfile_cp = lut_folder+'/calib_pump_current.csv'
    calibplot_cp = lut_folder+'/calib_pump_current.png'
    
    calibfile_r = lut_folder+'/calib_reflection.csv'
    calibplot_r = lut_folder+'/calib_reflection.png'
    
    calibfile_e = lut_folder+'/calib_emission.csv'
    calibplot_e = lut_folder+'/calib_emission.png'
    
    calibplot_c = lut_folder+'/calib_current.png'
    
    plot_list = []
    
    print ''
    print 'calibrate pump'
    if exists(logfile1) and exists(pumplog2):
        plot_list.append(calibplot_pp)
        plot_list.append(calibplot_cp)
        calibrate_pump(logfile1,pumplog2,calibfile_pp,calibplot_pp,calibfile_cp,calibplot_cp)
    else:
        print 'No file available for pump calibration; omitted.'
    
    print ''
    print 'calibrate refl'
    if exists(logfile2) and exists(logfile3):
        plot_list.append(calibplot_r)
        calibrate_reflection(logfile2,logfile3,calibfile_r,calibplot_r)
    else:
        print 'No files available for reflection calibration; omitted.'
    
    print ''
    print 'calibrate emission'
    if exists(logfile3) and exists(logfile4):
        plot_list.append(calibplot_e)
        calibrate_emission(logfile3,logfile4,calibfile_e,calibplot_e)
    else:
        print 'No files available for emission calibration; omitted.'
    
    print ''
    print 'check current integrity'
    logfiles = []
    if exists(logfile1): logfiles.append(logfile1)
    if exists(logfile2): logfiles.append(logfile2)
    if exists(logfile3): logfiles.append(logfile3)
    if exists(logfile4): logfiles.append(logfile4)
    if len(logfiles)>0:
        plot_list.append(calibplot_c)
        check_current_integrity(logfiles,calibplot_c)
    else:
        print 'No file available for current integrity check; omitted.'

    # summarize in pdf
    if len(plot_list)>0:
        write_report(plot_list)
    else:
        print 'No plots to plot, no report printed.'

def main():
    calib_folder = '20150123_calib_333um'
    calibrate(calib_folder)


if __name__ == "__main__":
    main()

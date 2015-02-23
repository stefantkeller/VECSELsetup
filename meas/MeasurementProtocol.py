#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

'''
While VECSELSetup.py provides control over the hardware,
this module provides functionallities to connect the hardware
with something useful: Write recorded measurements to files.

As a result in the measurement routine you will have to
initiate the hardware connection (using VECSELSetup),
connect the hardware with one of the following objects,
and then, throughout the rest of the routine
you will simply talk with these latter objects.
Under the hood hardware and recording are detached from each other,
but in the code you won't feel this.

See exp/ for examples.


IMPORTANT:
Note, in the current state this is set up for a Windows machine.
For Mac and Linux you have to replace r'\\' by r'/'; the two systems name directories differently.

'''

from __future__ import division # old: int division (1/4=0); future: float division (1/4=0.25)

import time
import csv
import numpy as np


class Meter(object):
    def __init__(self,PowerMeter,identifier='',file_path=''):
        # PowerMeter, an instance from VECSELSetup, or from VECSELSetupFake for testing
        # identifier and file_path, in order for this object to know where and under what name to save the recorded data
        self._pm = PowerMeter
        self.identifier = identifier

        self._file_path = file_path
        self._filename = None
        self._full_file_path = None


    def __str__(self):
        return ';'.join([self._pm._idn,self._pm._sens,self.identifier])

    def open_file(self,filename_prefix):
        self._filename = filename_prefix+self.identifier+r'.csv'
        self._full_file_path = self._file_path+u'\\'+self._filename
        self._file = open(self._full_file_path,'wb')
        self._file.write(r'columns=Power(W),time_measured(s);') # what the columns in this file correspond to
        self._file.write(r';'.join(self._pm.get_statset())) # write header
        self._file.write(r';time_stamp={0}'.format(time.time())+u'\n') # timestamp and close the line

    def close_file(self):
        self._file.close()
        return self._filename

    def measure_to_file(self):
        res, timing = self._pm.measure(timed=True)
        self._file.write(u'{0},{1:.3f}\n'.format(res,timing))
        return res

    def full_file_path(self):
        return self._full_file_path

class SpectrumCollector(object):
    def __init__(self,SpectroMeter,identifier='',meas_path='',spect_path=''):
        # SpectroMeter, an instance from VECSELSetup, or from VECSELSetupFake for testing
        self._osa = SpectroMeter
        self.identifier = identifier
        self._counter = None

        self._collection_path = meas_path # this file contains filenames corresponding to the spectra of the single current
        self._collection_filename = None
        self._full_file_path_collection = None
        self.wavelength_start, self.wavelength_stop = None, None # gets refreshed everytime a new collection is opened

        self._spectra_path = spect_path # here the files containing the actual spectra data are stored
        self._spectra_filename = None
        self._full_file_path_spectra = None
        self._timing = None

    def open_collection(self,filename_prefix=''):
        self._collection_filename = filename_prefix+self.identifier+r'.csv'
        self._full_file_path_collection = self._collection_path+u'\\'+self._collection_filename
        self._collection = open(self._full_file_path_collection,'wb')
        self._collection.write(r'columns=Current(A),Spectrum,TimeRequired(s);') # what the columns in the collection file mean
        self._collection.write(r';'.join(self._osa.get_statset()))
        self._collection.write(r';time_stamp={0}'.format(time.time())+u'\n') # timestamp and close the line
        self.wavelength_start, self.wavelength_stop = self._osa.read_wavelength_range() # in m
        self._counter = 0

    def write_collection_entry(self,current):
        self._collection.write(u'{0},{1},{2}\n'.format(current,self._spectra_filename,self._timing))

    def open_spectrum_file(self,spectrum_identifier):
        self._counter += 1 # this counter causes the files in the spectra folder to be in the same order as in the collection file:
        self._spectra_filename = spectrum_identifier+'_{0:03}'.format(self._counter)+r'.csv' # numbering with leading 0's, differentiating with counter to be absolutely sure not to overwrite another measurement
        self._full_file_path_spectra = self._spectra_path+u'\\'+self._spectra_filename
        self._spectrum = open(self._full_file_path_spectra,'wb')
        self._spectrum.write(u'Wavelength(nm),Amplitude(dBm),parent={0}\n'.format(self._collection_filename))

    def write_spectrum_file(self):
        res, self._timing = self._osa.measure(timed=True)
        n = len(res)
        wl = np.linspace(self.wavelength_start*1e9,self.wavelength_stop*1e9,n) # nm
        for j in xrange(n):
            self._spectrum.write(u'{0},{1}\n'.format(wl[j],res[j]))
        self._spectrum.close()

    def close_collection(self):
        self._collection.close()
        return self._collection_filename


def wait_for_temperature(HeatSink,T,wait=60,tolerance=3,timeout=2*3600,report_progress=False):
    # HeatSink, an instance from VECSELSetup, or from VECSELSetupFake for testing
    # T: requested temperature (in deg C)
    # wait (in s): time in s to wait before new temperature is probed
    # tolerance (in deg C): T is assumed to be reached once it is within T+-tolerance
    # timeout (in s): if temperature is not reached within timeout an error is issued
    t0 = time.time()
    if report_progress: print '' # a new line
    actual_T = HeatSink.set_temperature(T)
    while( np.abs(actual_T-T)>tolerance ):
        if report_progress: print actual_T,
        time.sleep(wait)
        actual_T = HeatSink.read_temperature()
        elapsed = time.time()-t0
        if elapsed>timeout:
            raise RuntimeError, 'HeatSink couldn\'t reach requested temperature within appropriate time; time elapsed: {0}'

    # temp is reached, wait again to be sure (might just have scratched the tolerance)
    if report_progress: print '' # a new line
    time.sleep(wait/2.0)
    actual_T = HeatSink.read_temperature()

    return actual_T, time.time()-t0


def open_power_source_file(PowerSource,path,temp):
    filename = '{0:03}_sourcecurrent.csv'.format(int(temp*10))
    file = open(path+u'\\'+filename,'wb')
    file.write(r'columns=set_current(A),actual_current(A);') # what the columns in this file correspond to
    statset = PowerSource.get_statset()
    file.write(r';'.join(statset)) # write header
    file.write(r';time_stamp={0}'.format(time.time())+u'\n') # timestamp and close the line
    return filename, file

def open_temp_log_file(HeatSink,path,temp):
    # temp for name identifier and so that args are identical with power_source file
    filename = '{0:03}_templogger.csv'.format(int(temp*10))
    file = open(u'\\'.join([path,filename]),'wb')
    file.write(r'columns=set_current(A),heat_sink(degC)') # what the columns in this file correspond to
    file.write(r';time_stamp={0}'.format(time.time())+u'\n') # timestamp and close the line
    return filename, file

def read_from_file(full_file_path,col=0,foo=lambda x:x):
    # foo: function to apply on every entry, e.g. float(); default is to do nothing
    _file = open(full_file_path,'rb')
    _file.readline() # skip header
    cf = csv.reader(_file,delimiter=',')
    res = []
    for row in cf:
        res.append(foo(row[col]))
    _file.close()
    return res

#=======================================================================================


def main():
    import VECSELSetupFake as V # test only with fake setup.
    pm = V.PowerMeter('','')
    test = Meter(pm,'test',r'C:\temp\')
    test.open_file('10_')
    test.measure_to_file()
    print test.close_file()
    print 'done'


if __name__ == '__main__': main()

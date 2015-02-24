#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division


import sys
from os import path, makedirs
import time


from VECSELsetup.meas import VECSELSetup as V
#from VECSELsetup.meas import VECSELSetupFake as V # activate in order to run a test round, without actually connecting the devices

from VECSELsetup.meas import RoutineFunctions as F
from VECSELsetup.meas import MeasurementProtocol as MP

'''
A low weight temperature logger
to demonstrates the simplest of available devices: the HeatSink
See also temp_logger_reader.py in order to read out the stored data.
'''

def main():
    measure_every_n_seconds = 120

    logfile_path = r'C:\Users\KamilP\Desktop\PyMeasurements\Meas\20150124_temp_loger.csv'

    with open(logfile_path, 'wb') as logfile:
        logfile.write(u'Logging temperature in interval of .. seconds: {0}\n'.format(measure_every_n_seconds))
        logfile.close()

        rm = V.ResourceManager()
        hs = V.HeatSink(rm,u'GPIB0::5::INSTR')

        j = 0
        print u'Start; In order to stop: click the red rectangle. This causes a KeyboardInterrupt...\nThe file is saved after every measurement, no data will be lost.'
        while True: #(j*measure_every_n_seconds <= measure_total_seconds):
            logfile = open(logfile_path, 'ab')
            logfile.write(u'{0},{1}\n'.format(time.time(),hs.read_temperature()))
            logfile.close()
            if j%30==0: print j/30,
            j += 1
            time.sleep(measure_every_n_seconds)
    print 'done'


if __name__ == '__main__': main()

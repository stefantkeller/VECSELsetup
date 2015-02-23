#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from __future__ import division # old: int division (1/4=0); future: float division (1/4=0.25)

import time
import numpy as np

"""
Fake VISA devices provides possibility to test code without actually connecting to the devices.
The following mocks have implemented the same commands as the real ones in VECSELSetup.py
"""

class PowerMeter(object):
    def __init__(self,resourcemanager,address):
        self._idn = 'PM-idn' # identification code of meter itself
        self._sens = 'SENS-idn' # id of sensor attached


    def __str__(self):
        return ';'.join([self._idn,self._sens])

    def get_statset(self):
        # information you want to save along with the measurements (header...)
        info = [r'*IDN?={0}'.format(self._idn),
                r'SYSTEM:SENSOR:IDN?={0}'.format(self._sens)]

        return info

    def average_over(self,N=1):
        read = N
        return read

    def set_wavelength(self,lambd=1270):
        read = lambd
        return read

    def measure(self,timed=True):
        # if timed: return yields measured result AND time it needed to execute
        t0 = time.time() # init for case of exception
        if timed:
            t0 = time.time()
            return np.random.random(), time.time()-t0
        else:
            return np.random.random()



class PowerSource(object):
    def __init__(self,resourcemanager,address):
        self._termination_char = u'\r' # \r or \n; for writing; \n seems not to work?!
        self._query_delay = 0.1 # time in s between write and read when query
        self._read_n = 500 # read raw so many bytes (or until machine sends nothing new anymore... 500 is way more than enough.)

        self._curr_max = 0.5 # safety measure, max allowed current (in A)

        self._las = 0

        self._port = 'COM1'
        self._name = 'ASLR::INSTR'

    def get_statset(self):
        # info about the current state, stuff that belongs in a file header
        info = []
        info.append('LMO={0}'.format(self._query('get LMO')))
        info.append('LCL={0}'.format(self._query('get LCL')))
        info.append('AT1={0}'.format(self._query('get AT1')))
        info.append('baudrate={0}'.format(r'9600\r'))
        info.append('data_bits={0}'.format(r'8\r'))
        info.append('parity={0}'.format(r'0\r'))
        info.append('stop_bits={0}'.format(r'8\r'))
        info.append('timeout={0}'.format(r'2000\r'))
        info.append('ERR={0}'.format(r'0\r'))

        return info

    def __str__(self):
        return ';'.join([self._port,self._name])

    def _query(self,msg):
        return msg

    def _write(self,msg):
        pass

    def close(self):
        print 'PowerSource closed'

    def on(self):
        # open shutter to turn on laser
        state = self._las
        if state == 0: # device currently off
            self._las = 1 # toggle 'on'
        elif state != 1: # if not off, it's on, nothing to toggle; however, if parsing results something strange turn off power
            self.close()
            raise IOError, 'Received unexpected state while turning laser ON: {0}'.format(state)
        return state

    def off(self):
        # close shutter; turn off laser
        self.set_current(0)
        state = self._las
        if state == 1: # device currently on
            self._las = 0 # toggle 'off'
        elif state != 0: # if not on, it's off, nothing to toggle; however, if parsing results something strange report!
            self.close()
            raise IOError, 'Received unexpected state while turning laser OFF: {0}'.format(state)
        return state

    def set_max_current(self,maxcurr=0):
        return maxcurr

    def set_current(self,curr=0):
        # if something goes wrong current is set to 0, the port is closed and the causing error raised again.
        # returns actual current (actual and set may differ a bit.)
        try:
            curr = np.min([self._curr_max,curr])
            # returns set value (supposed to be identical to curr)
            time.sleep(self._query_delay)
            ans = self.read_current()
            return ans
        except Exception as e:
            # whatever you have in here must be safe!
            # don't call self.off(): it calls set_current(0) and goes in recusion limbo
            self.close()
            raise Exception, e

    def read_current(self):
        return 0.0

    def read_power_internal(self):
        return 0.0

    def read_error(self):
        return 0

    def read_cooler(self):
        return 19.9


class SpectroMeter(object):
    def __init__(self,resourcemanager,address):
        self._query_delay = 0.1 # time in s between write and read when query
        self._read_n = 50

        self._res_name = 'Spectrometer'
        self._dev_name = self._query('ID?') # see also CONFIG?

        self._centerwl = None
        self._span = None


    def get_statset(self):
        # info about the current state, stuff that belongs in a file header
        info = [self._res_name,self._dev_name]
        info.append('AUNITS?={0}'.format(self._query('AUNITS?'))) # DBM, DBMV, DBUV, V, W
        info.append('CENTERWL?={0}'.format(self._query('CENTERWL?')))
        info.append('RB?(ResBandwidth)(nm)={0}'.format(self._query('RB?')))
        info.append('RL?(ReferenceLevel)(dBm)={0}'.format(self._query('RL?')))
        info.append('RLPOS?(PositionRL)={0}'.format(self._query('RLPOS?'))) # no idea what it means
        info.append('ROFFSET?(dB)={0}'.format(self._query('ROFFSET?')))
        info.append('SENSitivity?(dBm)={0}'.format(self._query('SENS?'))) # note: results are always returned in dBm regardless of the value set by AUNITS
        info.append('SPan?(nm)={0}'.format(self._query('SP?'))) # SP = wstop - wstart

        return info

    def __str__(self):
        return ';'.join([self._res_name,self._dev_name])

    def _query(self,msg):
        return msg

    def _write(self,msg):
        pass

    def close(self):
        pass

    def set_wavelength_center(self,lambd):
        self._centerwl = lambd
        return lambd

    def set_wavelength_span(self,span):
        self._span = span
        return span

    def read_wavelength_range(self):
        return [int(self._centerwl-self._span/2),int(self._centerwl+self._span/2)]

    def measure(self,timed=True):
        # if timed: return yields measured result AND time it needed to execute
        t0 = time.time() # init for case of exception
        if timed:
            t0 = time.time()
            return np.random.random(self._read_n), time.time()-t0
        else:
            return np.random.random(self._read_n)


class HeatSink(object):
    def __init__(self,dev,address):
        self._room_temperature = 20 # deg C
        self._temperature = 0
        self._temp_set = time.time()
        self._wait = 2 # s

    def __str__(self):
        return ''

    def set_temperature(self,T=None):
        #if T is None: T=self._room_temperature
        if T is not None:
            self._temperature = T
            self._temp_set = time.time()
        return self.read_temperature()

    def read_temperature(self):
        temperature = self._room_temperature
        now = time.time()
        if now-self._temp_set>self._wait: # implement a time delay, like the real device would cause
            temperature = self._temperature
        return temperature

    def close(self):
        pass

#=======================================================================================

ResourceManager = lambda : [] # need a dummy object to hand over

def main():
    pass


if __name__ == '__main__': main()

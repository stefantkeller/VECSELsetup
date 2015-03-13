#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

'''
Note:
The objects defined in this file talk with actual hardware.
If you are testing a measurement routine,
whether it works in principle,
you do NOT want to import this module.
In that case, import 'VECSELSetupFake' instead.
It provides you with some mocks,
that act as if you were connecting with the hardware
(while accepting the same comands),
without the need of a working connection.
'''

from __future__ import division # old: int division (1/4=0); future: float division (1/4=0.25)

import time
import numpy as np
import visa # Virtual Instrument Software Architecture to control e.g. GPIB, RS232, USB, Ethernet
from pyvisa import constants as C

vparse = lambda s, n=1: str(s)[:-n] # visa queries end with '\n', we don't want that, hence omit the last character

class PowerMeter(object):
    def __init__(self,resourcemanager,address):
        _pm = resourcemanager.open_resource(address)
        _pm.write(r'*CLS') # clear status; all event registers and error queue
        _pm.write(r'SENSE:POWER:AUTO ON') # legacy decision, inherited from .vi document passed down for generations (...or something like thats)
        _pm.write(r'SENS:AVERAGE 200') # default value

        self._idn = vparse(_pm.query(r'*IDN?')) # identification code of meter itself
        self._sens = vparse(_pm.query(r'SYSTEM:SENSOR:IDN?')) # id of sensor attached
        self._pm = _pm

    def __str__(self):
        return ';'.join([self._idn,self._sens])

    def get_statset(self):
        # information you want to save along with the measurements (header...)
        info = [r'*IDN?={0}'.format(self._idn),
                r'SYSTEM:SENSOR:IDN?={0}'.format(self._sens)]

        comands = [r'SENS:AVERAGE?', # averaging rate
                   r'SENS:CORRECTION?', # is there an attenuation factor?
                   #r'SENS:CORRECTION:BEAMDIAMETER?', # sensor aperture?
                   r'SENS:CORRECTION:WAVELENGTH?', # operation wavelength
                   r'SENS:POWER:REF?', # queries the delta reference value
                   r'SENS:POWER:REF:STATE?'] # queries the delta mode state

        nonasciicmd = [r'SENS:POWER:UNIT?', # W or dBm
                       r'CONFIGURE?'] # query the current measurement configuration (for a power meter that should read POW)

        for cmd in comands:
            info.append(cmd+'={0}'.format(self._pm.query_ascii_values(cmd)[0]))
        for cmd in nonasciicmd:
            info.append(cmd+'={0}'.format(vparse(self._pm.query(cmd))))

        return info

    def average_over(self,N=1):
        # according to specs 1 sample takes approx 3 ms
        self._pm.write(r'SENS:AVERAGE {0}'.format(N)) # set...
        read = self._pm.query_ascii_values(r'SENS:AVERAGE?')[0] # ...and ask what is newly set value
        return read

    def set_wavelength(self,lambd=1270):
        # wavelength in nm!
        self._pm.write(r'SENS:CORRECTION:WAVELENGTH {0}'.format(lambd))
        read = self._pm.query_ascii_values(r'SENS:CORRECTION:WAVELENGTH?')[0]
        return read

    def measure(self,timed=True):
        # if timed: return yields measured result AND time it needed to execute
        t0 = time.time() # init for case of exception
        if timed:
            t0 = time.time()
            return self._pm.query_ascii_values(r'MEASURE?')[0], time.time()-t0
        else:
            return self._pm.query_ascii_values(r'MEASURE?')[0]



class PowerSource(object):
    def __init__(self,resourcemanager,address):
        self._termination_char = u'\r' # \r or \n; for writing; \n seems not to work?!
        self._query_delay = 0.1 # time in s between write and read when query
        self._read_n = 500 # read raw so many bytes (or until machine sends nothing new anymore... 500 is way more than enough.)

        self._curr_max = 0.5 # safety measure, max allowed current (in A)
        self._delay_set_current = 2 # s; to wait between setting current and reading actually achieved value

        _ps = resourcemanager.open_resource(address)
        _ps = self._set_attributes(_ps)
        self._ps = _ps
        self._write('set ERR 0') # clear whatever was in the pipe before
        self._write('set LMO 0') # laser mode: CW
        self.set_current(0) # cancel whatever was on last at everytime we init the source
        lcl = self.set_max_current(self._curr_max)
        #print lcl

        self._port = _ps.resource_info[0].alias
        self._name = _ps.resource_info[0].resource_name


    def _set_attributes(self,_ps):
        # find name and flag of attributes with
        # "All Programs -> National Instruments -> VISA -> VISA Interactive Control"
        # here following the set attributes found with this app
        # if it works: accept the black magic and don't change anything!
        # if it doesn't... well... I hope you have no plans tonight
        #
        # the first settings come from the manual (unclear where to find it if you don't have it already, though)
        # laser-electronics.de
        # Laser Diode Control LDC 1000
        # Operating Instructions
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_BAUD,9600) # baud rate
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_DATA_BITS,8)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_PARITY,0) # 0 := none
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_STOP_BITS,10) # 10 = 1
        _ps.set_visa_attribute(C.VI_ATTR_TMO_VALUE,2000) # 2000 ms timeout

        #_ps.query_delay = 0.1 # time in s between write and read when query


        if self._termination_char == u'\r':
            _ps.set_visa_attribute(C.VI_ATTR_TERMCHAR,int(u'0xD',base=16)) # end lines with \n (=0xA) or \r (=0xD)
        elif termination_char == u'\n':
            _ps.set_visa_attribute(C.VI_ATTR_TERMCHAR,int(u'0xA',base=16)) # end lines with \n (=0xA) or \r (=0xD)
        else:
            raise NotImplementedError, r'As termination character choose either \n or \r; support for custom termination is not implemented.'
        _ps.write_termination = self._termination_char

        _ps.set_visa_attribute(C.VI_ATTR_TERMCHAR_EN,C.VI_TRUE) # enable termchar
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_END_IN,C.VI_ASRL_END_TERMCHAR) # end mode for reads (not clear whether 'read' by us or the machine)
        _ps.set_visa_attribute(C.VI_ATTR_IO_PROT,C.VI_PROT_NORMAL) # VI_PROT_NORMAL or VI_PROT_4882_STR

        # from partially working LabView vi:
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_FLOW_CNTRL,C.VI_ASRL_FLOW_XON_XOFF)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_XON_CHAR,17) # no explanation for the value
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_XOFF_CHAR,19) # same
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_DTR_STATE,C.VI_STATE_UNASSERTED)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_RTS_STATE,C.VI_STATE_ASSERTED)

        # attributes of unknown importance and actual meaning:
        _ps.set_visa_attribute(C.VI_ATTR_DMA_ALLOW_EN,C.VI_FALSE)
        _ps.set_visa_attribute(C.VI_ATTR_SUPPRESS_END_EN,C.VI_FALSE)
        _ps.set_visa_attribute(C.VI_ATTR_FILE_APPEND_EN,C.VI_FALSE)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_REPLACE_CHAR,int(u'0x0',base=16)) # sth with error handling
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_DISCARD_NULL,C.VI_FALSE)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_BREAK_LEN,250)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_ALLOW_TRANSMIT,C.VI_TRUE)
        _ps.set_visa_attribute(C.VI_ATTR_ASRL_BREAK_STATE,C.VI_STATE_UNASSERTED)
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_WIRE_MODE,C.VI_ASRL_232_DTE) # doesn't exist
        # read only(?)
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_CTS_STATE,C.VI_STATE_UNASSERTED)
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_DCD_STATE,C.VI_STATE_UNASSERTED)
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_DSR_STATE,C.VI_STATE_UNASSERTED)
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_RI_STATE,C.VI_STATE_UNASSERTED)

        # enable reading when received termination character
        # doesn't work because device sends inconsistent combinations of \n and \r
        # .. read raw!
        #_ps.set_visa_attribute(C.VI_ATTR_SEND_END_EN,C.VI_TRUE)
        #_ps.read_termination = self._termination_char # this machine returns random terminations: \r and \n mixed. read it "raw" and parse it from there!
        #_ps.set_visa_attribute(C.VI_ATTR_ASRL_END_OUT,C.VI_ASRL_END_TERMCHAR) #end mode for writes

        return _ps

    def get_statset(self):
        # info about the current state, stuff that belongs in a file header
        info = [r'alias={0}'.format(self._port),r'resource_name={0}'.format(self._name)]
        info.append(r'delay_set_current={0}'.format(self._delay_set_current))
        info.append(r'LMO={0}'.format(self._query('get LMO')))
        info.append(r'LCL={0}'.format(self._query('get LCL')))
        info.append(r'AT1={0}'.format(self._query('get AT1').replace('\xb0','')))
        info.append(r'baudrate={0}'.format(self._ps.get_visa_attribute(C.VI_ATTR_ASRL_BAUD)))
        info.append(r'data_bits={0}'.format(self._ps.get_visa_attribute(C.VI_ATTR_ASRL_DATA_BITS)))
        info.append(r'parity={0}'.format(self._ps.get_visa_attribute(C.VI_ATTR_ASRL_PARITY)))
        info.append(r'stop_bits={0}'.format(self._ps.get_visa_attribute(C.VI_ATTR_ASRL_STOP_BITS)))
        info.append(r'timeout={0}'.format(self._ps.get_visa_attribute(C.VI_ATTR_TMO_VALUE)))
        info.append(r'ERR={0}'.format(self._query('get ERR')))

        # sanitize entries
        info = [i.replace('\n','') for i in info]
        info = [i.replace('\r','') for i in info]
        return info

    def __str__(self):
        return ';'.join([self._port,self._name])

    def _query(self,msg):
        self._ps.write(unicode(msg))
        time.sleep(self._query_delay)
        return self._ps.read_raw(self._read_n)

    def _write(self,msg):
        time.sleep(self._query_delay) # give it time to process the old orders.
        self._ps.write(unicode(msg))

    def close(self):
        # whatever you have in here must be safe!
        # release lock on seial port
        # write may fail but any such error is held back in the buffer;
        # query('get ERR') to see
        # BUT: don't query in here, 'read' MAY cause a problem
        self._write('set SLC 0')
        self._ps.close()

    def on(self):
        # open shutter to turn on laser
        err = self.read_error()
        state = float(self._query('get LAS'))
        if state == 0 and err == 0: # device currently off
            self._write('set LAS') # toggle 'on'
        elif state != 1: # if not off, it's on, nothing to toggle; however, if parsing results something strange turn off power
            self.close()
            raise visa.VisaIOError, 'Received unexpected state while turning laser ON: {0}'.format(state)
        elif err != 0:
            self.close()
            raise visa.VisaIOError, 'An unresolved error prevents me from turning the laser on: {0}'.format(err)
        return state

    def off(self):
        # close shutter; turn off laser
        self.set_current(0)
        state = float(self._query('get LAS'))
        if state == 1: # device currently on
            self._write('set LAS') # toggle 'off'
        elif state != 0: # if not on, it's off, nothing to toggle; however, if parsing results something strange report!
            self.close()
            raise visa.VisaIOError, 'Received unexpected state while turning laser OFF: {0}'.format(state)
        return state

    def set_max_current(self,maxcurr=0):
        self._curr_max = maxcurr
        self._write('set LCL {0}A'.format(maxcurr))
        time.sleep(self._query_delay)
        return self._query('get LCL')

    def set_current(self,curr=0):
        # if something goes wrong current is set to 0, the port is closed and the causing error raised again.
        # returns actual current (actual and set may differ a bit.)
        try:
            curr = np.min([self._curr_max,curr])
            # returns set value (supposed to be identical to curr)
            self._write('set SLC {0}'.format(curr))
            time.sleep(self._query_delay) # regular delay
            time.sleep(self._delay_set_current) # give it time to actually set the current
            ans = self.read_current()
            return float(ans.split(' ')[0])
        except Exception as e:
            # whatever you have in here must be safe!
            # don't call self.off(): it calls set_current(0) and goes in recusion limbo
            self.close()
            raise Exception, e

    def read_current(self):
        try:
            return self._query('get ALC')
        except visa.VisaIOError, e: # includes timeout errors
            self.close()
            raise visa.VisaIOError, e

    def read_power_internal(self):
        try:
            return self._query('get ALP') # do NOT rely on this reading though! (from old calibration...)
        except visa.VisaIOError, e: # includes timeout errors
            self.close()
            raise visa.VisaIOError, e

    def read_error(self):
        # in case error reads:
        # rs232 time out error0
        # I neither know where that comes from, nor how to resolve it, try a bunch of things, so far it always went away, but I don't know on behalf of which comand
        # one suspicion: two write comands right after each other, hence the delay in _write()
        # but if you find it again, this might not be the only source for this error...
        try:
            err = float(self._query('get ERR'))
            return err
        except ValueError, e:
            # err responds with something unreadable or at least not a number.
            self.close()
            raise ValueError, e

    def read_cooler(self):
        # AT1 and AT2, however, only AT1 is active.
        # returns temperature in deg C
        try:
            temp = self._query('get AT1') # '\n19.9 \xb0C\r'
            return float(temp.split(' ')[0])
        except ValueError, e:
            self.close()
            raise ValueError, e

    '''def set_cooler(self, temp):
        self._write('set ST1 {0}'.format(temp))'''


class SpectroMeter(object):
    def __init__(self,resourcemanager,address):
        self._query_delay = 0.1 # time in s between write and read when query
        self._read_n = 4096 # read raw so many bytes (or until machine sends nothing new anymore... 4096 is overkill, but measurement does send many, many bytes)

        _osa = resourcemanager.open_resource(address)
        _osa = self._set_attributes(_osa)
        self._osa = _osa
        self._write('IP;') # Instrument preset (IP) sets all function to their preset (default) state (including: clears the error register)
        self._write('LG;') # set amplitude scale to logarithmic (for linear: LN)

        self._res_name = _osa.resource_info[0].resource_name
        self._dev_name = vparse(self._query('ID?')) # see also CONFIG?

    def _set_attributes(self,_osa):
        # default values with whom it worked; set to ensure.
        _osa.set_visa_attribute(C.VI_ATTR_TMO_VALUE,3000) # 3000 ms is already standard
        _osa.set_visa_attribute(C.VI_ATTR_TERMCHAR_EN,C.VI_FALSE)
        _osa.set_visa_attribute(C.VI_ATTR_SEND_END_EN,C.VI_TRUE)
        _osa.set_visa_attribute(C.VI_ATTR_TERMCHAR,int(u'0xA',base=16)) # end lines with \n (=0xA); only option according Language Reference
        _osa.set_visa_attribute(C.VI_ATTR_FILE_APPEND_EN,C.VI_FALSE)
        _osa.set_visa_attribute(C.VI_ATTR_IO_PROT,1)

        return _osa

    def get_statset(self):
        # info about the current state, stuff that belongs in a file header
        info = ['resource_name={0}'.format(self._res_name),'ID?={0}'.format(self._dev_name)]
        info.append('AUNITS?={0}'.format(vparse(self._query('AUNITS?')))) # DBM, DBMV, DBUV, V, W
        info.append('CENTERWL?={0}'.format(vparse(self._query('CENTERWL?'))))
        info.append('RB?(ResBandwidth)(nm)={0}'.format(vparse(self._query('RB?'))))
        info.append('RL?(ReferenceLevel)(dBm)={0}'.format(vparse(self._query('RL?'))))
        info.append('RLPOS?(PositionRL)={0}'.format(vparse(self._query('RLPOS?')))) # no idea what it means
        info.append('ROFFSET?(dB)={0}'.format(vparse(self._query('ROFFSET?'))))
        info.append('SENSitivity?(dBm)={0}'.format(vparse(self._query('SENS?')))) # note: results are always returned in dBm regardless of the value set by AUNITS
        info.append('SPan?(nm)={0}'.format(vparse(self._query('SP?')))) # SP = wstop - wstart

        return info

    def __str__(self):
        return ';'.join([self._res_name,self._dev_name])

    def _query(self,msg):
        # note: OSA is case sensitive!
        self._osa.write(unicode(msg))
        time.sleep(self._query_delay)
        return self._osa.read_raw(self._read_n)

    def _write(self,msg):
        # note: OSA is case sensitive!
        time.sleep(self._query_delay) # give it time to process the old orders.
        self._osa.write(unicode(msg))

    def close(self):
        # put OSA back to local operation
        #GPIB.write('loc'), should be in regular .close():
        self._osa.close()

    def set_sensitivity(self,sensitivity=None):
        if sensitivity is not None:
            self._write('SENS {0}DBM'.format(sensitivity))
        return float(self._query('SENS?'.format(sensitivity)))

    def set_wavelength_center(self,lambd):
        return float(self._query('CENTERWL {0}NM;CENTERWL?'.format(lambd)))

    def set_wavelength_span(self,span):
        # set wavelength range symmetrically around the center wavelength CENTERWL
        # It's equal to SP = STOPWL - STARTWL
        return float(self._query('SP {0}NM;SP?'.format(span)))

    def read_wavelength_range(self):
        return [float(self._query('STARTWL?')), float(self._query('STOPWL?'))]

    def measure(self,timed=True):
        # if timed: return yields measured result AND time it needed to execute
        # TDF [P,M,B,A,I] to set the requested output format: (decimal, integer, binary, 8-bit format, other 8-bit format)
        # TRA? request stored trace data in A (technically there is also TRB,TRC)
        t0 = time.time() # init for case of exception
        if timed:
            t0 = time.time()
            return self._query('TDF P;TRA?').split(','), time.time()-t0
        else:
            return self._query('TDF P;TRA?').split(',')


class HeatSink(object):
    def __init__(self,resourcemanager,address):
        _hs = resourcemanager.open_resource(address)
        _hs.write(r'*CLS') # clear status; all event registers and error queue

        self._idn = vparse(_hs.query(r'*IDN?'),2) # identification code of meter itself
        self._mode = vparse(_hs.query(r'TEC:MODE?'),2) # mode: ITE (TEC current), R (resistance/reference) or T (temperature)
        self._hs = _hs

    def __str__(self):
        return ';'.join([self._idn,self._mode])

    def set_temperature(self,T=None):
        if T is not None:
            raw_input('Set temperature MANUALLY and confirm: {0}'.format(T))
        return self.read_temperature()

    def read_temperature(self):
        return self._hs.query_ascii_values(r'TEC:T?')[0]

    def close(self):
        self._hs.close()


#=======================================================================================

ResourceManager = lambda : visa.ResourceManager()

def main():
    rm = visa.ResourceManager()
    print rm.list_resources(query=u'?*')
    """
    u'PXI5::1::INSTR'   n/a
    u'PXI5::2::INSTR'   frame grabber card: open NI-MAX to controll
    u'ASRL1::INSTR'     power source, i.e. pump controll
    u'ASRL10::INSTR'    n/a
    u'GPIB0::1::INSTR'  Orion AD100 actuator
    u'GPIB0::2::INSTR'  Orion Power Meter (n/a)
    u'GPIB0::4::INSTR'  n/a
    u'GPIB0::5::INSTR'  Newport TEC
    u'GPIB0::9::INSTR'  spectrometer
    """

    osa = SpectroMeter(rm,u'GPIB0::9::INSTR')

    ps = PowerSource(rm,u'ASRL1::INSTR')

    hs = HeatSink(rm,u'GPIB0::5::INSTR')


    pm = PowerMeter(rm,u'USB0::0x1313::0x8078::P0004893::INSTR')
    print pm
    print pm.get_statset()
    print pm.average_over(200)
    #print pm.set_wavelength(1270)
    print pm.measure()




if __name__ == '__main__': main()

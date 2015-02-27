#! /usr/bin/python2.7
# -*- coding: utf-8 -*-


from os.path import exists
import csv
import re
from itertools import izip as zip, count # izip for maximum efficiency: http://stackoverflow.com/questions/176918/finding-the-index-of-an-item-given-a-list-containing-it-in-python
import numpy as np
import matplotlib.pyplot as plt

import errorvalues as ev # github.com/stefantkeller/errorvalues

from varycolor import varycolor


def load(path,ignore_wrong_entries=False,return_header_dict=False):
    with open(path,'rb') as fn:
        header = fn.readline() # read and thus skip header
        hdict = split2dict(header,el_sep=';',en_sep='=',ignore_wrong_entries=ignore_wrong_entries)

        columns = hdict['columns'].split(',')
        N = len(columns)

        r = csv.reader(fn,delimiter=',')
        storage = {}
        for e in range(N):
            storage[e] = []
        for row in r:
            if row[0].startswith('#') or len(row)!=N: continue # a commented or invalid entry
            for e in range(N):
                storage[e].append(row[e])
                
    retlist = [storage[e] for e in range(N)]
    if return_header_dict: retlist.append(hdict)
    return retlist

def sanitize(strng):
    strng=strng.replace('\n','')
    strng=strng.replace('\r','')
    return strng
    
def unorder_to_stderrval(x,LUT,index_list):
    x = map(float,x)
    x = LUT(x,index_list)
    x = ev.stderrvallist(x)
    return x

def extract(logfile,identifiers=['Current','Pump','Refl','Laser']):
    # beyond default identifiers:
    # 'Spectra' (in order to extract spectra run LL_spectrum.py first - this writes the necessary eval files)
    # 'Temperature' (mean +- std (!) heat sink temperature seen after each measurement)
    rootpath = '/'.join(logfile.split('/')[:-1])

    # each temperature delivers a list of values attached with errorbars
    current_set = {} # this we need irrespective of whether we request it as a return value
    # store some boolean values:
    bcurr = 'Current' in identifiers
    bpump = 'Pump' in identifiers
    brefl = 'Refl' in identifiers
    blaser = 'Laser' in identifiers
    bspectra = 'Spectra' in identifiers
    btemperature = 'Temperature' in identifiers
    
    if bcurr: current = {}
    if bpump: pump = {}
    if brefl: reflection = {}
    if blaser: emission = {}
    if bspectra: spectra = {}
    if btemperature: temperature = {}
    #print bcurr,bpump,brefl,blaser

    with open(logfile,'rb') as lf:
        header = lf.readline() # read and thus skip header
        
        hdict = split2dict(header, ';','=')
        columns = hdict['columns'].split(',')
        cid = dict( zip(columns,range(len(columns))) ) # easily accessible dict with instructions of what the columns refer to
        
        pwr_folder = sanitize(hdict['pwr_folder'])
        pwr_root = rootpath+'/'+pwr_folder+'/'
        
        n_repetitions = int(hdict['n_repetitions'])
        logfile_version = hdict['logfile_version']
        #n_powermeters = hdict['n_powermeters']

        
        r = csv.reader(lf,delimiter=',')
        for row in r:
            if row[0].startswith('#'): continue # a commented entry => skip
            
            if 'Temp' in cid:
                T = float(row[cid['Temp']])
            elif 'Temp_set' in cid:
                T = float(row[cid['Temp_set']])
            else:
                T = np.nan
            timestamp = float(row[cid['Time_stamp']])
            
            cf = pwr_root+row[cid['Current']] # if 'Current' not in cid this raises a KeyError!
            c_set, c_got = load(cf)
            c_set, c_got = map(float,c_set), map(float,c_got)

            
            # create look up table in order to correlate the duplicate entries with one another
            ordered = find_random_duplicates(c_set)

            current_set[T] = np.array(sorted(ordered.keys()))

            index_list = np.array([ordered[c] for c in current_set[T]]).transpose() # look up table with indices corresponding to same set current, in ascending order!
            LUT = lambda x, indices: np.array([[x[i] for i in duplicate] for duplicate in indices])

            #
            # with the created LUT we reorder power readings:
            # every column corresponds to a set current,
            # we have as many duplicates as rows.
            #
            # assign errorbars to the measurements:
            # the errorbars correspond to the standard error
            # ste = std/sqrt(N)
            # the standard error tells us how well we know the mean of a distribution
            # this knowledge increases with the number of repetitions N
            # or in other words: averaging increases signal-to-noise.
            #
            # eventually:
            # subtract background and
            # store them in dict assigned to their temperature
            
            if bcurr:
                curr = unorder_to_stderrval(c_got,LUT,index_list)
                #curr = LUT(c_got,index_list)
                #curr = ev.stderrvallist(curr)
                #curr -= ev.min_(curr)[0]
                current[T] = curr# - ev.min(curr)[0]
                
            if bpump:
                if sanitize(logfile_version)=='p1':
                    pf = pwr_root+row[cid['Power']]
                else:
                    pf = pwr_root+row[cid['Pump']]
                pmp, ptime = load(pf)
                pmp = unorder_to_stderrval(pmp,LUT,index_list)
                #pmp = map(float,pmp)
                #pmp = LUT(pmp,index_list)
                #pmp = ev.stderrvallist(pmp)
                #pmp -= ev.min_(pmp)[0]
                pump[T] = pmp# - ev.min(pmp)[0]
                
            if brefl:
                rf = pwr_root+row[cid['Refl']]
                refl, rtime = load(rf)
                refl = unorder_to_stderrval(refl,LUT,index_list)
                #refl = map(float, refl)
                #refl = LUT(refl,index_list)
                #refl = ev.stderrvallist(refl)
                #refl -= ev.min_(refl)[0]
                reflection[T] = refl# - ev.min(refl)[0]
                
            if blaser:
                lf = pwr_root+row[cid['Laser']]
                las, ltime = load(lf)
                las = unorder_to_stderrval(las,LUT,index_list)
                #las = map(float, las)
                #las = LUT(las, index_list)
                #las = ev.stderrvallist(las)
                #las -= ev.min_(las)[0]
                emission[T] = las# - ev.min(las)[0]
                
            if btemperature:
                tf = pwr_root+row[cid['Temp_live']]
                tcurr, ths = load(tf)
                ths = map(float,ths)
                temperature[T] = ev.errval(np.mean(ths),np.std(ths,ddof=1))
                
            if bspectra:
                sf = row[cid['Spectra']]
                sf = pwr_root+'.'.join(sf.split('.')[:-1])+r'_eval.csv' # in order for this to exist: run LL_spectrum.py first!
                
                scurrent, lambda_short, lambda_long = load(sf) # scurrent == c_set
                
                lambda_short = unorder_to_stderrval(lambda_short,LUT,index_list)
                lambda_long = unorder_to_stderrval(lambda_long,LUT,index_list)
                
                spectra[T] = [lambda_short,lambda_long] # this is a list of lists!


    return_list = [current_set]
    if bcurr: return_list.append(current)
    if bpump: return_list.append(pump)
    if brefl: return_list.append(reflection)
    if blaser: return_list.append(emission)
    if bspectra: return_list.append(spectra)
    if btemperature: return_list.append(temperature)

    return return_list

def plotinstructions_write(instrfile,Temperatures,calib_folder):
    # Temperatures ought to be sorted!
    create_new = not exists(instrfile)
    if create_new:
        with open(instrfile,'wb') as f:
            f.write('Instruction file for the script to plot and fit (using {} for calibration):\n'.format(calib_folder))
            f.write('textx=1\n')
            f.write('fontsize=12\n')
            f.write('title=[-> insert meaningful title here <-]\n')
            f.write('xlim=[0,14]\n')
            f.write('ylim1=[-0.01,3]\n')
            f.write('ylim2=[20,50]\n')
            for T in Temperatures:
                f.write('texty1[{0}]=2\n'.format(T))
            for T in Temperatures:
                f.write('llow0[{0}]=2\n'.format(T))
                f.write('lhigh0[{0}]=10\n'.format(T))
            f.write('xlim3=[2,10]\n')
            f.write('ylim3=[1260,1270]\n')
            f.write('plot_temps_for_3=[')
            for T in Temperatures:
                f.write('{0}'.format(T))
                if not T==Temperatures[-1]: f.write(',')
            f.write(']\n')
            f.write('textx3=3\n')
            f.write('texty3=[1265,1263]\n')
        f.close() # close to actually write -- until now it's only in the buffer!
    print 'Open file {0} and modify instructions.'.format(instrfile)

def plotinstructions_read(instrfile):
    instr = {}
    with open(instrfile,'rb') as f:
        f.readline() # skip header
        r = csv.reader(f,delimiter='=')
        for row in r: instr[row[0]]=row[1]
    return instr

def lut_from_calibfile(address, ignore_error=False):
    lin_lut = lambda m,q: lambda x: x*m+q
    with open(address, 'rb') as f:
        header = f.readline()
        hdict = split2dict(header, ';','=')
        linreg = hdict['linreg']
        try:
            mq = ev.str2errvallist(linreg)
            if not ignore_error:
                m0, q0 = mq[0], mq[1]
            else:
                m0, q0 = mq[0].v(), mq[1].v()
        except IndexError: # legacy, in old calibrations mq is an empty list (i.e. no index)
            try:
                p = re.compile('(\d*\.\d*)\*\w+\+(-?\d*\.\d*)')
                m = p.match(linreg)
                m0 = float(m.group(1))
                q0 = float(m.group(2))
            except AttributeError, e:
                print address,linreg
                raise AttributeError, e
    return lin_lut(m0,q0)

def lut_from_calibfolder(calib_folder,identifiers=['Pump','Refl','Laser'],ignore_error=False):
    bcurr = 'Current' in identifiers
    bpump = 'Pump' in identifiers
    brefl = 'Refl' in identifiers
    blaser = 'Laser' in identifiers

    lut_1x1 = lambda x: x # 'do nothing', hence you can use the same 'lut'-expression, but use the raw data; for uncalibrated elements
    retlutlist = []
    
    if bcurr:
        calib_curr = calib_folder+'LUTs/calib_pump_current'
        if exists(calib_curr):
            curr_lut = lut_from_calibfile(calib_curr,ignore_error)
        else:
            curr_lut = lut_1x1
        retlutlist.append(curr_lut)
    if bpump:
        calib_pump = calib_folder+'/LUTs/calib_pump.csv'
        if exists(calib_pump):
            pump_lut = lut_from_calibfile(calib_pump,ignore_error)
        else:
            pump_lut = lut_1x1
        retlutlist.append(pump_lut)
    if brefl:
        calib_refl = calib_folder+'/LUTs/calib_reflection.csv'
        if exists(calib_refl):
            refl_lut = lut_from_calibfile(calib_refl,ignore_error)
        else:
            refl_lut = lut_1x1
        retlutlist.append(refl_lut)
    if blaser:
        calib_emission = calib_folder+'/LUTs/calib_emission.csv'
        if exists(calib_emission):
            emis_lut = lut_from_calibfile(calib_emission,ignore_error)
        else:
            emis_lut = lut_1x1
        retlutlist.append(emis_lut)
    
    return retlutlist if len(retlutlist)>1 else retlutlist[0] # as one would expect if only one is requested
    
def lut_interp_from_calibfile(address):
    with open(address, 'rb') as f:
        header = f.readline() # skip header
        r = csv.reader(f,delimiter=',')
        x,y = ev.errvallist([]),ev.errvallist([])
        for row in r:
            x.append(ev.errval(float(row[0]),float(row[1])))
            y.append(ev.errval(float(row[2]),float(row[3])))
    xsort = ev.sorting_instr(x) # make sure order is ascending
    x = ev.reorder(x,xsort)
    y = ev.reorder(y,xsort)
    lut = lambda v: ev.interplist(v,x,y)
    def value_scale(v):
        if not isinstance(v,ev.errval): return 1
        elif v.v()==0: return 0
        else: return v/v.v()
    return lambda evlist: ev.errvallist([lut(v)*value_scale(v) for v in evlist])

def lut_interp_from_calibfolder(calib_folder,identifiers=['Pump','Refl','Laser']):
    bcurr = 'Current' in identifiers
    bpump = 'Pump' in identifiers
    brefl = 'Refl' in identifiers
    blaser = 'Laser' in identifiers

    lut_1x1 = lambda x: x # 'do nothing', hence you can use the same 'lut'-expression, but use the raw data; for uncalibrated elements
    retlutlist = []
    
    if bcurr:
        calib_curr = calib_folder+'LUTs/calib_pump_current'
        if exists(calib_curr):
            curr_lut = lut_interp_from_calibfile(calib_curr)
        else:
            curr_lut = lut_1x1
        retlutlist.append(curr_lut)
    if bpump:
        calib_pump = calib_folder+'/LUTs/calib_pump.csv'
        if exists(calib_pump):
            pump_lut = lut_interp_from_calibfile(calib_pump)
        else:
            pump_lut = lut_1x1
        retlutlist.append(pump_lut)
    if brefl:
        calib_refl = calib_folder+'/LUTs/calib_reflection.csv'
        if exists(calib_refl):
            refl_lut = lut_interp_from_calibfile(calib_refl)
        else:
            refl_lut = lut_1x1
        retlutlist.append(refl_lut)
    if blaser:
        calib_emission = calib_folder+'/LUTs/calib_emission.csv'
        if exists(calib_emission):
            emis_lut = lut_interp_from_calibfile(calib_emission)
        else:
            emis_lut = lut_1x1
        retlutlist.append(emis_lut)
    
    return retlutlist   

def thermal_resistance(T,wavelength,dlambdadPd):
    # based on Heinen2012's equation (2)
    # lambda = dlambda/dT*T + dlambda/dPd*Pd + lambda_0
    #        = dlambdadPd*Pd + wavelength
    # with
    # lambda_0_ = dlambdadT*T + lambda_00
    # (lambda_00 is virtual wavelength at no dissipated power
    #  and heat sink temperature of 0 degC
    #  (resp. at T=0 of whatever the unit of input temperatures is...))
    #
    # R_th = dlambda/dPd / dlambda/dT = dT/dPd
    
    l0, dldT = ev.linreg(T.v(), wavelength.v(),wavelength.e())
    #dldD = ev.stderrval(dlambdadPd)
    dldD = ev.wmean(dlambdadPd) # supposed to be the same value measured several times => weighted mean
    #R_th = dldD/dldT
    
    return dldD, dldT, l0#, R_th


def split2dict(strng,el_sep=';',en_sep='=',ignore_wrong_entries=True):
    # 'a=1;b=2;c=3' -> {'a': '1', 'c': '3', 'b': '2'}
    # strng = 'a=1;b=2;c=3'
    # el_sep: element ('a=1',...) separator, e.g. ';'
    # en_sep: entry ('a'='1',...) separator, e.g. '='
    # if not ignore_wrong_entries:
    #   string whose parts doesn't fit above described pattern raises an error
    #   e.g. 'a=1;without equal sign;valid=True' raises a ValueError
    # if ignore_wrong_entries:
    #   these ValueErrors are ignored (pass)
    # see github.com/stefantkeller/STK_py_generals/general_functions.py
    el = strng.split(el_sep)
    splt = lambda x: x.split(en_sep)
    retdict = {} # return dict( (e0,e1) for e0,e1 in map( splt, el ) )
    for e in el:
        try:
            e0,e1 = splt(e)
            retdict[e0]=e1
        except ValueError, e:
            if ignore_wrong_entries: pass
            else:
                print strng
                raise ValueError, e
    return retdict

def find_random_duplicates(input):
    # input = [10,11,12,13,14,13,12,10,11,11,12,13,14,10,14]
    # (indices[ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14])
    # return: {10: [0, 7, 13], 11: [1, 8, 9], 12: [2, 6, 10], 13: [3, 5, 11], 14: [4, 12, 14]}
    #http://stackoverflow.com/questions/176918/finding-the-index-of-an-item-given-a-list-containing-it-in-python
    #http://stackoverflow.com/questions/479897/how-do-you-remove-duplicates-from-a-list-in-python-if-the-item-order-is-not-impo
    # see github.com/stefantkeller/STK_py_generals/general_functions.py
    deduplicated = sorted(set(input))
    indexlist = [[i for i, j in zip(count(), input) if j == k] for k in deduplicated]
    return dict((e0,e1) for e0,e1 in zip(deduplicated,indexlist))

def main():
    pass

if __name__ == "__main__":
    main()

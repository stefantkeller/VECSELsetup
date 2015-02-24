#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

import csv
import numpy as np

from gen_functions import load, sanitize, find_random_duplicates


def find_index_iter(array,value,low=None,high=None):
    '''
    same as find_index() but the value has to be exact
    [low,high] constrains search if approx position in the array is known already

    example:
    a = [1,2,3,4,5,6,7,8,9,0]
    it = find_index_iter(a,4)
    print it, (it==3)
    it = find_index_iter(a,8,high=6)
    print it, (it==None)
    it = find_index_iter(a,8,high=7)
    print it, (it==7)
    it = find_index_iter(a,0,low=7)
    print it, (it==9)
    see github.com/stefantkeller/STK_py_generals/general_functions.py
    '''
    if low==None: low=0
    if high==None: high=len(array)-1

    it = low
    for search in xrange(high-low+1):
    # one more iteration than range: to get last iteration as well.
    # if the value is found, this loop should break
    # if it doesn't the last +=1 is executed, which we can detect.
        if array[it]==value: break
        it += 1
    if it==high+1: it=None # not found; loop didn't break
    return it

def lambda_spread(wavelengths, powers, threshold=-35):
    max_i = find_index_iter(powers,np.max(powers))
    long_i = int(max_i) # init copied value
    short_i = int(max_i) # init copied value
    
    for p in powers[max_i:]:
        # start at peak of spectrum
        # from there go to longer wavelengths
        # stop once the power reading is lower than specified threshold
        # th_i then corresponds to the threshold index
        long_i += 1
        if p<threshold: break
    if long_i>=len(wavelengths): long_i=len(wavelengths)-1
    for p in powers[max_i::-1]: # start at max_i, go backwards
        short_i -= 1
        if p<threshold: break
    if short_i<0: sort_i=0
    
    lambda_long = wavelengths[long_i]
    lambda_short = wavelengths[short_i]
    return lambda_short,lambda_long

def extract_spectrum_file(filepath):
    wl, pw = [], []
    with open(filepath,'rb') as f:
        f.readline() # skip header
        r = csv.reader(f,delimiter=',')
        for row in r:
            if len(row)==2 and not row[0].startswith('#'): # no empty nor commented line
                wl.append(float(row[0]))
                pw.append(float(row[1]))
    return wl, pw

def extract_spectrum_collection(collection_path, spectra_path):
    currents,spectra,time_durations,hdict = load(collection_path,ignore_wrong_entries=True,return_header_dict=True)
    threshold = float(sanitize(hdict['SENSitivity?(dBm)']))

    lambda_shorts, lambda_longs = [], []
    for spe in spectra:
        wl, pw = extract_spectrum_file(spectra_path+spe)
        
        lambda_short,lambda_long = lambda_spread(wl,pw,threshold)
        lambda_shorts.append(lambda_short)
        lambda_longs.append(lambda_long)
        
    return currents, lambda_shorts, lambda_longs, threshold

def overview_spectra(collection_path, spectra_path):
    currents,spectra,time_durations = load(collection_path,ignore_wrong_entries=True)
    currents = map(float,currents)
    
    ordered = find_random_duplicates(currents)

    current_set = np.array(sorted(ordered.keys())) # sorted list without duplicates
    index_list = np.array([ordered[c] for c in current_set]) # look up table with indices corresponding to same set current, in ascending order!
    LUT = lambda x, indices: np.array([[x[i] for i in duplicate] for duplicate in indices])
    
    ordered_spectra_filenames = LUT(spectra,index_list) # [[current0_file0,current0_file1,...],[current1_file0,...],...]
    wavelengths, pw = extract_spectrum_file(spectra_path+ordered_spectra_filenames[0][0])
    spectra = []
    for cf in ordered_spectra_filenames:
        powers = []
        for f in cf:
            wl, pw = extract_spectrum_file(spectra_path+f)
            powers.append(pw)
        powers = np.array(powers)
        assert powers.shape == (len(cf),len(wavelengths))
        avg = np.mean(powers,axis=0) # for every wavelength there is one entry: the average of the duplicate power measurements
        spectra.append((avg-np.min(avg))/(np.max(avg)-np.min(avg))) # append normalized mean
    spectra = np.array(spectra)
    assert spectra.shape == (len(current_set),len(wavelengths))
    return current_set, wavelengths, spectra

def main():
    pass

        
if __name__ == "__main__":
    main()

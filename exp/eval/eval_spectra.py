#! /usr/bin/python2.7
# -*- coding: utf-8 -*-

from os import listdir
from os.path import exists

import csv
import numpy as np
import matplotlib.pyplot as plt

from VECSELsetup.eval.gen_functions import sanitize, split2dict
from VECSELsetup.eval.spectra import extract_spectrum_collection, overview_spectra


'''
In main() set logfile to appropriate address.
This module evaluates the longest emitted wavelength.
It reads out the measured spectra found on disc via logfile,
and writes new files with only the information about the longest emitted wavelength.
The filenames of these new files are the same name as stored in the logfile,
plus the suffix '_eval'.
For example 150_OSA.csv contains the information about current and filenames;
then the newly created 150_OSA_eval.csv contains current and wavelength.
'''


def _plot_overview_spectra(collection_path, spectra_path, temperature):
    currents, wavelengths, spectra = overview_spectra(collection_path, spectra_path)
    plt.clf()
    for j in xrange(len(currents)):
        plt.plot(wavelengths,spectra[j]-j,c='k')
    plt.xlim([wavelengths[0],wavelengths[-1]])
    plt.ylim([-len(currents),1])
    plt.yticks([])
    plt.title('{0} $^\circ$C'.format(temperature))

    plot_path = '.'.join(collection_path.split('.')[:-1]) + '.png'
    plt.savefig(plot_path)
    #plt.show()
    plt.clf()
    return plot_path

def spectra_evaluated(pwr_folder):
    # returns True or False, depending on whether or not the spectra are already evaluated
    evaluated = True
    pwr_folder_content = listdir(pwr_folder)
    for f in pwr_folder_content:
        if f.endswith('OSA.csv'):
            basename = ''.join(f.split('.')[:-1])
            evalfile = ''.join([basename,'_eval.csv'])
            evalfilepath = '/'.join([pwr_folder,evalfile])
            evaluated = evaluated and exists( evalfilepath ) # True if _eval.csv exists for all OSA.csv files
    return evaluated

def eval_spectra(logfile):

    rootpath = '/'.join(logfile.split('/')[:-1])
    with open(logfile,'rb') as lf:
        header = lf.readline()
        hdict = split2dict(header,el_sep=';',en_sep='=',ignore_wrong_entries=True)
        columns = hdict['columns'].split(',')
        cid = dict( zip(columns,range(len(columns))) )
        
        pwr_folder = sanitize(hdict['pwr_folder'])
        pwr_root = rootpath+'/'+pwr_folder+'/'
        
        spectr_folder = sanitize(hdict['spectr_folder'])
        spectr_root = rootpath+'/'+spectr_folder+'/'
        
        r = csv.reader(lf)
        for row in r: # every row corresponds to a temperature
            if 'Temp_set' in cid:
                T = row[cid['Temp_set']]
            else:
                T = np.nan
            spectr_file = row[cid['Spectra']]
            spcollection = pwr_root+spectr_file
            
            currents, lambda_shorts, lambda_longs, threshold = extract_spectrum_collection(spcollection, spectr_root)
            
            # write current and wavelengths in new file
            # filename is the same name as stored in the logfile,
            # plus the suffix '_eval'
            # e.g. 150_OSA.csv contains currents and filenames
            # ==> 150_OSA_eval.csv contains currents and wavelength
            eval_file = pwr_root+'.'.join(spectr_file.split('.')[:-1])+r'_eval.csv'
            with open(eval_file,'wb') as ef:
                ef.write(u'columns=Current(A),lambda_short(nm),lambda_long(nm);threshold={0}(dBm)\n'.format(threshold))
                for j in xrange(len(currents)):
                    ef.write(u'{0},{1},{2}\n'.format(currents[j],lambda_shorts[j],lambda_longs[j]))
            
            # secondly, store an image summarizing the spectra
            plot_file = _plot_overview_spectra(spcollection, spectr_root, T)

            print 'Evaluation written:', eval_file, plot_file
    print 'Spectra evaluated:', logfile
    

def main():
    logfile = '20150124_detailed/spot333um_noOC.csv'
    eval_spectra(logfile)


if __name__ == "__main__":
    main()

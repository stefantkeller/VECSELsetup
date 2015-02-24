#! /usr/bin/python2.7
# -*- coding: utf-8 -*-


from os import makedirs
from os.path import isfile,isdir,exists
from subprocess import call as spcall # this will write a report in LaTeX, iff you have it installed


def tex_report(plot_paths):
    path = plot_paths[0]
    report_folder = '/'.join(path.split('/')[:-1])+'/tmp'
    if not exists(report_folder):
        makedirs(report_folder)
    report_name = report_folder + '/calib_report.tex'

    with open(report_name,'wb') as r:
        r.write(r'''
\documentclass[11pt, a4paper]{article}
\usepackage[latin1]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[english]{babel}
\usepackage[pdftex]{graphicx}
\usepackage{color}
\usepackage[colorlinks]{hyperref}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{amstext}
\usepackage{fancyhdr}
\pagestyle{fancy}

\begin{document}
\fancyhead[L]{Calibration \today}
        ''')
        plot_paths = ['../'+plot.split('/')[-1] for plot in plot_paths]
        for plot in plot_paths:
            r.write(r'''
\begin{figure}
\centering
\includegraphics[width=12.5cm]{''')
            r.write(plot)
            r.write(r'''}
\end{figure}
            ''')
        
        r.write(r'''
\end{document}
        ''')
    
    return report_name

def write_report(plot_paths):

    report_path = tex_report(plot_paths)
    
    r = report_path.split('/')
    report_folder = '/'.join(r[:-1])
    report_name = '.'.join(r[-1].split('.')[:-1])
    spcall(['cd {0};pdflatex {1};mv {2} ..;cd ..;rm -r tmp/'.format(report_folder,report_name+'.tex',report_name+'.pdf')],shell=True)

def main():
    #report_name = r'20141126_calib/LUTs/tmp/calib_report.tex'
    plot_paths = [r'20141120_calib/LUTs/calib_pump.png',
                  r'20141120_calib/LUTs/calib_pump_current.png',
                  r'20141120_calib/LUTs/calib_reflection.png',
                  r'20141120_calib/LUTs/calib_emission.png',
                  r'20141120_calib/LUTs/calib_current.png']
    write_report(plot_paths)

if __name__ == "__main__":
    main()

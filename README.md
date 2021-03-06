VECSELsetup
==========

github.com/stefantkeller/VECSELsetup

Content
------

  * installation
  * file hierarchy
  * usage

Installation
-----------

This is a Python library.
If you don't have Python installed yet,
I recommend you install [Anaconda](http://continuum.io/downloads)
for Python 2.7 (it's free!).

To install this library
from github,
  1. click on "Download ZIP",
  2. extract the .zip
  3. copy the folder to where ever you want it
  4. adjust the [Pythonpath](http://lmgtfy.com/?q=how+to+adjust+pythonpath)

(at least, that's the proper way to do it).  
And, if you are familliar with git ... you know what to do.

If you don't care about "proper"
and you simply want it to work
(I don't know though what this breaks along the way...):  
after extracting the .zip,
copy the folder to (something like; if you work with Anaconda as recommended above)
  * Windows: `C:\Anaconda\Lib\site-packages`
  * Mac: `/Users/yourusername/anaconda/Lib/python2.7/site-packages`  
this path is already in the Pythonpath,
and Python will find it.


For measurements (the stuff in `meas/`) you need
[pyvisa](https://pyvisa.readthedocs.org/en/master/).

For evaluation (the stuff in `eval/`) you need to also install
[errorvalues](https://github.com/stefantkeller/errorvalues)
from github.com/stefantkeller/errorvalues --
with the same procedure as listed above.

If you intend to use the calibration in `exp/eval/calibration.py` as it is,
this is going to write an automated report (tuck together some plots) as a pdf;
ready for print.
This relys on [LaTeX](https://en.wikipedia.org/wiki/LaTeX) (pdflatex) to be installed on your system.

If measurement and evaluation happens on two different computers (recommended)
you probably install only those dependencies that you need.
That's ok, the error handling in `__init__.py` catches ImportError's and ignores them.
However, if nothing happens at all,
you might want to check whether you have installed,
what you're supposed to have installed
(maybe everything is caught and subsequentially ignored?).

File hierarchy
------------

The different folders have different purposes:
  * meas, setup control to record measurements
  * eval, scripts for evaluation of measurements
  * exp, examples of working measurement routines (using meas), and evaluation (using eval)
  * doc, documentation


Usage
----

Copy the files stored from the folder `exp` in your working directory.
The example `exp/meas/routine_measurement.py` is the most exhaustive for setup control / recording measurements.
While `exp/eval/light_light.py` highlights the evaluation part.

There is not graphical user interface (GUI),
as one might know from [LabView](http://www.ni.com/labview).
Instead, with this library
you have full controll over
what the software does.
But this comes with the price
to actually having to read the lines of code --
instead of looking at obscure icons.

There are only few lines of code
to read,
in order to understand what's going on;
and those are accompanied with comments.
So go ahead and read it.
You best start with the example scripts in the folder `exp`.

These lines of code
you can read with any text editor
of your choosing.
On Windows I recommend [PyScripter](https://code.google.com/p/pyscripter/).
It brings in some simple GUI features,
so you can edit and launch your measurement routines easily.

VECSELsetup
==========

github.com/stefantkeller/VECSELsetup

Content
------

  * installation
  * file hierarchy

Installation
-----------

This is a Python library.
If you don't have Python installed yet,
I recomend you install [Anaconda](http://continuum.io/downloads)
for Python 2.7 (for free!).

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
copy the folder to (something like; if you work with Anaconda as recomended above)
  * Windows: C:\Anaconda\Lib\site-packages
  * Mac: /Users/yourusername/anaconda/Lib/python2.7/site-packages
this path is already in the Pythonpath
and Python will find it.


For evaluation (the stuff in "eval/") you need to also install
[errorvalues](https://github.com/stefantkeller/errorvalues)
from github.com/stefantkeller/errorvalues --
with the same procedure as listed above.


File hierarchy
------------

The different folders have different purposes:
  * meas, setup control to record measurements
  * eval, scripts for evaluation of measurements
  * exp, examples of working measurement routines (using meas), and evaluation (using eval)
  * doc, documentation


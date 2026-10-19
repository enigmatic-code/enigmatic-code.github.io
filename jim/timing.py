#!/usr/bin/env python -t
###############################################################################
#
# File:         timing.py
# RCS:          $Header: $
# Description:  A Python Timing Module
# Author:       Jim Randell
# Created:      Mon Dec 24 10:06:15 2012
# Modified:     Fri Aug 16 13:13:43 2013 (Jim Randell) jim.randell@gmail.com
# Language:     Python
# Package:      N/A
# Status:       Experimental (Do Not Distribute)
#
# (C) Copyright 2012, Jim Randell, all rights reserved.
#
###############################################################################
# -*- mode: Python; py-indent-offset: 2; -*-

"""
This module provides elapsed timing measures.

Usually it is enough to just add the following line to your program
before the start of the section you want to time:

  import timing

and when the program exits it will report the elapsed time thus:

  [timing] elapsed time = 0.0008729s (872.85us)

By default the timing is started when the module is imported, and
stopped and the elapsed time reported when the Python interpreter
exits. But if you want more control you can do the following:

  from timing import Timer

  ...

  # create the timer
  timer = Timer('name')

  # start the timer
  timer.start()

  # the code you want to time would go here
  ...

  # stop the timer
  timer.stop()

  ...

  # print the report
  timer.report()


If you don't call start() then the timer will be started when it is
created.

If you don't call report() then the elapsed time report will be
printed when the Python interpreter exits.

If you don't call stop() then the timer will be stopped when the
Python processor exists, just before the report is printed.


You can create multiple timers. It might help to give them different
names to distinguish their reports. (The default name is "timing").


You can also wrap code to be timed like this:

  with Timer('name'):
    # the code you want to time goes here
    some_code()


You can create a function that will report the timing each time it
is called by decorating it with the timed decorator:

  from timing import timed

  @timed
  def whatever():
    some_code()

"""

from __future__ import print_function

__author__ = "Jim Randell <jim.randell@gmail.com>"
__version__ = "2013-08-16"

__credits__ = """Brian Gladman, contributor"""

import atexit
import time
import sys
import functools

if sys.platform == "win32":
  _timer = time.clock
else:
  _timer = time.time

class Timer(object):

  _default = None

  def __init__(self, name='timing', file=sys.stderr, exit_report=True, disable_default=True):
    """
    Create (and start) a timer.

    name = the name used in the report.
    file = where the report is sent
    exit_report = should the report be generated at exit
    disable_default = should the default timer be disabled
    """
    self._t0 = None
    self._t1 = None
    self._name = name
    self._file = file
    self._report = None
    if exit_report: atexit.register(self.report)
    if disable_default and Timer._default: Timer._default._report = '<none>'
    self.start()

  def start(self):
    """
    Set the start time of a timer.
    """
    self._t0 = _timer()
    self._t1 = None

  def stop(self):
    """
    Set the stop time of a timer.
    """
    self._t1 = _timer()

  def elapsed(self, disable_report=True):
    """
    Return the elapsed time of a stopped timer.

    disable_report = should the report be disabled
    """
    if disable_report: self._report = '<none>'
    return self._t1 - self._t0

  def format(self, t, fmt='{:.2f}'):
    """
    Format a time for the report.
    """
    u = 's'
    if t < 1.0: (t, u) = (1000 * t, 'ms')
    if t < 1.0: (t, u) = (1000 * t, 'us')
    return (fmt + u).format(t)

  def report(self):
    """
    Stop the timer and generate the report (if required).

    The report will only be generated once (if it's not been disabled).
    """
    if self._report: return self._report
    if self._t1 is None: self.stop()
    e = self.elapsed()
    self._report = "[{n}] elapsed time: {e:.7f}s ({f})".format(n=self._name, e=e, f=self.format(e))
    print(self._report, file=self._file)

  def __enter__(self):
    return self

  def __exit__(self, *args):
    self.report()

# function wrapper
def timed(f):
  """
  Return a timed version of function <f>.
  """
  @functools.wraps(f)
  def _timed(*args):
    t = Timer(f.__name__)
    r = f(*args)
    t.report()
    return r
  return _timed

if __name__ != '__main__':
  # start the default timer
  Timer._default = Timer(disable_default=False)

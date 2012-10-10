#!/usr/bin/env python

# Author: Marvin S. Addison
# Date: 2009-11-24
# Dependencies:
#   python 2.6
# Description:
#   Big Brother Web application monitoring script.
#   Uses python to send HTTP GET requests to arbitrary status URL and expects a
#   successful HTTP response code within threshold timeout period.
#
#   This script is intended to provide both basic availability checking
#   as well as application responsiveness.

# TODO: Set HTTP status/health check URL for your environment
url = 'http://www.google.com'

# Customize timeout period (in s) as needed
timeout = 3

# Customize name of BB collection as needed
collection = 'apphttp'

import os, string, subprocess, sys, urllib2
from datetime import datetime
from urllib2 import URLError, HTTPError


bb = os.getenv('BB')
if not bb:
  sys.exit('BB environment variable not set')
bbdisp = os.getenv('BBDISP')
if not bbdisp:
  sys.exit('BBDISP environment variable not set')

result = ''
color = 'green'
try:
  urllib2.urlopen(url, timeout = timeout).read()
except HTTPError as e:
  color = 'red'
  result = 'HTTP check FAILED for [%s] with status %s' % (url, e.code)
except URLError as e:
  color = 'red'
  result = 'HTTP check FAILED for [%s]: %s' % (url, e.reason)
except Exception as e:
  color = 'red'
  result = 'HTTP check FAILED for [%s]: %s' % (url, e)

bb_msg = 'status %s.%s %s %s\n%s' % (
  os.getenv('MACHINE'), collection, color,
  datetime.utcnow().strftime('%a %b %d %H:%M:%S UTC %Y'), result)
subprocess.call([bb, bbdisp, bb_msg])

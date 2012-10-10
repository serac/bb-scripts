#!/usr/bin/env python

# Author: Marvin S. Addison
# Date: 2009-12-21
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
# This value serves as both connection and read timeout periods
timeout = 2

# Customize number of connection attempts
# Note that an exponential backoff strategy is used for timeouts
# on subsequent tries
max_tries = 3

# Customize name of BB collection as needed
collection = 'apphttp'

import os, socket, string, subprocess, sys
from datetime import datetime
from httplib import HTTPConnection, HTTPSConnection
from urllib2 import HTTPError
from urlparse import urlparse, urlunparse

def http_check(url, timeout):
  """HTTP GET given URL.  Response must be received in given timeout"""
  parts = urlparse(url)
  conn = None
  if parts[0] == 'http':
    conn = HTTPConnection(parts[1], timeout=timeout)
  elif parts[0] == 'https':
    host_port = parts[1].split(':')
    host = host_port[0]
    port = 443
    if len(host_port) > 1:
      port = int(host_port[1])
    conn = HTTPSConnection(host=host, port=port, timeout=timeout)
  else:
    raise Exception('Cannot handle %s URL' % parts[0])  
  conn.request('GET', urlunparse((None, None) + parts[2:]))
  resp = conn.getresponse()
  if resp.status / 100 > 3:
    raise HTTPError(url, resp.status, resp.reason, resp.getheaders(), None)

def format_errors(errors):
  """Formats the given error list into a neat string representation"""
  msg = ''
  n = 1
  for err in errors:
    msg += '\n\t%s. %s' % (n, err)
    n += 1
  return msg

bb = os.getenv('BB')
if not bb:
  sys.exit('BB environment variable not set')
bbdisp = os.getenv('BBDISP')
if not bbdisp:
  sys.exit('BBDISP environment variable not set')

result = ''
color = 'green'
n = 1
wait = 0
fail_msgs = []
while n <= max_tries:
  wait = timeout ** n
  try:
    http_check(url, wait)
    break
  except HTTPError as e:
    color = 'red'
    result = 'HTTP check FAILED for [%s] with status %s' % (url, e.code)
    break
  except socket.timeout:
    fail_msgs.append('connect/read timeout (%ss)' % wait)
    n += 1
  except socket.error as e:
    fail_msgs.append('%s (timeout %ss)' % (e, wait))
    n += 1
  except Exception as e:
    color = 'red'
    errmsg = '%s::%s' % (e.__class__.__name__, str(e))
    if errmsg[-1] == ':':
      errmsg += '[no further details available]'
    result = 'HTTP check FAILED for [%s]:\n\n\t%s' % (url, errmsg)
    break

if n > max_tries:
  color = 'red'
  result = 'HTTP check FAILED for [%s]: max tries (%s) exceeded' % (url, max_tries)
  result += format_errors(fail_msgs)
elif n > 1:
  color = 'yellow'
  result = 'ATTENTION: HTTP check for [%s] passed after %s failures' % (url, n-1)
  result += format_errors(fail_msgs)

bb_msg = 'status %s.%s %s %s\n%s' % (
  os.getenv('MACHINE'), collection, color,
  datetime.utcnow().strftime('%a %b %d %H:%M:%S UTC %Y'), result)
subprocess.call([bb, bbdisp, bb_msg])


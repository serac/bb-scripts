#!/usr/bin/env python
################################################################
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at

#  http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
################################################################

# Author: Marvin S. Addison
# Date: 2012-10-10
# Dependencies:
#   python 2.6
# Description:
#   Big Brother CAS server monitoring script that makes use of new health monitoring
#   capability available in CAS 3.5.0.

# Customize port number as needed
cas_port = 8443

# Customize context path as needed
cas_context = '/cas'

# Customize timeout period (in s) as needed
# This value serves as both connection and read timeout periods
timeout = 3

# Customize name of BB collection as needed
collection = 'apphttp'

# Map of health check status strings to BB status colors.
STATUS_MAP = {
  'UNKNOWN': 'yellow',
  'OK': 'green',
  'INFO': 'green',
  'WARN': 'yellow',
  'ERROR': 'red'
}

import os, socket, string, subprocess, sys
from datetime import datetime
from httplib import HTTPConnection, HTTPSConnection
from urllib2 import HTTPError

class HealthSummary:
  """Describes overall CAS health in terms of a status and list of MonitorResult."""

  """Map of HTTP response codes to health statuses."""
  CODE_MAP = {
    100: 'UNKNOWN',
    200: 'OK',
    300: 'INFO',
    400: 'WARN',
    500: 'ERROR'
  }

  def __init__(self, response):
    """Creates a new instance from the HTTP response provided by the CAS /status URI."""
    if not response.status in HealthSummary.CODE_MAP:
      raise Exception("Unknown CAS health monitor HTTP response code %s" % response.status)

    self.status = HealthSummary.CODE_MAP[response.status]
    self.results = []
    for (header, value) in response.getheaders():
      header = header.upper()
      if header.startswith('X-CAS-'):
        self.results.append(MonitorResult(header[6:], value))

  def failed_monitors(self):
    """Gets a list of monitors that are not in OK state."""
    return [r for r in self.results if r.status != 'OK']


class MonitorResult:
  """Result of an individual health check item."""

  def __init__(self, name, value):
    """Creates a new monitor result from a named monitor and its status string."""
    self.name = name
    semi_pos = value.find(';')
    self.detail = None
    if semi_pos > 0:
      self.status = value[0:semi_pos]
      self.detail = value[semi_pos+1:]
    else:
      self.status = value

  def __str__(self):
    if self.detail:
      return '%s: %s - %s' % (self.name, self.status, self.detail)
    else:
      return '%s: %s' % (self.name, self.status)

# BB enviroment sanity check
cas_host = os.getenv('MACHINE')
if not cas_host:
  sys.exit('MACHINE environment variable not set')
bb = os.getenv('BB')
if not bb:
  sys.exit('BB environment variable not set')
bbdisp = os.getenv('BBDISP')
if not bbdisp:
  sys.exit('BBDISP environment variable not set')

errmsg = None
status = None
conn = None
try:
  conn = HTTPSConnection(host=cas_host, port=cas_port, timeout=timeout)
  conn.request('GET', cas_context + '/status')
  health = HealthSummary(conn.getresponse())
  status = health.status
  errmsg = '\n'.join([str(m) for m in health.failed_monitors()])
except socket.timeout:
  status = 'ERROR'
  errmsg = 'Socket connection or read timeout (%ss)' % timeout
except socket.error, e:
  status = 'ERROR'
  errmsg = 'Socket error: %s' % e
except Exception, e:
  status = 'ERROR'
  errmsg = '%s::%s' % (e.__class__.__name__, str(e))
  if errmsg[-1] == ':':
    errmsg += '[no further details available]'
finally:
  if conn: conn.close()

bb_msg = 'status %s.%s %s %s\n\nCAS health check status is %s\n%s' % (
  cas_host,
  collection,
  STATUS_MAP[status],
  datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
  status,
  errmsg)
subprocess.call([bb, bbdisp, bb_msg])


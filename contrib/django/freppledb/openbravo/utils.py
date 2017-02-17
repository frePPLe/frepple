#
# Copyright (C) 2015 by frePPLe bvba
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
# General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import base64
from urllib.error import URLError
from urllib.request import urlopen, Request

import logging
logger = logging.getLogger(__name__)


def get_data(url, host, user, password, method='GET', headers=None, xmldoc=''):
  '''
  Utility function to communicate with the Openbravo web service.
  '''
  # Connect to Openbravo
  if not url or not host or not user or not password:
    raise Exception("Invalid configuration")  

  # Prepare HTTP(S) request  
  if xmldoc:
    data = xmldoc.encode(encoding='utf_8')
  else:
    data = None 
  req = Request("%s%s" % (host, url), method=method, data=data)
  req.add_header("User-Agent", "frePPLe-Openbravo connector")
  req.add_header("Content-type", 'text/xml; charset=\"UTF-8\"')
  if xmldoc:
    req.add_header("Content-length", "%s" % len(xmldoc))
  encoded = base64.encodestring(('%s:%s' % (user, password)).encode('utf-8'))[:-1]
  req.add_header("Authorization", "Basic %s" % encoded.decode('ascii'))
  if headers:
    for key, value in headers.items():
      req.add_header(key, "%s" % value)
      
  # Send the request and read the response
  result = None
  try:
    with urlopen(req, data) as response:
      return response.read().decode("utf-8")
  except URLError as e:
    logger.error("Failed %s connection to %s%s" % (method, host, url))
    if result:
      logger.error(result)
    raise e

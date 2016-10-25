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
import http.client
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)


def get_data(url, host, user, password, method='GET', headers=None, xmldoc=''):
  '''
  Utility function to communicate with the Openbravo web service.
  '''
  # Connect to Openbravo
  if not url or not host or not user or not password:
    raise Exception("Invalid configuration")
  full_url = urlparse("%s%s" % (host, url))
  if full_url.scheme == 'https':
    webservice = http.client.HTTPSConnection(host=full_url.netloc)
  else:
    webservice = http.client.HTTPConnection(host=full_url.netloc)
  if full_url.query:
    webservice.putrequest(method, "%s?%s" % (full_url.path, full_url.query))
  else:
    webservice.putrequest(method, full_url.path)
  webservice.putheader("Host", full_url.netloc)
  webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
  webservice.putheader("Content-type", 'text/xml; charset=\"UTF-8\"')
  webservice.putheader("Content-length", "%s" % len(xmldoc))
  encoded = base64.encodestring(('%s:%s' % (user, password)).encode('utf-8'))[:-1]
  webservice.putheader("Authorization", "Basic %s" % encoded.decode('ascii'))
  if headers:
    for key, value in headers.items():
      webservice.putheader(key, "%s" % value)
  webservice.endheaders()
  webservice.send(xmldoc.encode(encoding='utf_8'))

  # Get the Openbravo response
  response = webservice.getresponse()
  result = response.read().decode("utf-8")
  if response.status != http.client.OK:
    logger.error("Failed %s connection to %s%s" % (method, host, url))
    logger.error(result)
    raise Exception(response.reason)
  return result

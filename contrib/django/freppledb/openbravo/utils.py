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


def get_data(url, host, user, password):
  '''
  Utility function to read data from the Openbravo web service.
  '''
  # Connect to openbravo
  webservice = http.client.HTTPConnection(host)
  webservice.putrequest("GET", url)
  webservice.putheader("Host", host)
  webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
  webservice.putheader("Content-type", "text/html; charset=\"UTF-8\"")
  webservice.putheader("Content-length", "0")
  webservice.putheader("Authorization", "Basic %s" % base64.encodestring(
    ('%s:%s' % (user, password)).replace('\n', '').encode("utf-8")).decode("utf-8")
    )
  webservice.endheaders()
  webservice.send('')

  # Get the openbravo response
  response = webservice.getresponse()
  if response.status != http.client.OK:
    raise Exception(response.reason)
  return response.read().decode("utf-8")


def post_data(xmldoc, url, host, user, password):
  '''
  Utility function to post data to the Openbravo web service.
  '''
  # Send the data to openbravo
  webservice = http.client.HTTPConnection(host)
  webservice.putrequest("POST", url)
  webservice.putheader("Host", host)
  webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
  webservice.putheader("Content-type", 'text/xml')
  webservice.putheader("Content-length", str(len(xmldoc)))
  webservice.putheader("Authorization", "Basic %s" % base64.encodestring(
    ('%s:%s' % (user, password)).replace('\n', '').encode("utf-8")).decode("utf-8")
    )
  webservice.endheaders()
  webservice.send(xmldoc)

  # Get the openbravo response
  response = webservice.getresponse()
  if response.status != http.client.OK:
    raise Exception(response.reason)


def delete_data(url, host, user, password):
  '''
  Utility function to delete data from the Openbravo web service.
  '''
  # Connect to openbravo
  webservice = http.client.HTTPConnection(host)
  webservice.putrequest("DELETE", url)
  webservice.putheader("Host", host)
  webservice.putheader("User-Agent", "frePPLe-Openbravo connector")
  webservice.putheader("Content-type", "text/html; charset=\"UTF-8\"")
  webservice.putheader("Content-length", "0")
  webservice.putheader("Authorization", "Basic %s" % base64.encodestring(
    ('%s:%s' % (user, password)).replace('\n', '').encode("utf-8")).decode("utf-8")
    )
  webservice.endheaders()
  webservice.send('')

  # Get the openbravo response
  response = webservice.getresponse()
  if response.status != http.client.OK:
    raise Exception(response.reason)
  return response.read().decode("utf-8")


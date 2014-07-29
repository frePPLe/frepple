import openerp
import logging
from datetime import datetime, timedelta
from xml.etree.cElementTree import iterparse

logger = logging.getLogger(__name__)


class importer(object):

  def __init__(self, req, **kwargs):
    self.req = req
    self.database = kwargs.get('database', None)
    self.user = kwargs.get('user', None)
    password = kwargs.get('password', None)
    if not self.database or not self.user or not password:
      raise Exception("Authentication error")
    self.language = kwargs.get('language', 'en_US')
    self.company = kwargs.get('company', None)
    self.datafile = kwargs.get('frePPLe plan')
    # TODO set the language on the context
    self.req.session.authenticate(self.database, self.user, password)

  def run(self):
    msg = []
    count = 0

    # Parsing the XML data file
    for event, elem in iterparse(self.datafile, events=('start','end')):
      if event == 'end' and elem.tag == 'operationplan':
        qty = elem.find("quantity").text
        oper = elem.get('operation')
        strt = elem.find('start').text
        nd = elem.find('end').text
#         <operationplan id="1145" operation="Ship [LAP-E5] Laptop E5023 @ Your Company">
#         <demand name="SO001 1"/>
#         <start>2014-07-27T00:00:00</start>
#         <end>2014-07-27T00:00:00</end>
#         <quantity>3</quantity>
#         </operationplan>
        print(qty, oper, strt, nd)
        count += 1
        # Remove the element now to keep the DOM tree small
        root.clear()
      elif event == 'start' and elem.tag == 'operationplans':
        # Remember the root element
        root = elem

    # Be polite, and reply to the post
    msg.append("Processed %s uploaded records" % count)
    return '\n'.join(msg)


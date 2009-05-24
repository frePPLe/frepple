#
# Copyright (C) 2009 by Johan De Taeye
#
# This library is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA
#

# file : $URL: https://frepple.svn.sourceforge.net/svnroot/frepple/trunk/contrib/django/freppledb/admin.py $
# revision : $LastChangedRevision: 879 $  $LastChangedBy: jdetaeye $
# date : $LastChangedDate: 2008-12-30 12:07:36 +0100 (Tue, 30 Dec 2008) $

try:
  import cherrypy
except:
  # Alternative definitions when cherrypy is not available.
  # We only want to report the missing module when the REST web service is 
  # really used.
  def RESTwebservice(address=None, port=8080):
    raise ImportError, "no module named cherrypy"    
else:  
  
  def RESTwebservice(address=None, port=None):
    import socket
    
    # Pick up the address
    if address == None:
      try: address = socket.gethostbyname(socket.gethostname())
      except: address = '127.0.0.1'
    
    # Pick up the port number
    try: port = int(port or 8080)
    except: port = 8080

    # Validate the address and port number
    try:
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.bind( (address, port) )
      s.close()
    except socket.error, e:
      raise Exception("Invalid address '%s' and/or port '%s': %s" % (address, port, e))

    cherrypy.config.update({
      'server.socket_host': address,
      'server.socket_port': port,
      'log.access_file': None,
      'log.error_file': None,
      #'log.screen': False,
      #'tools.gzip.on': True,
      'log.level': 'info',
      })    
    config = {'/': 
        {
            #'tools.trailing_slash.on': False,
            #'server.environment': 'development',
            'server.threadPool': 10,
            'engine.autoreload_on': False,
            #'log.access_log.propagate': False ,
        }
    }
    print 'Web service starting on http://%s:%s/' % (address, port)
    cherrypy.quickstart(RESTinterface(), "", config=config)    
    print 'Web service stopped'

  class RESTinterface:
    top = [ 
      '<?xml version="1.0" encoding="UTF-8" ?>\n',
      '<plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n',
      ]
    bottom = [ 
      '</plan>\n',
      ]
 
    # Top-level interface handling URLs of the format:
    #    PUT /
    #    GET /
    @cherrypy.expose
    def POST(self):
      return "OK"
      
    # Top-level interface handling URLs of the format:
    #    PUT /
    #    GET /
    @cherrypy.expose
    def index(self):
      res = []
      for i in self.top: res.append(i)
      res.append('<locations>\n')
      for f in frepple.locations(): res.append(f.toXML())        
      res.append('</locations>\n')
      res.append('<customers>\n')
      for f in frepple.customers(): res.append(f.toXML())        
      res.append('</customers>\n')
      res.append('<operations>\n')
      for f in frepple.operations(): res.append(f.toXML())        
      res.append('</operations>\n')
      res.append('<buffers>\n')
      for f in frepple.buffers(): res.append(f.toXML())        
      res.append('</buffers>\n')
      res.append('<items>\n')
      for f in frepple.items(): res.append(f.toXML())        
      res.append('</items>\n')
      res.append('<flows>\n')
      for b in frepple.buffers():      
        for f in b.flows: res.append(f.toXML())        
      res.append('</flows>\n')
      res.append('<loads>\n')
      for b in frepple.resources():      
        for f in b.loads: res.append(f.toXML())        
      res.append('</loads>\n')
      res.append('<problems>\n')
      for f in frepple.problems(): res.append(f.toXML())        
      res.append('</problems>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for locations handling URLs of the format:
    #    GET /location/
    #    GET /location/<name>/
    @cherrypy.expose
    def location(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<locations>\n')
      if name:
        # Return a single location
        try:
          res.append(frepple.location(name=name,action="C").toXML())
        except:
          # Location not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all locations
        for f in frepple.locations(): res.append(f.toXML())        
      res.append('</locations>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for buffers handling URLs of the format:
    #    GET /buffer/
    #    GET /buffer/<name>/
    @cherrypy.expose
    def buffer(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<buffers>\n')
      if name:
        # Return a single buffer
        try:
          res.append(frepple.buffer(name=name,action="C").toXML())
        except:
          # Buffer not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all buffers
        for f in frepple.locations(): res.append(f.toXML())        
      res.append('</buffers>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for items handling URLs of the format:
    #    GET /item/
    #    GET /item/<name>/
    @cherrypy.expose
    def item(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<items>\n')
      if name:
        # Return a single item
        try:
          res.append(frepple.item(name=name,action="C").toXML())
        except:
          # Item not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all items
        for f in frepple.items(): res.append(f.toXML())        
      res.append('</items>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for demands handling URLs of the format:
    #    GET /demand/
    #    GET /demand/<name>/
    @cherrypy.expose
    def demand(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<demands>\n')
      if name:
        # Return a single demand
        try:
          res.append(frepple.demand(name=name,action="C").toXML())
        except:
          # Demand not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all locations
        for f in frepple.demands(): res.append(f.toXML())        
      res.append('</demands>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for resources handling URLs of the format:
    #    GET /resource/
    #    GET /resource/<name>/
    @cherrypy.expose
    def resource(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<resources>\n')
      if name:
        # Return a single resource
        try:
          res.append(frepple.resource(name=name,action="C").toXML())
        except:
          # Resource not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all resources
        for f in frepple.resources(): res.append(f.toXML())        
      res.append('</resources>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for calendars handling URLs of the format:
    #    GET /calendar/
    #    GET /calendar/<name>/
    @cherrypy.expose
    def calendar(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<calendars>\n')
      if name:
        # Return a single calendar
        try:
          res.append(frepple.calendar(name=name,action="C").toXML())
        except:
          # Calendar not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all calendars
        for f in frepple.calendars(): res.append(f.toXML())        
      res.append('</calendars>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for customers handling URLs of the format:
    #    GET /customer/
    #    GET /customer/<name>/
    @cherrypy.expose
    def customer(self, name=None):
      res = []
      for i in self.top: res.append(i)
      res.append('<customers>\n')
      if name:
        # Return a single customer
        try:
          res.append(frepple.customer(name=name,action="C").toXML())
        except:
          # Customer not found
          raise cherrypy.HTTPError(404,"entity not found")
      else:
        # Return all customers
        for f in frepple.customers(): res.append(f.toXML())        
      res.append('</customers>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for flows handling URLs of the format:
    #    GET /flow/
    @cherrypy.expose
    def flow(self):
      res = []
      for i in self.top: res.append(i)
      res.append('<flows>\n')
      for b in frepple.buffers():      
        for f in b.flows: res.append(f.toXML())        
      res.append('</flows>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for loads handling URLs of the format:
    #    GET /load/
    @cherrypy.expose
    def load(self):
      res = []
      for i in self.top: res.append(i)
      res.append('<loads>\n')
      for b in frepple.resources():      
        for f in b.loads: res.append(f.toXML())        
      res.append('</loads>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)
        
    # Interface for problems handling URLs of the format:
    #    GET /problem/
    @cherrypy.expose
    def problem(self):
      res = []
      for i in self.top: res.append(i)
      res.append('<problems>\n')
      for f in frepple.problems(): res.append(f.toXML())        
      res.append('</problems>\n')
      for i in self.bottom: res.append(i)
      return "".join(res)

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
# Foundation Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

# file : $URL$
# revision : $LastChangedRevision$  $LastChangedBy$
# date : $LastChangedDate$

try:
  import cherrypy
except:
  # Alternative definitions when cherrypy is not available.
  # We only want to report the missing module when the REST web service is 
  # really used.
  def RESTwebservice(address=None, port=8080):
    raise ImportError, "no module named cherrypy"    
else:  
  import os
  
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
            #'server.environment': 'development',
            'server.threadPool': 10,
            'engine.autoreload_on': False,
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
    
    current_dir = os.getcwd()
    
    @cherrypy.expose
    def testupload(self):
        return """
        <html><body>
            <form action=".." method="post" enctype="multipart/form-data">
            filename: <input type="file" name="myFile"/><br/>
            <input type="submit"/>
            </form>
        </body></html>
        """
        
    # Serve the XSD definition
    @cherrypy.expose
    def frepple_xsd(self):
      return cherrypy.lib.static.serve_file(
        os.path.join(self.current_dir, 'frepple.xsd'),
        content_type='application/xml'
        )
        
    # Serve the XSD definition
    @cherrypy.expose
    def frepple_core_xsd(self):
      return cherrypy.lib.static.serve_file(
        os.path.join(self.current_dir, 'frepple_core.xsd'),
        content_type='application/xml'
        )
        
    # Top-level interface handling URLs of the format:
    #    POST /
    #    PUT /
    #    GET /
    @cherrypy.expose
    def index(self):
      request = cherrypy.request
      cherrypy.response.headers['server'] = 'frepple/%s' % frepple.version
      cherrypy.response.headers['content-type'] = 'application/xml'
      if request.method == 'GET': 
        # GET request 
        res = []
        for i in self.top: res.append(i)
        res.append('<locations>\n')
        for f in frepple.locations(): res.append(f.toXML())        
        res.append('</locations>\n')
        res.append('<customers>\n')
        for f in frepple.customers(): res.append(f.toXML())        
        res.append('</customers>\n')
        res.append('<calendars>\n')
        for f in frepple.calendars(): res.append(f.toXML())        
        res.append('</calendars>\n')
        res.append('<operations>\n')
        for f in frepple.operations(): res.append(f.toXML())        
        res.append('</operations>\n')
        res.append('<items>\n')
        for f in frepple.items(): res.append(f.toXML())        
        res.append('</items>\n')
        res.append('<buffers>\n')
        for f in frepple.buffers(): res.append(f.toXML())        
        res.append('</buffers>\n')
        res.append('<demands>\n')
        for f in frepple.demands(): res.append(f.toXML())        
        res.append('</demands>\n')
        res.append('<resources>\n')
        for f in frepple.resources(): res.append(f.toXML())        
        res.append('</resources>\n')
        res.append('<operationplans>\n')
        for f in frepple.operationplans(): res.append(f.toXML())        
        res.append('</operationplans>\n')
        res.append('<problems>\n')
        for f in frepple.problems(): res.append(f.toXML())        
        res.append('</problems>\n')
        for i in self.bottom: res.append(i)
        return "".join(res)
      else:
        # POST and PUT requests
        error = []
        for f in cherrypy.request.params:
          try:
            frepple.readXMLdata(cherrypy.request.params[f].file.read())       
          except Exception, e:
            error.append("%s : %s" % (f,e))
        if len(error) > 0:          
          return '\n'.join(error)
        return "OK"
        
    # A generic way to expose XML data.
    # Use this decorator function to decorate a generator function. 
    def simpleXMLdata(gen):
      @cherrypy.expose
      def decorator(self, *__args, **__kw):
        cherrypy.response.headers['server'] = 'frepple/%s' % frepple.version
        if cherrypy.request.method == 'GET': 
          # Get requests
          cherrypy.response.headers['content-type'] = 'application/xml'
          res = []
          for i in self.top: res.append(i)
          for i in gen(self, *__args): res.append(i)
          for i in self.bottom: res.append(i)
          return "".join(res)
        elif cherrypy.request.method  == 'POST' or cherrypy.request.method == 'PUT': 
          # Post and put requests
          cherrypy.response.headers['content-type'] = 'application/xml'
          res = []
          for i in gen(self, *__args): res.append(i)
          return "".join(res)
        else:
          # Other HTTP verbs (such as head, delete, ...) are not supported
          raise cherrypy.HTTPError(404,"Not found")
      return decorator
      
    # Interface for locations handling URLs of the format:
    #    GET /location/
    #    GET /location/<name>/
    #    POST /location/<name>/?<parameter>=<value>
    @simpleXMLdata
    def location(self, name=None):
      if cherrypy.request.method == 'GET':
        # GET information
        yield '<locations>\n'
        if name:
          # Return a single location
          try:
            yield frepple.location(name=name,action="C").toXML()
          except:
            # Location not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all locations
          for f in frepple.locations(): yield f.toXML()        
        yield '</locations>\n'          
      else:
        # Create or update a location
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.location(name=name)
        except:
          # Location not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for buffers handling URLs of the format:
    #    GET /buffer/
    #    GET /buffer/<name>/
    @simpleXMLdata
    def buffer(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<buffers>\n'
        if name:
          # Return a single buffer
          try:
            yield frepple.buffer(name=name,action="C").toXML()
          except:
            # Buffer not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all buffers
          for f in frepple.locations(): yield f.toXML()
        yield '</buffers>\n'
      else:
        # Create or update a buffer
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.buffer(name=name)
        except:
          # Buffer not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for items handling URLs of the format:
    #    GET /item/
    #    GET /item/<name>/
    @simpleXMLdata
    def item(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<items>\n'
        if name:
          # Return a single item
          try:
            yield frepple.item(name=name,action="C").toXML()
          except:
            # Item not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all items
          for f in frepple.items(): yield f.toXML()
        yield '</items>\n'
      else:
        # Create or update an item
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.item(name=name)
        except:
          # Item not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
          
    # Interface for operations handling URLs of the format:
    #    GET /operation/
    #    GET /operation/<name>/
    @simpleXMLdata
    def operation(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<operations>\n'
        if name:
          # Return a single operation
          try:
            yield frepple.operation(name=name,action="C").toXML()
          except:
            # Item not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all items
          for f in frepple.operations(): yield f.toXML()
        yield '</operations>\n'
      else:
        # Create or update an operation
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.operation(name=name)
        except:
          # Operation not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for demands handling URLs of the format:
    #    GET /demand/
    #    GET /demand/<name>/
    @simpleXMLdata
    def demand(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<demands>\n'
        if name:
          # Return a single demand
          try:
            yield frepple.demand(name=name,action="C").toXML()
          except:
            # Demand not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all locations
          for f in frepple.demands(): yield f.toXML()
        yield '</demands>\n'
      else:
        # Create or update a demand
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.demand(name=name)
        except:
          # Demand not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for resources handling URLs of the format:
    #    GET /resource/
    #    GET /resource/<name>/
    @simpleXMLdata
    def resource(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<resources>\n'
        if name:
          # Return a single resource
          try:
            yield frepple.resource(name=name,action="C").toXML()
          except:
            # Resource not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all resources
          for f in frepple.resources(): yield f.toXML()
        yield '</resources>\n'
      else:
        # Create or update a resource
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.resource(name=name)
        except:
          # Resource not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for calendars handling URLs of the format:
    #    GET /calendar/
    #    GET /calendar/<name>/
    @simpleXMLdata
    def calendar(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<calendars>\n'
        if name:
          # Return a single calendar
          try:
            yield frepple.calendar(name=name,action="C").toXML()
          except:
            # Calendar not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all calendars
          for f in frepple.calendars(): yield f.toXML()
        yield '</calendars>\n'
      else:
        # Create or update a calendar
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.calendar(name=name)
        except:
          # Calendar not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for customers handling URLs of the format:
    #    GET /customer/
    #    GET /customer/<name>/
    @simpleXMLdata
    def customer(self, name=None):
      if cherrypy.request.method == 'GET':
        yield '<customers>\n'
        if name:
          # Return a single customer
          try:
            yield frepple.customer(name=name,action="C").toXML()
          except:
            # Customer not found
            raise cherrypy.HTTPError(404,"Entity not found")
        else:
          # Return all customers
          for f in frepple.customers(): yield f.toXML()
        yield '</customers>\n'
      else:
        # Create or update a customer
        if name == None: raise cherrypy.HTTPError(404,"Entity not found")
        try:
          loc = frepple.customer(name=name)
        except:
          # Customer not found
          raise cherrypy.HTTPError(404,"Entity not found")
        ok = True
        for i in cherrypy.request.params:
          try:
            setattr(loc, i, cherrypy.request.params[i])
          except Exception, e:
            yield "Error: %s\n" % e
            ok = False
        if ok: yield "OK\n"
        
    # Interface for flows handling URLs of the format:
    #    GET /flow/
    @simpleXMLdata
    def flow(self):
      if cherrypy.request.method == 'GET':
        yield '<flows>\n'
        for b in frepple.buffers():      
          for f in b.flows: yield f.toXML()
        yield '</flows>\n'
      else:
        raise cherrypy.HTTPError(404,"Not supported")
        
    # Interface for loads handling URLs of the format:
    #    GET /load/
    @simpleXMLdata
    def load(self):
      if cherrypy.request.method == 'GET':
        yield '<loads>\n'
        for b in frepple.resources():      
          for f in b.loads: yield f.toXML()
        yield '</loads>\n'
      else:
        raise cherrypy.HTTPError(404,"Not supported")
        
    # Interface for problems handling URLs of the format:
    #    GET /problem/
    @simpleXMLdata
    def problem(self):
      if cherrypy.request.method == 'GET':
        yield '<problems>\n'
        for f in frepple.problems(): yield f.toXML()
        yield '</problems>\n'
      else:
        raise cherrypy.HTTPError(404,"Not supported")

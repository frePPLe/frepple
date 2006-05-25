/***************************************************************************
file : $URL$
version : $LastChangedRevision$  $LastChangedBy$
date : $LastChangedDate$
email : jdetaeye@users.sourceforge.net
***************************************************************************/

/***************************************************************************
*                                                                         *
* Copyright (C) 2006 by Johan De Taeye                                    *
*                                                                         *
* This library is free software; you can redistribute it and/or modify it *
* under the terms of the GNU Lesser General Public License as published   *
* by the Free Software Foundation; either version 2.1 of the License, or  *
* (at your option) any later version.                                     *
*                                                                         *
* This library is distributed in the hope that it will be useful,         *
* but WITHOUT ANY WARRANTY; without even the implied warranty of          *
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser *
* General Public License for more details.                                *
*                                                                         *
* You should have received a copy of the GNU Lesser General Public        *
* License along with this library; if not, write to the Free Software     *
* Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA *
*                                                                         *
***************************************************************************/
package frepple.backend;

import javax.management.MBeanServer;
import javax.management.ObjectName;
import javax.naming.InitialContext;
import org.apache.log4j.Logger;
import org.jboss.mx.util.MBeanServerLocator;

/**
 */
public class ConnectionFactory {

	private static Class connectionClass = null;
    private static Logger log = Logger.getLogger(ConnectionFactory.class);

	public static api create() throws Exception {
	    
	  Object instance;
	  
	  // Pick up the class name
		if(connectionClass == null) {
			try {
			  InitialContext jndiContext = new InitialContext();
			  String classname = (String) jndiContext.lookup("java:comp/env/Frepple/BackendConnection");
			  connectionClass = Class.forName(classname);
				log.info("Using frepple connection class " + connectionClass);
			} catch (Exception e) {
				log.error("Initialization of frepple connection failed:" + e);
				throw e;
			}
		}
		
		// Create the connection
		try {
			instance = connectionClass.newInstance();
		} catch (Exception e) {
			e.printStackTrace();
			throw e;
		}
		
		// Register the connection with JMX server
		try {
		  // MBeanServer server = MBeanServerFactory.createMBeanServer(); xxx
	    MBeanServer server = MBeanServerLocator.locateJBoss();
      ObjectName objName = new ObjectName("DefaultDomain:Name=frepple");
      server.registerMBean((frepple.backend.webservice.connection)(instance), objName);
  		//server.createMBean(connectionClass.getName(), objName);
			log.info("Registered frepple with JMX console");
		} catch (Exception e) {
      e.printStackTrace();
      throw e;
    } 
		
		return (api) instance;
	}
}

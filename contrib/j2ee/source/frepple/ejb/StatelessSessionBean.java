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
package frepple.ejb;

import java.rmi.RemoteException;
import javax.ejb.EJBException;
import javax.ejb.SessionBean;
import javax.ejb.SessionContext;
import org.apache.log4j.Logger;
import frepple.backend.ConnectionFactory;
import frepple.backend.api;


/**
 * @ejb.bean name="StatelessSession"
 *           display-name="Name for StatelessSession"
 *           description="Description for StatelessSession"
 *           jndi-name="ejb/StatelessSession"
 *           type="Stateless"
 *           view-type="local"        
 */
public class StatelessSessionBean implements SessionBean, api {

	private static final long serialVersionUID = 1L;
	private api connection = null;
	private SessionContext context = null;
    private static Logger log = Logger.getLogger(StatelessSessionBean.class);
	
	/**
	 */
	public StatelessSessionBean() {
		super();
		log.debug("Creating SessionBean " + hashCode());
	}

	/**
	 */
	public void setSessionContext(SessionContext arg0)
		throws EJBException,
		RemoteException {
		context = arg0;
	}

	/**
	 */
	public void ejbRemove() throws EJBException, RemoteException {
	}

	/**
	 */
	public void ejbActivate() throws EJBException, RemoteException {
		log.debug("Activating SessionBean " + hashCode());
		try {
            connection.initialize();
        } catch (Exception e) {
            e.printStackTrace();
            throw new EJBException("Can't create backend connection");
        }
	}

	/**
	 */
	public void ejbPassivate() throws EJBException, RemoteException {
		log.debug("Passivating SessionBean " + hashCode());
		connection = null;
	}

	/**
	 */
	public void initialize() {
		log.debug("Initializing SessionBean " + hashCode());
		try {
            connection = (api) ConnectionFactory.create();
    		connection.initialize();
        } catch (Exception e) {
            e.printStackTrace();
        }
	}

	/**
	 */
	public void readXMLData(String x) {
		connection.readXMLData(x);
	}

	/**
	 */
	public void saveFile(String x) {
		connection.saveFile(x);
	}

	/**
	 */
	public String saveString() {
		return connection.saveString();
	}

	public void ejbCreate() {
	}

	public boolean isConnected() {return true;}
	
  public void disconnect() {
  }
  
  public void testConnection() {
  }
  
  public void reset() {
  }

}

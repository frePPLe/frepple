/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/contrib/j2ee/source/frepple/jms/MessageBean.java $
  version : $LastChangedRevision$  $LastChangedBy$
  date : $LastChangedDate$
  email : jdetaeye@users.sourceforge.net
***************************************************************************/

/***************************************************************************
*                                                                         *
* Copyright (C) 2007 by Johan De Taeye                                    *
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

package frepple.jms;


import javax.ejb.EJBException;
import javax.ejb.MessageDrivenBean;
import javax.ejb.MessageDrivenContext;
import javax.jms.*;
import javax.naming.InitialContext;

import org.apache.log4j.Logger;

import frepple.backend.ConnectionFactory;
import frepple.backend.api;


/**
 * @ejb.bean name="MessageBean"
 *           display-name="Frepple EJB MessageBean"
 *           description="A message bean "
 *           destination-type="javax.jms.Queue"
 *           acknowledge-mode="Auto-acknowledge"
 */
public class MessageBean implements MessageDrivenBean, MessageListener {

	private static final long serialVersionUID = 1L;
	private MessageDrivenContext ctx = null;
    private QueueConnection conn;
    private static Logger log = Logger.getLogger(MessageBean.class);
    private api freppleconn = null;

	/**
	 * @throws Exception */
	public MessageBean() throws Exception {
		super();
		// Initialize a connection to the frepple backend
		freppleconn = ConnectionFactory.create();
	}

	/* (non-Javadoc)
	 * @see javax.ejb.MessageDrivenBean#setMessageDrivenContext(javax.ejb.MessageDrivenContext)
	 */
	public void setMessageDrivenContext(MessageDrivenContext arg0)
		throws EJBException {
        ctx = arg0;
	}

	/* (non-Javadoc)
	 * @see javax.ejb.MessageDrivenBean#ejbRemove()
	 */
	public void ejbRemove() throws EJBException {
		log.debug("Removing MessageBean " + hashCode());
        ctx = null;
        try {
            if (conn != null) {
                conn.close();
            }
        } catch(JMSException e) {
            e.printStackTrace();
        }
	}

	/**
	 * @see javax.jms.MessageListener#onMessage(javax.jms.Message)
	 */
	public void onMessage(Message msg) {
	  try {
	    TextMessage tm = (TextMessage) msg;
	    log.debug("Message received on MessageBean " + hashCode() + ": " + tm.getText());
	    freppleconn.readXMLData(tm.getText());
	  } catch(Throwable t) {
	    t.printStackTrace();
	  }
	}

	/**
	 * Default create method
	 *
	 * @throws CreateException
	 */
	public void ejbCreate() {
        log.debug("Creating MessageBean " + hashCode());
        try {
            InitialContext iniCtx = new InitialContext();
            Object tmp = iniCtx.lookup("java:comp/env/jms/QCF");
            QueueConnectionFactory qcf = (QueueConnectionFactory) tmp;
            conn = qcf.createQueueConnection();
            conn.start();
        } catch (Exception e) {
            throw new EJBException("Failed to create MessageBean:", e);
        }
	}
}

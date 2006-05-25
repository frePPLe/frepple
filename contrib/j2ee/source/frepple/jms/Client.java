/***************************************************************************
  file : $URL: file:///develop/SVNrepository/frepple/trunk/contrib/j2ee/source/frepple/jms/Client.java $
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

package frepple.jms;

import javax.jms.*;
import javax.naming.*;

/**
 */
public class Client {
    static QueueConnection conn;
    static QueueSession session;
	static Queue queB;

	public static void main(String[] args) {
		System.out.println("Start sending messages...");
		try {
			
			// Init
			InitialContext iniCtx = new InitialContext();
			Object tmp = iniCtx.lookup("ConnectionFactory");
			QueueConnectionFactory qcf = (QueueConnectionFactory) tmp;
			conn = qcf.createQueueConnection();
			queB = (Queue) iniCtx.lookup("queue/B");
	        session = conn.createQueueSession(false,
	                QueueSession.AUTO_ACKNOWLEDGE);
			conn.start();
			
			// Send a few text msgs to queB
			QueueSender send = session.createSender(queB);

			for (int m = 0; m < 10; m++) {
				TextMessage tm = session.createTextMessage("text message #" + m);
				tm.setJMSType("frepple-xml");
				send.send(tm);
			}
			
			// Finalize
			conn.stop();
	        session.close();
			conn.close();
		} catch (Exception e) {
			e.printStackTrace();
		}
		System.out.println("End sending messages");
	}
}

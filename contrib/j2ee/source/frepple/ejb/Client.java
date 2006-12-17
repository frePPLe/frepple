/***************************************************************************
file : $URL$
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
package frepple.ejb;

import java.rmi.RemoteException;

import javax.ejb.CreateException;
import javax.naming.InitialContext;
import javax.naming.NamingException;

/**
 */
public class Client {

	public static void main(String[] args) throws RemoteException, CreateException, NamingException {

		// Get the Profile bean's home interface
		InitialContext iniCtx = new InitialContext();
		Object tmp = iniCtx.lookup("frepple/ejb");
		StatelessSessionBeanRemoteHome pHome = (StatelessSessionBeanRemoteHome) tmp;

		// Create a profile for a person
		System.out.println("Creating a session bean");
		StatelessSessionBeanRemote bean = pHome.create();

		// Test the session bean
		bean.initialize();
		bean.readXMLData("test");
	}
}

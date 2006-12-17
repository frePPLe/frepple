/***************************************************************************
    file     : $URL: file:///develop/SVNrepository/frepple/trunk/contrib/j2ee/source/frepple/webservice/client.java $
    revision : $LastChangedRevision$  $LastChangedBy$
    date     : $LastChangedDate$
    email    : jdetaeye@users.sourceforge.net
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

package frepple.webservice;

import javax.xml.namespace.QName;

import org.apache.axis.AxisFault;
import org.apache.axis.client.Call;
import org.apache.axis.client.Service;

/** This is a test client for the frepple backend web service.
 */
public class client {

	public static void main(String[] args) {
		 try {

		 	// Parameter for the web service location
		 	String endpoint = "http://localhost/axis/planner";

		 	// Set the appropriate parameters for the call
			Service service = new Service();
			Call call = (Call) service.createCall();
			call.setTargetEndpointAddress(new java.net.URL(endpoint));
	        call.setUseSOAPAction(true);
	        call.setProperty(org.apache.axis.AxisEngine.PROP_DOMULTIREFS, Boolean.FALSE);
	        call.setEncodingStyle(null);
	        call.setProperty(org.apache.axis.client.Call.SEND_TYPE_ATTR, Boolean.TRUE);
	        call.setSOAPVersion(org.apache.axis.soap.SOAPConstants.SOAP11_CONSTANTS);

	        // Call the web service for the 'add' operation
	        call.setOperationName(new QName("", "add"));
	        call.setSOAPActionURI("planner#add");
			Integer ret = (Integer) call.invoke(new Object[] {new Integer(10), new Integer(11)});
			System.out.println("aaaa" + ret);

	        // Call the web service for the 'inputxml' operation
			call.setOperationName(new QName("", "InputXML"));
	        call.setSOAPActionURI("planner#InputXML");
			ret = (Integer) call.invoke(new Object[] {"Hello!"});
			System.out.println("bbbb" + ret);

		} catch (AxisFault e) {
			System.err.println(e.toString());
			e.printStackTrace();
		} catch (Exception e) {
			System.err.println(e.toString());
			e.printStackTrace();
		}

	}
}

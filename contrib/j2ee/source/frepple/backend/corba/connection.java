/***************************************************************************
file : $URL$
version : $LastChangedRevision$  $LastChangedBy$
date : $LastChangedDate$
email : johan_de_taeye@yahoo.com
***************************************************************************/

/***************************************************************************
*                                                                         *
* Copyright (C) 2005 by Johan De Taeye                                    *
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
package frepple.backend.corba;

import frepple.backend.api;

/**
 */
public class connection implements api {

	/* (non-Javadoc)
	 * @see frepple.backend.api#initialize()
	 */
	public void initialize() {
		// TODO Auto-generated method stub
		System.out.println("initialize");
	}

	/* (non-Javadoc)
	 * @see frepple.backend.api#readXMLData(java.lang.String)
	 */
	public void readXMLData(String x) {
		// TODO Auto-generated method stub
		System.out.println("readXMLdata " + x);	
	}

	/* (non-Javadoc)
	 * @see frepple.backend.api#saveFile(java.lang.String)
	 */
	public void saveFile(String x) {
		// TODO Auto-generated method stub
		System.out.println("saveFile to " + x);
	}

	/* (non-Javadoc)
	 * @see frepple.backend.api#saveString()
	 */
	public String saveString() {
		// TODO Auto-generated method stub
		System.out.println("saveString");
		return new String("hello");
	}

	public boolean isConnected() {return true;}
	
  public void disconnect() {
  }
  
  public void testConnection() {
  }
  
  public void reset() {
  }
}

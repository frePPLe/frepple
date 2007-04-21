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

class frepple_java
{

  public static void main(String args[])
  {
    boolean error = false;
    try
    {
      System.out.println("Reading base data:");
      freppleJNI.FreppleReadXMLData("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" +
      "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" +
        "<NAME>actual plan</NAME>" +
        "<DESCRIPTION>Anything goes</DESCRIPTION>" +
        "<CURRENT>2007-01-01T00:00:01</CURRENT>" +
        "<OPERATIONS>" +
          "<OPERATION NAME=\"make end item\" xsi:type=\"OPERATION_FIXED_TIME\">" +
            "<DURATION>24:00:00</DURATION>" +
          "</OPERATION>" +
        "</OPERATIONS>" +
        "<ITEMS>" +
          "<ITEM NAME=\"end item\">" +
            "<OPERATION NAME=\"delivery end item\" xsi:type=\"OPERATION_FIXED_TIME\">" +
              "<DURATION>24:00:00</DURATION>" +
            "</OPERATION>" +
          "</ITEM>" +
        "</ITEMS>" +
        "<BUFFERS>" +
          "<BUFFER NAME=\"end item\">" +
            "<PRODUCING NAME=\"make end item\"/>" +
            "<ITEM NAME=\"end item\"/>" +
          "</BUFFER>" +
        "</BUFFERS>" +
        "<RESOURCES>" +
          "<RESOURCE NAME=\"Resource\">" +
            "<MAXIMUM NAME=\"Capacity\" xsi:type=\"CALENDAR_FLOAT\">" +
              "<BUCKETS>" +
                "<BUCKET START=\"2007-01-01T00:00:01\" VALUE=\"1\"/>" +
              "</BUCKETS>" +
            "</MAXIMUM>" +
            "<LOADS>" +
              "<LOAD>" +
                "<OPERATION NAME=\"make end item\" />" +
              "</LOAD>" +
            "</LOADS>" +
          "</RESOURCE>" +
        "</RESOURCES>" +
        "<FLOWS>" +
          "<FLOW xsi:type=\"FLOW_START\">" +
            "<OPERATION NAME=\"delivery end item\"/>" +
            "<BUFFER NAME=\"end item\"/>" +
            "<QUANTITY>-1</QUANTITY>" +
          "</FLOW>" +
          "<FLOW xsi:type=\"FLOW_END\">" +
            "<OPERATION NAME=\"make end item\"/>" +
            "<BUFFER NAME=\"end item\"/>" +
            "<QUANTITY>1</QUANTITY>" +
          "</FLOW>" +
        "</FLOWS>" +
        "<DEMANDS>" +
          "<DEMAND NAME=\"order 1\">" +
            "<QUANTITY>10</QUANTITY>" +
            "<DUE>2007-01-04T09:00:00</DUE>" +
            "<PRIORITY>1</PRIORITY>" +
            "<ITEM NAME=\"end item\"/>" +
            "<POLICY>PLANLATE</POLICY>" +
          "</DEMAND>" +
        "</DEMANDS>" +
      "</PLAN>",true,false);
      System.out.println(" OK");

      System.out.println("Adding an item:");
      freppleJNI.FreppleReadXMLData("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" +
        "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" +
          "<ITEMS>" +
            "<ITEM NAME=\"New Item\"/>" +
          "</ITEMS>" +
        "</PLAN>", true, false);
      System.out.println(" OK");

      System.out.println("Saving frepple model to a string:");
      System.out.println(freppleJNI.FreppleSaveString());
      System.out.println(" OK");

      System.out.println("Saving frepple model to a file:");
      freppleJNI.FreppleSaveFile("turbo.java.xml");
      System.out.println(" OK");

      System.out.println("Passing invalid XML data to frepple:");
      freppleJNI.FreppleReadXMLData("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" +
        "<PLAN xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" +
          "<XXDESCRIPTION>Dummy</XXDESCRIPTION>" +
        "</PLAN>", true, false);
      System.out.println(" OK");

      System.out.println("End of frepple commands");
      }
      catch (Exception e)
      {
        System.out.println("Runtime exception caught: " + e.getMessage());
        //print "Caught an unknown exception"
        e.printStackTrace();
        error = true;
      }

    if (!error) System.out.println("All commands passed without error");
    System.out.println( "Exiting...");

  }
}

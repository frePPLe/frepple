<?xml version="1.0" encoding="UTF-8"?>
<!--

 Copyright (C) 2006 by Johan De Taeye

 This library is free software; you can redistribute it and/or modify it
 under the terms of the GNU Lesser General Public License as published
 by the Free Software Foundation; either version 2.1 of the License, or
 (at your option) any later version.

 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
 General Public License for more details.

 You should have received a copy of the GNU Lesser General Public
 License along with this library; if not, write to the Free Software
 Foundation Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA

 file : $HeadURL: file:///develop/SVNrepository/frepple/trunk/configure.in $
 revision : $LastChangedRevision$  $LastChangedBy$
 date : $LastChangedDate$
 email : jdetaeye@users.sourceforge.net
 
  xmlns="http://www.w3.org/TR/REC-html40">
-->
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  >
<xsl:output method="html" indent="no" />
<xsl:template match="/PLAN/BUFFERS">
  <html>
  <head>
  <link href="styles.css" rel="stylesheet" type="text/css"/>  
  <script type="text/javascript" src="filter.js"></script>
  </head>
  <body>
    <form>
    <table border="1">
    <tr bgcolor="#a5a5ff">
      <th align="left">Name</th> 
      <th align="left">Location</th> 
      <th align="left">Item</th> 
      <th align="left"> </th> 
      <th align="left">B1</th> 
      <th align="left">B2</th> 
      <th align="left">B3</th> 
    </tr>
    <xsl:for-each select="BUFFER">
    <!-- <xsl:sort select="@NAME"/> -->
    <tr>
      <td><xsl:value-of select="@NAME" /></td>
      <td><xsl:value-of select="LOCATION/@NAME" /></td>
      <td><xsl:value-of select="ITEM/@NAME" /></td>
      <td>Supply</td>
      <td><input type="text" size="3" value="1" onChange="kiwi(this,1);"/></td>
      <td><input type="text" size="3" value="1" onChange="kiwi(this,2);"/></td>
      <td><input type="text" size="3" value="1" onChange="kiwi(this,3);"/></td>
    </tr>
    <tr>
      <td></td>
      <td></td>
      <td></td>
      <td>Demand</td>
      <td>0</td>
      <td>2</td>
      <td>0</td>
    </tr>
    <tr>
      <td></td>
      <td></td>
      <td></td>
      <td>Onhand</td>
      <td>1</td>
      <td>0</td>
      <td>1</td>
    </tr>
    </xsl:for-each>
  </table>
  </form>
  </body>
  </html>
</xsl:template></xsl:stylesheet>

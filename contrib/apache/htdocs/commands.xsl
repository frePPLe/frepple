<?xml version="1.0" encoding="ISO-8859-1"?>
<!--

 Copyright (C) 2007 by Johan De Taeye

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

 file : $HeadURL$
 revision : $LastChangedRevision$  $LastChangedBy$
 date : $LastChangedDate$
 email : jdetaeye@users.sourceforge.net

-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
  <html>
  <head>
  <link href="/styles.css" rel="stylesheet" type="text/css"/>
  <script type="text/javascript" src="../filter.js"></script>
  <script type="text/javascript" language="JavaScript">
  <![CDATA[
  // Execute a remote xml file
  function cmd(filename)
  {
    var xmlhttp = createXMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
      if (xmlhttp.readyState==4)
        top.data.document.getElementById("content").innerHTML +=
          "<p>" + (new Date().toLocaleString()) + ": Finished executing '" + filename + "': " + xmlhttp.responseText + "</p>";
    }
    xmlhttp.open("POST", "/cmd/" + filename, true);
    xmlhttp.send(null);
    top.data.document.getElementById("content").innerHTML +=
      "<p>" + (new Date().toLocaleString()) + ": Start executing '" + filename + "'</p>";
    return false;
  }
  ]]>
  </script>
  </head>
  <body>
    <h2>Remote Commands</h2>
    Execute pre-defined command files stored on the server:
    <form name="remote" onsubmit="return false;">
    <table border="1">
    <tr class="header">
      <th align="left">Name</th>
      <th align="left">Execute</th>
      <th align="left">Description</th>
      <th align="left">File</th>
    </tr>
    <xsl:for-each select="COMMANDS/COMMAND">
    <tr>
      <td align="center">
        <b><xsl:value-of select="NAME"/></b>
      </td>
      <td>
        <input id="{FILE}" type="button" onclick="return cmd(id);" value="Execute"/>
      </td>
      <td><xsl:value-of select="DESCRIPTION"/></td>
      <td>
        <a target="_blank" href="{FILE}">
        <xsl:value-of select="FILE"/>
        </a>
      </td>
    </tr>
    </xsl:for-each>
    </table>
    </form>
  </body>
  </html>
</xsl:template>

</xsl:stylesheet>

<?xml version="1.0" encoding="ISO-8859-1"?>
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
 
-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
  <html>
  <head>
  <link href="../styles.css" rel="stylesheet" type="text/css"/>
  <script type="text/javascript" src="../filter.js"></script>
  <script type="text/javascript" language="JavaScript">
  <![CDATA[

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
    <h2>Commands</h2>
    <form onsubmit="return false;">
    <table border="1">
    <tr bgcolor="#9acd32">
      <th align="left">Name</th>
      <th align="left">Description</th>
      <th align="left">File</th>
    </tr>
    <xsl:for-each select="COMMANDS/COMMAND">
    <tr>
      <td align="center">
        <b><xsl:value-of select="NAME"/></b>
        <input id="{FILE}" type="button" onclick="return cmd(id);" value="Run"/>
      </td>
      <td><xsl:value-of select="DESCRIPTION"/></td>
      <td>
        <a target="data" href="{FILE}">
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
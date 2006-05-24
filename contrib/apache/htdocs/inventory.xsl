<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns="http://www.w3.org/TR/REC-html40">
<xsl:template match="/PLAN/BUFFERS">
  <html>
  <head>
  <link href="styles.css" rel="stylesheet" type="text/css"/>  
  <script type="text/javascript" src="filter.js"></script>
  </head>
  <body>
    <form>
    <table border="1">
    <tr bgcolor="#9acd32">
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
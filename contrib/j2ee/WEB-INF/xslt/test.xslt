<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns="http://www.w3.org/1999/xhtml">
  <xsl:output method="xml" indent="yes" encoding="UTF-8"
/>
     
  <!-- Define the parameters:
    a: name of the item
    b: description of the item
    c: name of the delivery operation
  -->
  <xsl:param name="a">default item name</xsl:param>
  <xsl:param name="b"/>
  <xsl:param name="c"/>
  
  <!-- Create the output xml  -->
  <xsl:template match="/">
	<PLAN xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
	<ITEMS>
	  <ITEM NAME="{$a}">
        <xsl:if test="$c" >
        <DESCRIPTION><xsl:value-of select="$b"/></DESCRIPTION>
	    </xsl:if>
        <xsl:if test="$c" >
	    <OPERATION NAME="{$c}"/>
	    </xsl:if>
	  </ITEM>
	</ITEMS>
    </PLAN>
  </xsl:template>
    
</xsl:stylesheet>

=======
XML API
=======

The planning engine natively reads XML documents.

Here's a simple annotated example of a data file in frePPLe's format:

  .. code-block:: XML

      <?xml version="1.0" encoding="UTF-8"?>
      <plan xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <items>
          <!-- Define an item. -->
          <item name="item X">
        </items>
        <demands>
          <!-- Find or create an order. It also implicitly defines items, locations and 
               customers that are referenced. --> 
          <demand name="order A">
            <item name="item X"/>
            <location name="depot Y"/>
            <customer name="client Z"/>
            <quantity>10</quantity>
            <due>2016-01-10T00:00:00</due>
            <priority>1</priority>
          </demand>
          <!-- Similar to previous element, but using attributes for all simple data types. -->            
          <demand name="order B" quantity="2" due="2016-03-11T00:00:00" priority="1">
            <item name="item X"/>
            <location name="depot Y"/>
            <customer name="client Z"/>
          </demand>          
        </demands>
        <!-- Define an operation, including all materials it produces or consumes, and 
          all resources it uses. --> 
        <operations>
          <operation name="make item X" xsi:type="operation_time_per">
            <flows>
              <flow xsi:type="flow_end">
                <item name="item X"/>
                <quantity>-1</quantity>
              </flow>
              <flow xsi:type="flow_start">
                <item name="component 1"/>
                <quantity>-1</quantity>
              </flow>
            </flows>
            <loads>
              <load>
                <resource name="workcenter alfa"/>
                <quantity>1</quantity>
              </load>
            </loads>
            <duration>PT1H</duration>    <!-- 1 hour in XML format -->
            <duration_per>PT5M</duration_per>  <!-- 5 minutes in XML format -->
          </operation>
        </operations>
        <!-- Material consumption definitions as above, but not structured inside 
           an operation element. Because of the flexible way that elements are allowed
           to be nested you can choose a layout of the XML document that best suits
           your data source and taste. -->
        <flows>
          <flow xsi:type="flow_start">
            <operation name="make item X"/>
            <item name="another component"/>
            <quantity>-1</quantity>
          </flow>
        </flows>
      </plan>

The XML format is defined in `XML schema`_ format in
the file https://raw.githubusercontent.com/frePPLe/frePPLe/master/bin/frepple.xsd
(use master to see the development version, or replace it with the version number you're using).
The engine can optionally validate the incoming documents against this schema and reject
invalid data files. 

The following encodings are supported for XML data: ASCII, UTF-8, UTF-16 (Big/Small Endian),
UTF-32(Big/Small Endian), EBCDIC code pages IBM037, IBM1047 and IBM1140, ISO-8859-1 (aka Latin1) 
and Windows-1252. UTF-8 will be the best choice in most situations.

There are plenty of sample XML-files available:

- | The planning engine has a lot of its unit tests written as XML files.
  | See the .xml files in the folders under https://github.com/frePPLe/frePPLe/tree/master/test
  
- | The connector with the Odoo ERP system is implemented as a web service that collects all
    ERP in frePPLe's XML format. The frePPLe planning engine connects to this URL, retrieves
    the XML data and parses it in-memory to construct the planning model.
  | While it may be hard to read without known the Odoo API and data model, it may still be
    worth to have a look at `that code`_ and get a flavor of how that looks.

.. _`XML schema`: https://en.wikipedia.org/wiki/XML_schema

.. _`that code`: https://github.com/frePPLe/frePPLe/blob/master/contrib/odoo/addons_v9/controllers/outbound.py

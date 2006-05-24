
This directory contains an Excel add-in for Frepple.
The goal of the add-in is to demonstrate a modeling tool that is as intuitive 
and simple as possible for end users.

* You require Excel 2003 on your machine (since we extensively use the XML
  mapping feature).
  
* To install the add-in, start Excel and navigate to "Tools/Add-Ins".
  Select "Browse" and select the file frepple.xla.
  You should have an extra heading "frepple" in the menu bar.

* To build a model you can start from the sample in the file "frepple.xls".
  To start from an empty sheet, you need to add a XML-mapping. Navigate to 
  "Data/XML/XML Source". At the bottom of the new pane, click on "XML Maps"
  and then "Add". Use the file "frepple_flat.xsd" as the schema definition file.
  Now you should be able to drag and drop elements from the XML map in your 
  worksheets.
  
* The add-in is not complete, it only serves as a demo of the possible usage.
  It'll need to be tailored for every real usage.
  Press Alt-F11 to see all the code of the add-in, and give it a go...
  
* The architecture used in the demo is not the most robust and scalable...
  The XML maps are first exported to a file. 
  Next, this xml-file is transformed into another xml-file for use as input in 
  Frepple. The transform is performed with an XSL processor.
  Finally Frepple reads in the data and exports back the results.

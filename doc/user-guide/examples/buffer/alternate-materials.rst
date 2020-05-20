===================
Alternate materials
===================

In many industries the bill of materials can contain alternate materials: the same product
can be produced using different components. 

FrePPLe provides 2 constructs to model such alternatives:

- A first option is to use different operations, all producing the same item. 
  Each alternate operation operation can use a completely different set of
  materials and resources.
   
- A second option is to model an alternate for a single consumed item. A single operation is
  used and one of its operation-materials can be substituted with another.

`Check this feature on a live example <https://demo.frepple.com/alternate-materials/data/input/operationmaterial/>`_

:download:`Download an Excel spreadsheet with the data for this example<alternate-materials.xlsx>`


The example models shows both modeling constructs:

* | **Alternate operations**
  | The product X can be produced using 2 versions of the bill of materials, modeled as different
    operations. Version 1 uses components A, B and C. Version 2 uses components C, D and E.

  | The `operation table <https://demo.frepple.com/alternate-materials/data/input/operation/>`_ 
    has 2 operations to produce the item X. The fields priority, search mode, effective start date
    and effective end date control which alternate is selected when generating the plan.
  | In this example there is a short period of time where both versions of the bill of materials are effective.
    During this time period the planning algorithm will select the cheapest production mode - which is the second
    bill of material that uses cheaper components.
  
  .. image:: _images/alternate-materials-1.png
     :alt: Operation table
  
  | The generated plan has 
    `manufacturing orders <https://demo.frepple.com/alternate-materials/data/input/manufacturingorder/>`_ 
    on both operations.
  
  .. image:: _images/alternate-materials-3.png
     :alt: Manufacturing orders

* | **Alternate item**
  | The component C can be substituted by component C-alt in both versions of the bill of material.
    Component C-alt is preferred over C, but it has a longer lead time.

  | The 
    `operation material table <https://demo.frepple.com/alternate-materials/data/input/operationmaterial/>`_
    contains records to consume both component C and C-alt. The name field is used to mark that
    these records are alternates of each other. The fields priority, search mode, effective start
    date and effective end date control which of the substitutes is selected when generating the plan.

  .. image:: _images/alternate-materials-2.png
     :alt: Operation material table

  | In the generated plan you'll see that the preferred component C-alt is purchased after its long
    lead time. Until then we need to buy component C to meet our demand.
  | In the `inventory detail report <https://demo.frepple.com/alternate-materials/data/input/operationplanmaterial/>`_ 
    you can review the inventory changes of all items. You can see that manufacturing order 5 for
    operation "Make X version 2" uses item C, while the manufacturing order 6 uses item C-alt. 
  
  .. image:: _images/alternate-materials-4.png
     :alt: Inventory detail for C and C-alt
    
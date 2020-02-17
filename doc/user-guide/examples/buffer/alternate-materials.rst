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


The example models shows both modeling constructs.

The product X can be produced using 2 versions of the bill of materials, modeled as different
operations. Version 1 uses components A, B and C. Version 2 uses components C, D and E.

The component C can be substituted by component C-alt in both versions of the bill of material.
Component C-alt is preferred over C, but it has a longer lead time.

Here are more specifics details on the configuration:

- | The operation table has 2 operations to produce the item X. The fields priority, search mode, 
    effective start date and effective end date control which alternate is selected when generating 
    the plan.
  | In this example there is a short period of time where both versions of the bill of materials are effective.
    During this time period the planning algorithm will select the cheapest production mode - which is the second
    bill of material that uses cheaper components.
  
  .. image:: _images/alternate-materials-1.png
     :height: 385 px
     :width: 1112 px
     :scale: 100 %  
     :alt: Operation table
  
- | The operation material table contains records to consume both component C and C-alt. The
    name field is used to mark that these records are alternates of each other. The fields priority,
    search mode, effective start date and effective end date control which of the substitutes is
    selected when generating the plan.
  | In the example you'll see that the preferred component C-alt is purchased after its long
    lead time. Until then we need to buy component C to meet our demand.

  .. image:: _images/alternate-materials-2.png
     :height: 568 px
     :width: 1113 px
     :scale: 100 %  
     :alt: Operation material table
    
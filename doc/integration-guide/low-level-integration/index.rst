=====================
Low level integration
=====================

Most projects will integrate frePPLe at the application and/or 
database level. FrePPLe's open architecture allows also integration
scenario's where frePPLe is much closer embedded in another enterprise
application.

* Using the :doc:`xml` or :doc:`python` you can directly interact with 
  the core planning algorithm. It allows data integration without passing
  through frePPLe's database, and it allows customization of the planning
  workflows and algorithms. 

* | FrePPLe allows embedding screens in a frame of your web application
    providing a unified user experience. 
  | See :doc:`user-interface`.

.. toctree::
   :maxdepth: 2
   
   xml
   python
   user-interface

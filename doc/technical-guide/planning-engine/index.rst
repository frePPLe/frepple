===============
Planning engine
===============

At the core of frePPLe is its memory-resident planning engine.

It's main features:

* Coded in C++ for optimal performance

* Fast and efficient modelling framework for planning problems in discrete
  manufacturing industries.

* | Extendible architecture using plugin modules.
  | Plugin modules are shared libraries loaded at runtime.

* | Embeds Python as a scripting language.
  | FrePPLe embeds an interpreter for the Python language. All objects in
    the planning engine can be read, created, updated and deleted from Python
    code. All functionality of Python and its extension modules is accessible
    from the planning engine.

* Native support for XML data.

This chapter highlights some topics of interest to developers wishing the
customize or extend the planning engine.

.. toctree::
   :maxdepth: 3

   class-diagram
   planning-algorithm
   cluster-algorithm
   extension-modules
   unit-tests

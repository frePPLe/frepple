==========================
Frequently asked questions
==========================


User interface
--------------

* **How does frePPLe choose the language of the user interface?**

  The frePPLe web server detects the language settings of your browser.
  If any of the supported languages is in the list, the user interface will
  automatically be shown in that language. If none of the supported
  languages is accepted by your browser, English is used by default.

  A user can override the detected language in the preferences screen.

* **I want frePPLe in my own language**

  FrePPLe is ready to plug in translations for additional languages. Follow
  the instructions :doc:`on this page <technical-guide/user-interface/translating-the-user-interface>`
  to create you own translations and submit them to the frePPLe team.

  It’ll take you only a few hours to come up with the translations.


Data integration
----------------

* **How do I load data from my data source into the frePPLe database?**

  The recommended and fastest method to load data is to directly access the
  database tables with the database utility or ETL tool of your choice.
  The database schema of frePPLe is kept simple and transparent for this
  purpose.

  A second choice is to use the frepple_loadxml command to import an XML file.

  Another choice is to use the loaddata command to import data in JSON or
  YAML format.

  A last alternative is to upload CSV-files in the user interface

* **How do I export planning results from the frePPLe database to an external**
  **system?**

  The recommended and most performant method is to directly pull the data
  from the database tables with the database utility or ETL tool of your choice.
  The planning results are stored in tables with the prefix out\_.

  Alternatively, you can use the dumpdata command to export in XML, JSON or
  YAML format.

  Or, you can save the data from the user interface in CSV-format.

* **How can I export my model to share with others?**

  At times it can be handy to export the content of your data to share it
  with others for debugging or analysis. The simplest way to achieve this
  is to export the model as an Excel spreadsheet from the execution screen.

  If the model is big, using a database dump will be faster and more efficient.

* **How can I import a model sent to me?**

  A model exported as a Excel workbook can be imported again from the execution
  screen. You should first erase any existing contents from the database before
  loading the workbook.

Modelling and solver algorithm
------------------------------

* **What is the solver algorithm in frePPLe?**

  The default solver is a heuristic solver. The algorithm orders all demands
  in order of priority and due date, and searches for each demand the best plan.

  The steps for planning a demand are:

  #. The algorithm first starts with a backward search: From the demand due
     date, we compute backward taking into account all lead times.

     Material availability, capacity constraints, post-operation times,
     safety stock levels and alternate supply paths are all considered in
     this backward search.

  #. If the backward search is not feasible with all post-operation times and
     safety stock respected, frePPLe will create a plan in which the
     post-operation times are shrunk and safety stock inventory targets are
     not met.

     In other words these are considered “soft constraints”: we try to respect
     them if possible, but will create a plan that violates these if that is
     required to deliver the customer order on time.

  #. When the backward search finds that the demand can’t be fulfilled at
     the due date at all, frePPLe switches to forward planning mode for that
     demand. The algorithm will try to minize the delay.

     Material availability, capacity constraints, post-operation times, and
     alternate supply paths are all considered in this forward search.

  The algorithm thus automatically switches between a backward and forward
  search. This results in a plan that minimizes late orders with low inventory
  levels.

  You can experiment with this behavior by first creating a demand with a very
  late due date, and observe the plan created by the backward planning mode.
  When the due date is set to tomorrow, the plan will show the forward planning
  mode.

  A more detailed description can be found :doc:`here <technical-guide/planning-engine/planning-algorithm>`.

  FrePPLe also allows external solvers to be implemented as plugins. For
  specific planning problems additional solvers can be developed.

* **Where will the solver do well? Where will it not work well?**

  There is no such thing as a generic algorithm that can solve all planning
  problems optimally and efficiently. Every solving algorithm has its strengths
  and weaknesses.

  The frePPLe default solver is designed with discrete manufacturing
  environments in mind. In these environments material and capacity constraints
  are interacting with each other, and a plan is required that intelligently
  synchronizes the procurement of materials with the available capacity.

  Some examples of planning problems where the frePPLe default solver is likely
  to fall short:

  * | Project planning:
    | If your planning problem has one-of tasks with complex dependencies and
      timing constraints the solver needs to recognize and utilize the critical
      path information. Such logic is currently not implemented.

  * | Human resource planning:
    | If your planning problems looks like a timetable where people need to be
      assigned to a set of tasks subject to a complex set of constraints and
      objectives, you’ll find that specialized solvers are doing a better job
      than frePPLe.

  * | Combinatorial problems:
    | Some planning problems look like puzzles. A combinatorial search is
      required to achieve good plan quality in such environments. The heuristic
      rules used by the default solver will find a feasible solution fast, but
      it can be far from optimal.

* **How can I debug or trace the solver algorithm?**

  The level of detail in the planning file can be controlled with the parameter
  “plan.loglevel”. Setting this variable to “2” will generate a full trace of
  the planning algorithm.

Database
--------

* **What are recommended PostgreSQL database settings?**

  See the Django documentation at https://docs.djangoproject.com/en/dev/ref/databases/#postgresql-notes

  We highly recommend the pgtune tool http://pgtune.leopard.in.ua/ to configure
  the database to your hardware capabilities.

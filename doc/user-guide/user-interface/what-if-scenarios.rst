=================
What-if scenarios
=================

FrePPLe allows users to easily create alternative plans. With the scenario
management you can easily create copies of the complete model.

During the installation a number of what-if *slots* are configured by the
adminstrator. See :doc:`this page </installation-guide/multi-model>` for the
details.

The scenario's can have the following states:

* **Free**:
  The slot is currently unallocated and available for use.

* **In Use**:
  Data has been copied into the scenario slot. Users can freely work
  independently in the scenario, without affecting the main model.

  When scenarios are in use, a drop down list appears in the upper right
  corner. It allows you to select the scenario to work in.

  .. image:: _images/scenario-selection.png
   :alt: Scenario selection

In :doc:`the execution screen <execute>`, you can change the status of a slot:

* | **Copy** is used to duplicate an existing schema into a free slot.
  | After copying the scenario slot moves from *free* to *in use*.

* | **Release** is used to flag that work on the what-if scenario
    slot has finished.
  | After releasing the scenario slot moves from *in use* to *free again*.

Access rights and permissions can be managed for each scenario individually.
After the copying of a scenario only 1) the user executing the command
and 2) superusers in the source scenario are marked active in the new scenario.
Other users can be granted access by marking them active in the new scenario, and
by assigning them appropriate privileges in it.
See :doc: `User permissions and roles </user-guide/user-interface/getting-around/user-permissions-and-roles>`

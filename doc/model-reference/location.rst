========
Location
========

A location is a (physical or logical) place where resources, buffers
and operations are located.

FrePPLe uses locations from reporting purposes, and the ‘available’
calendar is used to model the working hours and holidays of resources,
buffers and operations.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Name of the location.
                               | This is the key field and a required attribute.
description  string            Free format description.
category     string            Free format category.
subcategory  string            Free format subcategory.
available    calendar          Calendar defining the working hours for all operations,
                               resources and buffers in the location.
owner        location          | Locations are organized in a hierarchical tree.
                               | This field defines the parent location.
members      list of location  | Locations are organized in a hierarchical tree.
                               | This field defines a list of child location.
hidden       boolean           Marks entities that are considered hidden and are normally
                               not shown to the end user.
action       A/C/AC/R          | Type of action to be executed:
                               | A: Add an new entity, and report an error if the entity
                                 already exists.
                               | C: Change an existing entity, and report an error if the
                                 entity doesn’t exist yet.
                               | AC: Change an entity or create a new one if it doesn’t
                                 exist yet. This is the default.
                               | R: Remove an entity, and report an error if the entity
                                 doesn’t exist.
============ ================= ===========================================================

**Example XML structures**

Adding or changing a location

.. code-block:: XML

   <plan>
     <locations>
       <location name="site A">
         <category>cat A</category>
         <owner name="Manufacturing sites"/>
       </location>
     </locations>
   </plan>

Alternate format of the previous example

.. code-block:: XML

   <plan>
     <locations>
       <location name="Manufacturing sites">
         <members>
           <location name="site A" category="cat A"/>
         </members>
       </location>
     </locations>
   </plan>

Deleting a location

.. code-block:: XML

   <plan>
     <locations>
       <location name="site A" action="R"/>
     </locations>
   </plan>

**Example Python code**

Adding or changing a location

::

    loc1 = frepple.location(name="Manufacturing sites")
    loc2 = frepple.location(name="site A", category="cat A", owner=loc1)

Deleting a location

::

    frepple.location(name="site A", action="R")

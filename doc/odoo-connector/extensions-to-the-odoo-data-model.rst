=================================
Extensions to the Odoo data model
=================================

Some manufacturing concepts do not exist in standard Odoo. The frepple connector
also adds some new objects and fields to Odoo.

The philosphy of the frepple-odoo connector is to use Odoo as the single source of truth
for all master data.


  1. | **Skills**
     | The concept of skill where a work center can have one or more skill has been
       added into odoo. A skill link is visible in the Master Data menu. This table is equivalent
       to the frePPLe :doc:`../model-reference/skills` table, used to define the available skills.

     .. image:: _images/skill.png
      :alt: Skill view in odoo

  2. | **Work Center Skill**
     | This table is equivalent to the frePPLe :doc:`../model-reference/resource-skills` table.
       This table is used to assign skill(s) to a work center.
     | A *Work Center Skill* link has been added in the Master Data menu.

     .. image:: _images/work_center_skill.png
      :alt: work center skill view in odoo

  3. | **Work centers**
     | New fields *owner* and *constrained* have been added to the work centers.
     | The owner field allows the planner to define a parent work center.
     | The constrained flag specifies whether frepple should plan this workcenter with infinite
       capacity or not.

     .. image:: _images/work_center.png
      :alt: work center in odoo

  4. | **Operations**
     | In the Operations view of Odoo, 4 new fields have been added:
       *Skill*, *Search Mode*, *Priority* and *secondary work center*.
     | Because it is not uncommon that an operation requires more than one work center to run, the connectors
       off the possibility to configure one or more secondary work centers.
     | This table is the equivalent to the frePPLe :doc:`../model-reference/operation-resources` table.

     .. image:: _images/operations.png
      :alt: Operations in odoo

  5. | **Bills of Materials**
     | In the Bills of Materials view of Odoo, new fields have been added:
       *Scrap Rate* and *Quantity Multiple*.
     | The scrap rate field allows the planner to define the expected scrap rate for the manufacturing process.
       A manufacturing order of 10 will consume material quantities to produce 10 pieces but will only
       produce 9 pieces when the scrap rate is set to 10%.
     | The quantity multiple field allows the planner to define a multiple quantity for the manufacturing orders.
       For example, if the quantity multiple is set to 5, manufacturing orders can only have a quantity of 5,10,15...
     | This table is the equivalent to the frePPLe :doc:`../model-reference/operations` table.

     .. image:: _images/boms.png
      :alt: Bills of Materials in odoo

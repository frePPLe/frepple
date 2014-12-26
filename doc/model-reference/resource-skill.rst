==============
Resource skill
==============

A resource skill associates a certain skill with a resource.

The association can be date effective and also has a priority.

**Fields**

=============== ================= ===========================================================
Field           Type              Description
=============== ================= ===========================================================
skill           skill             | Name of the skill.
                                  | This is a key field and a required attribute.
resource        resource          | Name of the resource.
                                  | This is a key field and a required attribute.
effective_start dateTime          Date when the resource gains this skill.
effective_end   dateTime          Date when the resource loses this skill.
priority        integer           | Priority of this resource among all resources having this
                                    skill.
                                  | A lower number indicates that this resource is preferred
                                    when the skill is required. This field is used when the
                                    search policy of the load is PRIORITIY.
action          A/C/AC/R          | Type of action to be executed:
                                  | A: Add an new entity, and report an error if the entity
                                    already exists.
                                  | C: Change an existing entity, and report an error if the
                                    entity doesn’t exist yet.
                                  | AC: Change an entity or create a new one if it doesn’t
                                    exist yet. This is the default.
                                  | R: Remove an entity, and report an error if the entity
                                    doesn’t exist.
=============== ================= ===========================================================

**Example XML structures**

Adding or changing resource skills

.. code-block:: XML

    <plan>
      <skills>
         <skill name="Qualified operator">
           <resourceskills >
             <resourceskill resource name="John" />
             <resourceskill resource name="Paul" />
             <resourceskill resource name="Neil" />
           </resourceskills>
        </skill>
      </skills>
    </plan>

Deleting a resource skill

.. code-block:: XML

    <plan>
       <skills>
         <skill>
            <resourceskills>
               <resourceskill name="Qualified operator" action="R"/>
            </resourceskills>
         <skill>
       </skills>
    </plan>

**Example Python code**

Adding or changing resource skills

::

    skill = frepple.skill(name="Qualified operator")
    resource = frepple.resource(name="John")
    frepple.resourceskill(resource=resource, skill=skill, priority=1)

Deleting a skill

::

    skill = frepple.skill(name="Qualified operator")
    resource = frepple.resource(name="John")
    frepple.resourceskill(resource=resource, skill=skill, action="R")

Iterate over skills and assigned resources

::

    for m in frepple.skills():
      print "Following resources have skill '%s':" % m.name
      for i in m.resourceskills:
        print " ", i.resource.name, i.priority, i.effective_start, i.effective_end

Iterate over resources and assigned skills

::

    for m in frepple.resources():
      print "Resources '%s' has skills:" % m.name
      for i in m.resourceskills:
        print " ", i.skill.name, i.priority, i.effective_start, i.effective_end

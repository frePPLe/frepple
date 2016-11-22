======
Skills
======

A skill defines a certain property that can be assigned to resources.
A resource can have any number of skills.

The operationresource table associates an operation with a resource. In that table we
can define a skill required on the resource.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Unique name of the skill.
                               | This is the key field and a required attribute.
resources    list of resources A read-only list of all resources having this skill.
============ ================= ===========================================================

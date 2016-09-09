=====
Skill
=====

A skill defines a certain property that can be assigned to resources.

Each resource can have any number of skills.

A load models the association of an operation and a resource. A load can
specify a skill required on the resource.

**Fields**

============ ================= ===========================================================
Field        Type              Description
============ ================= ===========================================================
name         non-empty string  | Name of the skill.
                               | This is the key field and a required attribute.
resources    list of resources A read-only list of all resources having this skill.
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

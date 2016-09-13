===============
Resource skills
===============

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
=============== ================= ===========================================================

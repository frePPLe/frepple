=========
Attribute
=========

This table allows users to add custom attribute fields to the frePPLe data models.

The attribute fields are automatically defined in the database. They behave 
exactly like any other field: editing, exporting, importing, sorting, filtering...
are all possible.

================ ================= ===========================================================
Field            Type              Description
================ ================= ===========================================================
name             string            | Unique name of the field.
                                   | Only alfanumeric characters are allowed.

label            string            The string displayed in the user interface. This will be 
                                   translated automatically to the language configured in
                                   your browser.

type             string            | Data type of the attribute.
                                   | Possible values are:

                                   - string
                                   - boolean
                                   - number
                                   - integer
                                   - date
                                   - datetime
                                   - duration
                                   - time
                                   - jsonb
                              
editable         boolean           | Marks whether this field is editable.
                                   | Non-editable read-only fields are typically used to 
                                     store computed attributes or metrics.

initially_hidden boolean           | When set to false (default) the attribute is shown by
                                     default.
                                   | When set to true users will only need to explicitly
                                     customize the report to see the attribute.
================ ================= ===========================================================

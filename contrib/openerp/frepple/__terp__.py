# -*- encoding: utf-8 -*-

{
    "name" : "Advanced Planning and Scheduling Module",
    "version" : "1.0",
    "author" : "frePPLe",
    "website" : "http://www.frepple.com",
    "category" : "Generic Modules/Production",
    "depends" : ["mrp"],
    "description": """
    This module performs constrained planning scheduling with frePPLe.
    """,
    "init_xml": [],
    "update_xml": [
      'frepple_data.xml',
      'frepple_view.xml',
      'ir.model.access.csv',
      ],
    "demo_xml": [],
    "installable": True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

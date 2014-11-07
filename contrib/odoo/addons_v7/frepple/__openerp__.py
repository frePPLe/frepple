# -*- coding: utf-8 -*-
{
    'name': 'frePPLe connector',
    'version': '0.2.9',
    'category': 'Manufacturing',
    'summary': 'Advanced planning and scheduling',
    'author': 'frePPLe',
    'website': 'http://frepple.com',
    'description': '''
Connector to frePPLe
====================
Finite capacity planning and scheduling
=======================================

FrePPLe is an open source production planning and scheduling application.
It generates material and capacity feasible plans.

This module allows an odoo instance to send data to frePPLe and receive back
planning results.

With this module frePPLe can be used to replace the MRP scheduler from odoo.
Alternatively, the production planner can use frePPLe in parallel to take
material and capacity planning decisions.
    ''',
    'images': [
       'images/configure.png',
       'images/cron_scheduler.png',
       'images/manual_action.png'
       ],
    'depends': [
      'procurement',
      'product',
      'purchase',
      'sale',
      'resource',
      'mrp'
      ],
    'data': [
      'frepple_data.xml',
      ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}

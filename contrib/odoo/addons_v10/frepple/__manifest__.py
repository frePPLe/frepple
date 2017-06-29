# -*- coding: utf-8 -*-
{
    'name': 'frepple',
    'version': '4.0.0',
    'category': 'Manufacturing',
    'summary': 'Advanced planning and scheduling',
    'author': 'frePPLe',
    'website': 'https://frepple.com',
    'license': 'AGPL-3',
    'description': 'Connector to frePPLe - finite capacity planning and scheduling',
    'depends': [
      'procurement',
      'product',
      'purchase',
      'sale',
      'resource',
      'mrp'
      ],
    'external_dependencies': {'python': ['jwt']},
    'data': [
      'frepple_data.xml',
      ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': True,
}

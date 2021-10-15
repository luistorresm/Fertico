# -*- coding: utf-8 -*-
{
    'name': "Límite de crédito",

    'summary': """
        Modulo para control de límite crédito""",

    'description': """
        Límites de crédito
    """,

    'author': "Wobin",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base',
    'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',

        'views/views.xml',
        'views/templates.xml',
        'views/credit_limit.xml',
        'views/sale_order_view.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

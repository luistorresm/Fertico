# -*- coding: utf-8 -*-
{
    'name': "Fertico addons 14",

    'summary': """
        Addons para base de datos version 14""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Wobin",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'base', 'account', 'purchase','point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',

        'views/views.xml',
        'views/templates.xml',
        'views/migration.xml',
        'views/pos_init.xml',
        'views/attendances.xml',
        'views/price_list.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

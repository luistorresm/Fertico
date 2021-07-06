# -*- coding: utf-8 -*-
{
    'name': "Wobin créditos",

    'summary': """
        Aplicación para administración de procesos de créditos""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Wobin",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web'],

    # always loaded
    'data': [
        #data
        'data/credit_data.xml',

        #security
        'security/ir.model.access.csv',
        'security/credit_security.xml',
        
        #'views/views.xml',
        #'views/templates.xml',
        'views/menus.xml',
        'views/reports.xml',
        'views/params.xml',
        'views/pre_application.xml',
        'views/record.xml',
        'views/credit_limit.xml',
        'views/tracking_limit.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
# -*- coding: utf-8 -*-
{
    'name': "Albagro Reciba",

    'summary': """Módulo para agregar una serie de personalizaciones para Reciba de Alabagro""",

    'description': """Módulo para gestionar las personalizaciones relativas a nuevos modelos, vistas, validaciones para el proceso de Reciba""",

    'author': "Wobin Simple Cloud",
    'website': "https://fertico.odoo.com/web",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '11.0.1.0.3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/saldos_pendientes_grupo.xml',      

        'views/views.xml',
        'views/templates.xml',
        'views/reciba.xml',
        'views/cycle.xml',
        'views/purchase.xml',
        'views/modality.xml',
        'views/saldos_pendientes.xml',      
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
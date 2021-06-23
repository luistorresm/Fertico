# -*- coding: utf-8 -*-
# from odoo import http


# class FerticoAddons(http.Controller):
#     @http.route('/fertico_addons/fertico_addons/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fertico_addons/fertico_addons/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fertico_addons.listing', {
#             'root': '/fertico_addons/fertico_addons',
#             'objects': http.request.env['fertico_addons.fertico_addons'].search([]),
#         })

#     @http.route('/fertico_addons/fertico_addons/objects/<model("fertico_addons.fertico_addons"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fertico_addons.object', {
#             'object': obj
#         })

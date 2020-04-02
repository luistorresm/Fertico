# -*- coding: utf-8 -*-
from odoo import http

# class Fertico-addons(http.Controller):
#     @http.route('/fertico-addons/fertico-addons/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fertico-addons/fertico-addons/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fertico-addons.listing', {
#             'root': '/fertico-addons/fertico-addons',
#             'objects': http.request.env['fertico-addons.fertico-addons'].search([]),
#         })

#     @http.route('/fertico-addons/fertico-addons/objects/<model("fertico-addons.fertico-addons"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fertico-addons.object', {
#             'object': obj
#         })
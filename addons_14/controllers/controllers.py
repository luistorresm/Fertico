# -*- coding: utf-8 -*-
# from odoo import http


# class Addons14(http.Controller):
#     @http.route('/addons_14/addons_14/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addons_14/addons_14/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('addons_14.listing', {
#             'root': '/addons_14/addons_14',
#             'objects': http.request.env['addons_14.addons_14'].search([]),
#         })

#     @http.route('/addons_14/addons_14/objects/<model("addons_14.addons_14"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addons_14.object', {
#             'object': obj
#         })

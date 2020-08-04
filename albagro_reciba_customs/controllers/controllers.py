# -*- coding: utf-8 -*-
from odoo import http

# class AlbagroRecibaCustoms(http.Controller):
#     @http.route('/albagro_reciba_customs/albagro_reciba_customs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/albagro_reciba_customs/albagro_reciba_customs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('albagro_reciba_customs.listing', {
#             'root': '/albagro_reciba_customs/albagro_reciba_customs',
#             'objects': http.request.env['albagro_reciba_customs.albagro_reciba_customs'].search([]),
#         })

#     @http.route('/albagro_reciba_customs/albagro_reciba_customs/objects/<model("albagro_reciba_customs.albagro_reciba_customs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('albagro_reciba_customs.object', {
#             'object': obj
#         })
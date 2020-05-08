# -*- coding: utf-8 -*-
from odoo import http

# class Block-credit(http.Controller):
#     @http.route('/block-credit/block-credit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/block-credit/block-credit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('block-credit.listing', {
#             'root': '/block-credit/block-credit',
#             'objects': http.request.env['block-credit.block-credit'].search([]),
#         })

#     @http.route('/block-credit/block-credit/objects/<model("block-credit.block-credit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('block-credit.object', {
#             'object': obj
#         })
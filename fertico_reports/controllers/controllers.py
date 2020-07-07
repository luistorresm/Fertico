# -*- coding: utf-8 -*-
from odoo import http

# class FerticoReports(http.Controller):
#     @http.route('/fertico_reports/fertico_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fertico_reports/fertico_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fertico_reports.listing', {
#             'root': '/fertico_reports/fertico_reports',
#             'objects': http.request.env['fertico_reports.fertico_reports'].search([]),
#         })

#     @http.route('/fertico_reports/fertico_reports/objects/<model("fertico_reports.fertico_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fertico_reports.object', {
#             'object': obj
#         })
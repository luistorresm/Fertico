# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

#//////////////////////////////////////////////////////////////////////////////////////////////#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     START
# 
# This ticket intends to help final users to clasify and to add new grouping tools in order
# to improve their analysis experience,
#//////////////////////////////////////////////////////////////////////////////////////////////#
class AccountAnalyticTag(models.Model):
    _inherit = "account.analytic.tag"

    analytic_tag_type = fields.Selection([('trip', 'Trip'),
                                          ('route', 'Route'),
                                          ('operator', 'Operator')],
                                         'Analytic Tag Type', default="trip")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tag_trip = fields.Char('Trip', compute="_compute_trip")    
    tag_route = fields.Char('Route', compute="_compute_route")    
    tag_operator = fields.Char('Operator', compute="_compute_operator")   

    @api.depends('analytic_tag_ids')
    def _compute_trip(self):
        for rec in self:
            if rec.analytic_tag_ids:
                tags = rec.analytic_tag_ids.ids.split(",")

                for vals in tags:
                    tag = self.env['account.analytic.tag'].browse(vals)

                    if tag.mapped('analytic_tag_type') == 'trip':
                        rec.tag_trip = vals


    @api.depends('analytic_tag_ids')
    def _compute_route(self):
        for rec in self:
            if rec.analytic_tag_ids:
                tags = rec.analytic_tag_ids.ids.split(",")

                for vals in tags:
                    tag = self.env['account.analytic.tag'].browse(vals)

                    if tag.mapped('analytic_tag_type') == 'route':
                        rec.tag_route = vals                        


    @api.depends('analytic_tag_ids')
    def _compute_operator(self):
        for rec in self:
            if rec.analytic_tag_ids:
                tags = rec.analytic_tag_ids.ids.split(",")

                for vals in tags:
                    tag = self.env['account.analytic.tag'].browse(vals)

                    if tag.mapped('analytic_tag_type') == 'operator':
                        rec.tag_operator = vals                
#//////////////////////////////////////////////////////////////////////////////////////////////#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#//////////////////////////////////////////////////////////////////////////////////////////////#
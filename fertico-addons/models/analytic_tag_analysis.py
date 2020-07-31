# -*- coding: utf-8 -*-
from odoo import api, fields, models

#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     START
# 
# This ticket intends to help final users to clasify and to add new grouping tools in order
# to improve their analysis experience,
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
class AccountAnalyticTag(models.Model):
    _inherit = "account.analytic.tag"

    #:::::::::::::::::::::::::::::::::::::::::::::
    #   MODEL FIELDS
    #:::::::::::::::::::::::::::::::::::::::::::::       
    analytic_tag_type = fields.Selection([('trip', 'Trip'),
                                          ('route', 'Route'),
                                          ('operator', 'Operator')],
                                         'Analytic Tag Type')



class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    #:::::::::::::::::::::::::::::::::::::::::::::
    #   MODEL FIELDS
    #:::::::::::::::::::::::::::::::::::::::::::::
    trip     = fields.Many2one('account.analytic.tag', compute=get_trip, string='Trip', store=True)
    route    = fields.Many2one('account.analytic.tag', compute=get_route, string='Route', store=True)
    operator = fields.Many2one('account.analytic.tag', compute=get_operator, string='Operator', store=True)    


    #:::::::::::::::::::::::::::::::::::::::::::::
    #   MODEL METHODS
    #:::::::::::::::::::::::::::::::::::::::::::::
    @api.depends('tag_ids')
    def get_trip(self):
        """This method intends to distribute and assign trips in analytic tags in
           their corresponding columns in account move lines"""        
        for line in self:
            for tag in line.tag_ids:
                if tag.tag_type == 'trip':
                    line.travel=tag.id


    @api.depends('tag_ids')
    def get_route(self):
        """This method intends to distribute and assign routes in analytic tags in
           their corresponding columns in account move lines"""        
        for line in self:
            for tag in line.tag_ids:
                if tag.tag_type == 'route':
                    line.route=tag.id


    @api.depends('tag_ids')
    def get_operator(self):
        """This method intends to distribute and assign operators in analytic tags in
           their corresponding columns in account move lines"""        
        for line in self:
            for tag in line.tag_ids:
                if tag.tag_type == 'operator':
                    line.operator=tag.id          
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
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

    #////////////////////////////////////////////////////////////////////////
    #   MODEL FIELDS
    #////////////////////////////////////////////////////////////////////////    
    analytic_tag_type = fields.Selection([('trip', 'Trip'),
                                          ('route', 'Route'),
                                          ('operator', 'Operator')],
                                         'Analytic Tag Type', default="trip")

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #////////////////////////////////////////////////////////////////////////
    #   MODEL FIELDS
    #////////////////////////////////////////////////////////////////////////
    tag_trip = fields.Char('Trip', compute="_compute_trip")    
    tag_route = fields.Char('Route', compute="_compute_route")    
    tag_operator = fields.Char('Operator', compute="_compute_operator")   


    #////////////////////////////////////////////////////////////////////////
    #   MODEL METHODS
    #////////////////////////////////////////////////////////////////////////
    @api.depends('analytic_tag_ids')
    def _compute_trip(self):
        for rec in self:
            #Obtain multiples IDs:
            if rec.analytic_tag_ids:
                tags_ids = rec.analytic_tag_ids.ids

                #Get recordset from model of analytic tags:
                for tag_id in tags_ids:
                    tag = self.env['account.analytic.tag'].browse(tag_id)

                    #Assign value into column of trips
                    if tag.analytic_tag_type == 'trip':
                        rec.tag_trip = tag.name


    @api.depends('analytic_tag_ids')
    def _compute_route(self):
        for rec in self:
            #Obtain multiples IDs:
            if rec.analytic_tag_ids:
                tags_ids = rec.analytic_tag_ids.ids

                #Get recordset from model of analytic tags:
                for tag_id in tags_ids:
                    tag = self.env['account.analytic.tag'].browse(tag_id)

                    #Assign value into column of route
                    if tag.analytic_tag_type == 'route':
                        rec.tag_route = tag.name                        


    @api.depends('analytic_tag_ids')
    def _compute_operator(self):
        for rec in self:
            #Obtain multiples IDs:
            if rec.analytic_tag_ids:
                tags_ids = rec.analytic_tag_ids.ids

                #Get recordset from model of analytic tags:
                for tag_id in tags_ids:
                    tag = self.env['account.analytic.tag'].browse(tag_id)

                    #Assign value into column of operator
                    if tag.analytic_tag_type == 'operator':
                        rec.tag_operator = tag.operator              
#//////////////////////////////////////////////////////////////////////////////////////////////#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#//////////////////////////////////////////////////////////////////////////////////////////////#
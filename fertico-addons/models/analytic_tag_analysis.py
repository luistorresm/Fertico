# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

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

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    #:::::::::::::::::::::::::::::::::::::::::::::
    #   MODEL FIELDS
    #:::::::::::::::::::::::::::::::::::::::::::::
    tag_trip = fields.Char('Trip', store=True, compute="_compute_trip")    
    tag_route = fields.Char('Route', store=True, compute="_compute_route")    
    tag_operator = fields.Char('Operator', store=True, compute="_compute_operator")   


    #:::::::::::::::::::::::::::::::::::::::::::::
    #   MODEL METHODS
    #:::::::::::::::::::::::::::::::::::::::::::::
    @api.depends('analytic_tag_ids')
    def _compute_trip(self):
        """This method intends to distribute and assign trips in analytic tags in
           their corresponding columns in account move lines"""
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
        """This method intends to distribute and assign routes in analytic tags in
           their corresponding columns in account move lines"""        
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
        """This method intends to distribute and assign operators in analytic tags in
           their corresponding columns in account move lines"""        
        for rec in self:
            #Obtain multiples IDs:
            if rec.analytic_tag_ids:
                tags_ids = rec.analytic_tag_ids.ids

                #Get recordset from model of analytic tags:
                for tag_id in tags_ids:
                    tag = self.env['account.analytic.tag'].browse(tag_id)

                    #Assign value into column of operator
                    if tag.analytic_tag_type == 'operator':
                        rec.tag_operator = tag.name             
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\#
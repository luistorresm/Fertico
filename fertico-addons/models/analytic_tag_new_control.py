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

    tag_trip = fields.Char('Trip')    
    tag_route = fields.Char('Route')    
    tag_operator = fields.Char('Operator')            
#//////////////////////////////////////////////////////////////////////////////////////////////#
#   TICKET 102    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#//////////////////////////////////////////////////////////////////////////////////////////////#
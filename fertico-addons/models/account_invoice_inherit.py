# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _  

import logging
_logger = logging.getLogger(__name__)      

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 002 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     START
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    #:::::::::::::::::::::::
    # MODEL FIELDS
    #:::::::::::::::::::::::
    payment_date = fields.Char("Payment Date", store=True, compute="compute_payment_date")


    #:::::::::::::::::::::::
    # MODEL METHODS
    #::::::::::::::::::::::: 
    @api.depends('number')
    def compute_payment_date(self):
        for rec in self:
            _logger.info('\n\n\n ID: %s\n\n\n', rec.id)
            _logger.info('\n\n\n payments_widget: %s\n\n\n', rec.payments_widget)
            rec.payment_date = "1.0"
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 002 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#             

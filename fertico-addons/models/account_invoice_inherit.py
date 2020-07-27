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
    payment_date = fields.Char("Payment Date", compute="compute_payment_date")


    #:::::::::::::::::::::::
    # MODEL METHODS
    #::::::::::::::::::::::: 
    @api.multi
    def compute_payment_date(self):
        for rec in self:
            _logger.info('\n\n\n ID: %s\n\n\n', rec.id)

            acc_mv_ln_id = self.env['account.move.line'].search([('invoice_id', '=', rec.id)]) 
            _logger.info('\n\n\n acc_mv_ln_id: %s\n\n\n', acc_mv_ln_id.ids )

            for v in acc_mv_ln_id.ids:
                acc_par_rec_id = self.env['account.partial.reconcile'].search([('debit_move_id', '=', v)])                
                _logger.info('\n\n\n acc_par_rec_id: %s\n\n\n', acc_par_rec_id.id)              
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 002 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#             

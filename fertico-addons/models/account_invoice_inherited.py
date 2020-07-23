# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _  
import logging
_logger = logging.getLogger(__name__)      

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 002 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     START
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    #:::::::::::::::::::::::
    # MODEL FIELDS
    #:::::::::::::::::::::::
    supplier_bill_date = fields.Char("Supplier Bill Date", store=True, compute="_compute_sup_bll_dte")


    #:::::::::::::::::::::::
    # MODEL METHODS
    #::::::::::::::::::::::: 
    @api.multi
    def _compute_sup_bll_dte(self):
        for v in self:
            if v.payments_widget:
                _logger.info('\n\n\n v.payments_widget: %s\n\n\n', v.payments_widget)
        
         
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 002 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#             

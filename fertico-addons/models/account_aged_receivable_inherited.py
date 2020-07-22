# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api
from odoo.tools.translate import _  

#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 011 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     START
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
class report_account_aged_receivable(models.AbstractModel):
    _inherit = "account.aged.receivable"

    def get_columns_name(self, options):    
        """This method intends add a new column of Invoice Dates into Account Aged Receivable Report"""
        #Obtain columns of original header:
        columns = super().get_columns_name(options)
        #Inserting new column of Invoice Date:
        columns.insert(1, {'name': _('Release Invoice Date'), 'class': 'number', 'style': 'white-space:nowrap;'})
        return columns
    
    @api.model
    def get_lines(self, options, line_id=None):
        """This method intends add a new values of Invoice Dates into Account Aged Receivable Report"""
        #Obtain original list of rows of the report:
        lines = super().get_lines(options, line_id)
        for line in lines:
            #Inject an empty value into the new added column:
            if line.get('level') == 2:
                line.get('columns').insert(0, {'name': ''}) 
            #Only the rows with level 4 correspond to broken down concepts:                
            elif line.get('level') == 4:     
                #Retrieve id of account move, after obtain invoice and its date:
                move_id = self.env['account.move.line'].browse(line['id']).move_id
                invoice_id = self.env['account.invoice'].search([('move_id', '=', move_id.id)])
                #Inserting new value for column of Release Invoice Date:
                if invoice_id.date_invoice:
                    cr_date = invoice_id.date_invoice
                    cr_date = datetime.strptime(cr_date, '%Y-%m-%d').strftime("%d/%m/%Y")                                    
                    line['columns'].insert(0, {'name': cr_date})
                else:
                    line['columns'].insert(0, {'name': ""})
            #Inject an empty value into the new added column for Total row:        
            else:                
                line.get('columns').insert(0, {'name': ''})                     
        return lines
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#
#   TICKET 011 ALBAGRO    DEVELOPED BY SEBASTIAN MENDEZ    --     END
#\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\#             

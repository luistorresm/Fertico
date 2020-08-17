from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _

class RecibaOrder(models.Model):
    _name = 'reciba.order'
    _description = 'Reciba'

    @api.one
    @api.depends('gross_weight', 'tare_weight')
    def _get_net(self):
        self.net_weight=self.gross_weight-self.tare_weight


    product_id    = fields.Many2one('product.product', string="Product")
    no_ticket     = fields.Char(string="No. ticket", required=True)
    gross_weight  = fields.Float(string="Gross weight")
    tare_weight   = fields.Float(string="Tare weight")
    net_weight    = fields.Float(string="Net weight", compute="_get_net", store=True)
    cycle_id      = fields.Many2one('reciba.cycle', string="Cycle")
    customer_id   = fields.Many2one('res.partner', string="Productor name")
    modality_id   = fields.Many2one('reciba.modality', string="Modality")
    has_debts     = fields.Boolean(string='Does it have debts this client?', default=False)
    error_message = fields.Text(compute='display_debts_pop_up')

    def name_get(self):
        res=[]
        for reciba in self:
            res.append((reciba.id,reciba.no_ticket))
        return res


    def display_debts_pop_up(self):
        #Retrieve rows from "account.invoice" model where the present provider
        #is revised to detect if has open invoices indicating that must pay its debts:         
        msg = ""
        sql_query = """SELECT company_id, SUM(residual_signed) 
                         FROM account_invoice 
                        WHERE (partner_id = %s)
                          AND (state = 'open')
                          AND (type = 'in_invoice' OR type = 'in_refund') 
                        GROUP BY company_id;"""
                        
        self.env.cr.execute(sql_query, (self.customer_id.id,))
        residual_companies = self.env.cr.fetchall()        

        #Validate if query has results:
        if residual_companies:           
            #Construct the error message, beginning with client with open sales invoices:
            debtor = self.env['res.partner'].search([('id', '=', self.partner_id.id)]).name
            msg = _('The related contact on the purchase order %s has outstanding balances on sales: \n') % (debtor)
                          
            for val in residual_companies:
                #Iterate companies with residual (outstanding balance) and concatenate
                company_name = self.env['res.company'].search([('id', '=', val[0])]).name
                msg += _('\n[+] %s balance by $%s') % (company_name, val[1])                    
                #Sum up residuals in order to indicate how much is debted
                summatory_residual += val[1] 
                         
            #Concatenate last part of error message:
            msg += _('\n\nConsider making discounts for settlement.')
            self.has_debts = True
            self.error_message = msg
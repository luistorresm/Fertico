from odoo import models, fields, api

class AccountPartialReconcile(models.Model):
    _inherit='account.partial.reconcile'
    #==========================================Reporte account reconcile======================================
    
    #====Metodo para campos calculados, busca los registros anteriores de la factura del registro actual======
    #====Los suma para para saber el total pagado antes de ese abono y suma el abono actual para tener =======
    #====el saldo final hasta ese momento=====================================================================
    @api.multi
    @api.depends('amount')
    def get_paid(self):
        #obtenemos los datos de facturas de acuerdo al tipo
        for partial in self:
            if partial.credit_move.invoice_id:
                #facturas de compras
                invoice=partial.credit_move.invoice_id
                data = self.env['account.partial.reconcile'].search(['&',('credit_move.invoice_id', '=', invoice.id),('id', '<', partial.id)])
                paid_total=0
                for d in data:
                    paid_total+=d.amount
                partial.incial=partial.total_purchase-paid_total
                partial.final=partial.total_purchase-(paid_total+partial.amount)
            else:
                #facturas de ventas
                invoice=partial.debit_move.invoice_id
                data = self.env['account.partial.reconcile'].search(['&',('debit_move.invoice_id', '=', invoice.id),('id', '<', partial.id)])
                paid_total=0
                for d in data:
                    paid_total+=d.amount
                partial.incial=partial.total-paid_total
                partial.final=partial.total-(paid_total+partial.amount)
                

    #Campos calculados
    incial = fields.Float(string="Saldo inicial", compute='get_paid')
    final = fields.Float(string="Saldo final", compute='get_paid')
    
    #Campos relacionados de ventas
    total = fields.Monetary(related='debit_move_id.invoice_id.amount_total')
    
    debit_move = fields.Many2one(related='debit_move_id', store=True)
    customer = fields.Many2one(string="Customer", related='debit_move_id.invoice_id.partner_id', store=True)
    account = fields.Many2one(string="Account", related='debit_move_id.invoice_id.account_id')
    account_type = fields.Selection(related='debit_move_id.invoice_id.account_id.user_type_id.type')

    #Campos relacionados de compras
    total_purchase = fields.Monetary(related='credit_move_id.invoice_id.amount_total')
    
    credit_move = fields.Many2one(related='credit_move_id', store=True)
    customer_purchase = fields.Many2one(string="Vendor", related='credit_move_id.invoice_id.partner_id', store=True)
    account_purchase = fields.Many2one(string="Account", related='credit_move_id.invoice_id.account_id')
    account_type_purchase = fields.Selection(related='credit_move_id.invoice_id.account_id.user_type_id.type')    
    
    invoice = fields.Char()
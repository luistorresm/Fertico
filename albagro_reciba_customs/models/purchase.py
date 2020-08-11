from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cycle_id = fields.Many2one('reciba.cycle', string="Cycle")
    modality_id = fields.Many2one('reciba.modality', string="Modality")

    @api.multi
    @api.onchange('order_line')
    def _onchange_reciba_line(self):
        
        partner=self.partner_id.id
        cycle=self.cycle_id.id
        modality=self.modality_id.id
        

        for line in self.order_line:
            if partner == False:
                if line.reciba_id.customer_id:
                    self.partner_id = line.reciba_id.customer_id
            if cycle == False:
                if line.reciba_id.cycle_id:
                    self.cycle_id = line.reciba_id.cycle_id
            if modality == False:
                if line.reciba_id.modality_id:
                    self.modality_id = line.reciba_id.modality_id
    
    @api.multi
    @api.onchange('order_line')
    def _onchange_reciba_line_ticket(self):

        for line in self.order_line:
            n=0
            duplicate=[]
            for l in self.order_line:
                if line.reciba_id.id == l.reciba_id.id:
                    n+=1
                    if n > 1:
                        duplicate.append(l.id)
            for d in duplicate:
                self.order_line = [(3, d)]
                res = {'warning': {
                    'title': 'Advertencia',
                    'message': 'La boleta seleccionada ya está siendo utilizada'
                }}
                return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    reciba_id = fields.Many2one('reciba.order', string="Ticket")
    cycle = fields.Many2one(related='reciba_id.cycle_id', string="Cycle", store=True)
    invoice_status = fields.Selection(related='invoice_lines.invoice_id.state', string="Invoiced status", store=True)
    qty_invoice = fields.Float(related='invoice_lines.quantity', string="Invoiced quantity", store=True) 
    ticket = fields.Boolean(compute="get_reciba")

    @api.multi
    @api.onchange('reciba_id')
    def _onchange_reciba(self):
        if self.reciba_id:
            reciba = self.env['purchase.order.line'].search([('reciba_id','=',self.reciba_id.id)])
            if reciba:
                self.reciba_id=0
                res = {'warning': {
                    'title': 'Advertencia',
                    'message': 'La boleta seleccionada ya ha sido utilizada anteriormente'
                }}
                return res
            else:
                self.product_id = self.reciba_id.product_id


    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        product = super(PurchaseOrderLine, self).onchange_product_id()
        self.product_qty=self.reciba_id.net_weight


    #===============Evaluamos si se tiene un ticket agregado y guardamos el resultado en un campo boolean=============
    @api.multi
    @api.depends('reciba_id','product_id')
    def get_reciba(self):
        if self.reciba_id:
            self.ticket = True
        else:
            self.ticket = False
    
    
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cycle_id = fields.Many2one('reciba.cycle', string="Cycle")
    modality_id = fields.Many2one('reciba.modality', string="Modality")

    @api.multi
    @api.onchange('invoice_line_ids')
    def _onchange_reciba_line(self):
        
        cycle=self.cycle_id.id
        modality=self.modality_id.id

        for line in self.invoice_line_ids:
            if cycle == False:
                if line.reciba_id.cycle_id:
                    self.cycle_id = line.reciba_id.cycle_id
            if modality == False:
                if line.reciba_id.modality_id:
                    self.modality_id = line.reciba_id.modality_id


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    reciba_id = fields.Many2one(related='purchase_line_id.reciba_id', string="Ticket")
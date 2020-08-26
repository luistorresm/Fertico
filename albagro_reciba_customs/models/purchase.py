from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    cycle_id = fields.Many2one('reciba.cycle', string="Cycle")
    modality_id = fields.Many2one('reciba.modality', string="Modality")

    #==============Revisamos si hay cambios en las lineas de compras========================================
    @api.multi
    @api.onchange('order_line')
    def _onchange_reciba_line(self):
        
        partner=self.partner_id.id
        cycle=self.cycle_id.id
        modality=self.modality_id.id
        
        #Si se agrega una reciba, toma el vendedor, ciclo y modalidad y se los asigna a la ordern de compra
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
    
    #=====================Revisamos si hay cambios en lineas de compra==============
    @api.multi
    @api.onchange('order_line')
    def _onchange_reciba_line_ticket(self):

        for line in self.order_line:
            n=0
            duplicate=[]
            #===Revisamos si hay alguna boleta repetida y de ser así mostramos una advertencia y quitamos la linea===
            for l in self.order_line:
                if line.reciba_id:
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
    discount = fields.Float(string="Discount of quantity")
    humidity = fields.Float(string="Humidity %")

    #=======Revisamos si la reciba seleccionada ya ha sido usada y mostramos una advertencia=====
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

    #=========Asignamos la cantidad que tiene la reciba a la cantidad de la linea de compra========
    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        product = super(PurchaseOrderLine, self).onchange_product_id()
        self.product_qty=self.reciba_id.free_qty
        self.discount = self.reciba_id.discount_applied
        self.humidity = self.reciba_id.percentage_humidity.percentage
        

    
    @api.multi
    @api.onchange('product_qty')
    def get_qty(self):
        if self.reciba_id:
            self.product_qty = self.reciba_id.free_qty
    
    
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

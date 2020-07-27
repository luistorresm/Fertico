from odoo import fields, models, api

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    #==========================metodo para calcular la diferencia===================================
    @api.one
    @api.depends('product_qty', 'qty_received')
    def _get_difference(self):
        self.difference = self.product_qty - self.qty_received


    #=================Desactivamos la suma del campo al agrupar las lista============================
    price_unit = fields.Float(group_operator=False)
    #=================Creamos un campo calculado para obtener la diferencia entre pedido y recibido==
    difference = fields.Float(compute="_get_difference", store=True)
    

class DifferenceWizard(models.TransientModel):
    _name = "difference.wizard"
    #=======================modelo de wizard donde se calcular la diferencia==========================

    @api.multi
    def calculate_difference(self):
        lines = self.env['purchase.order.line'].browse(self._context.get('active_ids'))
        for line in lines:
            line.difference = line.product_qty - line.qty_received
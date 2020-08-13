from odoo import models, fields, api

class RecibaOrder(models.Model):
    _name = 'reciba.order'
    _description = 'Reciba'

    @api.one
    @api.depends('gross_weight', 'tare_weight')
    def _get_net(self):
        self.net_weight=self.gross_weight-self.tare_weight


    product_id = fields.Many2one('product.product', string="Product")
    no_ticket = fields.Char(string="No. ticket", required=True)
    gross_weight = fields.Float(string="Gross weight")
    tare_weight = fields.Float(string="Tare weight")
    net_weight = fields.Float(string="Net weight", compute="_get_net", store=True)
    cycle_id = fields.Many2one('reciba.cycle', string="Cycle")
    customer_id = fields.Many2one('res.partner', string="Productor name")
    modality_id = fields.Many2one('reciba.modality', string="Modality")



    def name_get(self):
        res=[]
        for reciba in self:
            res.append((reciba.id,reciba.no_ticket))
        return res



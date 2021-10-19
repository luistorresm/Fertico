
from odoo import _, api, fields, models

class Account_move(models.Model):
    _inherit = "account.move"


    id_recepcion = fields.Char(
        string='Número de recepción.',
    )

    # no_sociedad = fields.Char(
    #     string='Numero de sociedad',
    # )

    sale_client_order_ref = fields.Char(
        string='Numero de Remisión',
        compute='_compute_sale_order',
        copy=False,
        index=True,
        readonly=True,
        store=True,
        tracking=True,
    )

    supplier_number = fields.Char(
        string='Numero de Proveedor',
        related="partner_id.supplier_number"
    )

    @api.depends('invoice_origin')
    def _compute_sale_order(self):
        for rec in self:
            if rec.invoice_origin:
                picking = self.env['stock.picking'].search([('origin', '=', rec.invoice_origin)],limit=1)
                if picking.origin != False:
                    rec.sale_client_order_ref = picking.name
                else:
                       rec.sale_client_order_ref = False
            else:
                rec.sale_client_order_ref = False


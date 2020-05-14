from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    enable_price=fields.Boolean(String="Enable price change", default=False)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    block_price_line=fields.Boolean(default=False)

    @api.onchange('product_id')
    def _onchange_sale_product(self):
        product = self.env['product.template'].search([('name','=',self.product_id.name)])
        if product:
            self.block_price_line=product.enable_price

class SaleOrderLine(models.Model):
    _inherit = 'account.invoice.line'

    block_price_line=fields.Boolean(default=False)

    @api.onchange('product_id')
    def _onchange_invoice_product(self):
        product = self.env['product.template'].search([('name','=',self.product_id.name)])
        if product:
            self.block_price_line=product.enable_price
        

    
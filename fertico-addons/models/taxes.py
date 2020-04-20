from odoo import fields, models, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.onchange('order_line', 'partner_id')
    def _onchange_order(self, context=None):
        sr_tag=False
        for sale in self:
            for tag in sale.partner_id.category_id:
                if tag.name == 'Sin Retencion':
                    sr_tag=True

            if sr_tag == True:
                for ol in sale.order_line:
                    tax_array=[]
                    for index,tax in enumerate(ol.tax_id):
                        if tax.amount < 0:
                            ol.tax_id=[(2,tax.id)]

    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner(self, context=None):
        sr_tag=False
        for sale in self:
            for tag in sale.partner_id.category_id:
                if tag.name == 'Sin Retencion':
                    sr_tag=True

            if sr_tag == False:
                for ol in sale.order_line:
                    product_taxes = self.env['product.product'].search([('id','=',ol.product_id.id)])
                    ol.tax_id=product_taxes.taxes_id

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.onchange('invoice_line_ids', 'partner_id')
    def _onchange_order(self, context=None):

        sr_tag=False
        for sale in self:
            if sale.type=='out_invoice':
                for tag in sale.partner_id.category_id:
                    if tag.name == 'Sin Retencion':
                        sr_tag=True

                if sr_tag == True:
                    for ol in sale.invoice_line_ids:
                        tax_array=[]
                        for index,tax in enumerate(ol.invoice_line_tax_ids):
                            if tax.amount < 0:
                                ol.invoice_line_tax_ids=[(2,tax.id)]

    @api.multi
    @api.onchange('partner_id')
    def _onchange_partner(self, context=None):
        sr_tag=False
        for sale in self:
            if sale.type=='out_invoice':
                for tag in sale.partner_id.category_id:
                    if tag.name == 'Sin Retencion':
                        sr_tag=True

                if sr_tag == False:
                    for ol in sale.invoice_line_ids:
                        product_taxes = self.env['product.product'].search([('id','=',ol.product_id.id)])
                        ol.invoice_line_tax_ids=product_taxes.taxes_id
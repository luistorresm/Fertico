from odoo import models, fields, api

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    display_sales=fields.Boolean(string="Display in sales", default=True)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    display_sales=fields.Boolean(string="Display in sales", default=True)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_domain_term(self):
        company=self.env.user.company_id.id
        domain=['&',('display_sales','=',True),('company_id','=',company)]
        return domain

    payment_term_id = fields.Many2one(domain=_get_domain_term)
    pricelist_id = fields.Many2one(domain="[('display_sales','=',True)]")
    

    
    

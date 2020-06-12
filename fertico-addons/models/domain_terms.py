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
    def _get_company(self):
        return self.env.user.company_id.id

    company_user=fields.Integer(default=_get_company)

    payment_term_id = fields.Many2one(domain="['&',('display_sales','=',True),('company_id','=','company_user')]")
    pricelist_id = fields.Many2one(domain="[('display_sales','=',True)]")
    

    
    

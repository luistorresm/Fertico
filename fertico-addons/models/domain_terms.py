from odoo import models, fields, api

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    display_sales=fields.Boolean(string="Display in sales", default=True)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    display_sales=fields.Boolean(string="Display in sales", default=True)
    force_term=fields.Boolean(string="Force terms", default=False)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _get_domain_term(self):
        company=self.env.user.company_id.id
        domain=['&',('display_sales','=',True),('company_id','=',company)]
        return domain

    payment_term_id_domain = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term',
        readonly=True, states={'draft': [('readonly', False)]},
        help="If you use payment terms, the due date will be computed automatically at the generation "
             "of accounting entries. If you keep the payment terms and the due date empty, it means direct payment. "
             "The payment terms may compute several due dates, for example 50% now, 50% in one month.", domain=_get_domain_term)
    pricelist_id_domain = fields.Many2one(
        'product.pricelist', 'Pricelist',
        help='Pricelist of the selected partner.', domain="[('display_sales','=',True)]", required=True)
    force = fields.Boolean(related='pricelist_id.force_term')

    @api.multi
    @api.onchange('payment_term_id_domain')
    def _onchange_term(self):
        self.payment_term_id=self.payment_term_id_domain

    @api.multi
    @api.onchange('pricelist_id_domain')
    def _onchange_pricelist(self):
        self.pricelist_id=self.pricelist_id_domain
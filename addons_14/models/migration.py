from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_gid = fields.Integer()
    additional_info = fields.Char()
    l10n_mx_type_of_operation = fields.Selection([
        ('03', ' 03 - Provision of Professional Services'),
        ('06', ' 06 - Renting of buildings'),
        ('85', ' 85 - Others')])

    def autocomplete(self):
        return True

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pricelist_id_domain = fields.Integer(required=False)
    force = fields.Boolean()
    payment_term_id_domain = fields.Integer(required=False)

    @api.onchange('pricelist_id')
    def change_pricelist(self):
        self.pricelist_id_domain = self.pricelist_id.id

    @api.onchange('payment_term_id')
    def change_term(self):
        self.payment_term_id_domain = self.payment_term_id.id


class StockLocation(models.Model):
    _inherit = 'stock.location'

    allow_negative_stock = fields.Boolean()

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    display_sales = fields.Boolean()
    force_term = fields.Boolean()

class ProductCategory(models.Model):
    _inherit = 'product.category'

    allow_negative_stock = fields.Boolean()

class ResCompany(models.Model):
    _inherit = 'res.company'

    partner_gid = fields.Char()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_studio_field_7eVcs = fields.Selection([('AxC', 'AxC'),
        ('Libre', 'Libre'),
        ('Sabritas', 'Sabritas')], string="Cosecha tipo")
    x_studio_field_E5KYj = fields.Float(string="Descuento")
    x_studio_field_x3aOW = fields.Float(string="% Humedad")

class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_mx_edi_amount_authorized_diff = fields.Float(
        'Amount Authorized Difference (Invoice)', limit=1)
        
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    x_studio_field_KXQlu = fields.Many2one('res.partner', string = "Empresa transferencia interna")

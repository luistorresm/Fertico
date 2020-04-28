from odoo import models, fields, api

class AccountAnalyticDistribution(models.Model):
    _name = 'account.analytic.distribution'
    _description = 'Analytic Account Distribution'

    account_id = fields.Many2one('account.analytic.account', string='Analytic Account', required=True)
    percentage = fields.Float(string='Percentage', required=True, default=100.0)
    name = fields.Char(string='Name',  readonly=False)
    tag_id = fields.Many2one('account.analytic.tag', string="Parent tag", required=True)

    _sql_constraints = [
        ('check_percentage', 'CHECK(percentage >= 0 AND percentage <= 100)',
         'The percentage of an analytic distribution should be between 0 and 100.')
    ]

class AccountAnalyticTag(models.Model):
    _inherit = "account.analytic.tag"

    active_analytic_distribution = fields.Boolean('Analytic Distribution')
    analytic_distribution_ids = fields.One2many('account.analytic.distribution', 'tag_id', string="Analytic Accounts")

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def action_move_create(self):
        """This method make the distribution of the account lines"""
        res= super(AccountInvoice, self).action_move_create()
        for inv in self:

            my_list = []
            n_line=0
            lines = inv.invoice_line_ids
            for line in lines:
                if line.analytic_tag_ids:
                    tags=line.analytic_tag_ids
                    for tag in tags:
                        adis = tag.analytic_distribution_ids
                        for adi in adis:
                            obj = (True,n_line,adi.account_id.id,adi.percentage, line.product_id.name, line.price_subtotal, inv.number, line.quantity, line.product_id.id, line.analytic_tag_ids.ids, line.product_id.uom_id.id)
                            my_list.append(obj)
                else:
                    obj = (False,n_line)
                    my_list.append(obj)
                n_line=n_line+1

            
            inv_move=[]
            for move in inv.move_id.line_ids:
                inv_move.append(move.id)
            inv_move.reverse()

            for ml in my_list:
                if ml[0]==True:
                    
                    if inv.type=='out_invoice':
                        tags=[]
                        tags.append(ml[9])
                        vals = {
                            'account_id' : int(ml[2]),
                            'date' : inv.date_invoice,
                            'amount': (ml[5]*(ml[3]/100)),
                            'name': ml[4],
                            'move_id': inv_move[ml[1]],
                            'ref': ml[6],
                            'unit_amount': ml[7],
                            'product_id': ml[8],
                            'tag_ids': [(6,0,ml[9])],
                            'product_uom_id': ml[10]
                        }
                        record = self.env['account.analytic.line'].create(vals)
                    elif inv.type=='in_invoice':
                        tags=[]
                        tags.append(ml[9])
                        vals = {
                            'account_id' : int(ml[2]),
                            'date' : inv.date_invoice,
                            'amount': (ml[5]*(ml[3]/100))*-1,
                            'name': ml[4],
                            'move_id': inv_move[ml[1]],
                            'ref': ml[6],
                            'unit_amount': ml[7],
                            'product_id': ml[8],
                            'tag_ids': [(6,0,ml[9])],
                            'product_uom_id': ml[10]
                        }
                        record = self.env['account.analytic.line'].create(vals)
        return res

    @api.multi
    @api.onchange('invoice_line_ids')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        for order in self:
            for line in order.invoice_line_ids:
                product_template = self.env['product.template'].search([('name','=',line.product_id.name)])
                tags=[]
                for tag in product_template.analytic_tag_ids:
                    tags.append(tag.id)
                line.analytic_tag_ids = [(6,0,tags)]

class ProductTemplate(models.Model):
    _inherit = "product.template"
    analytic_tag_ids = fields.Many2many('account.analytic.tag', 'product_ids', string="Analytic Tag")

class AnalyticTag(models.Model):
    _inherit = "account.analytic.tag"
    product_ids = fields.Many2many('product.template', 'analytic_tag_ids',string="Product")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    @api.onchange('order_line')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        for order in self:
            for line in order.order_line:
                product_template = self.env['product.template'].search([('name','=',line.product_id.name)])
                tags=[]
                for tag in product_template.analytic_tag_ids:
                    tags.append(tag.id)
                line.analytic_tag_ids = [(6,0,tags)]

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    @api.onchange('order_line')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        for order in self:
            for line in order.order_line:
                product_template = self.env['product.template'].search([('name','=',line.product_id.name)])
                tags=[]
                for tag in product_template.analytic_tag_ids:
                    tags.append(tag.id)
                line.analytic_tag_ids = [(6,0,tags)]
                

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
            my_list_cost =[]
            
            n_line=0
            n_cost=0
            for line in inv.invoice_line_ids:
                if inv.type=='out_invoice':
                    price=line.product_id.standard_price
                for tag in line.analytic_tag_ids:
                    for adi in tag.analytic_distribution_ids:
                        obj = (adi.account_id.id, adi.percentage, line.product_id.name, line.price_subtotal, inv.number, line.quantity, line.product_id.id, line.analytic_tag_ids.ids, line.product_id.uom_id.id,n_line)
                        my_list.append(obj)
                        if inv.type=='out_invoice' and line.product_id.type=='product':
                            obj = (adi.account_id.id,adi.percentage, line.product_id.name, price, inv.number, line.quantity, line.product_id.id, line.analytic_tag_ids.ids, line.product_id.uom_id.id, n_cost)
                            my_list_cost.append(obj)
                if inv.type=='out_invoice' and line.product_id.type=='product':
                    n_cost+=1                            
                n_line+=1
            
            inv_move=[]
            for move in inv.move_id.line_ids:
                inv_move.append(move.id)
            inv_move.reverse()  
            
            for ml in my_list:
                if inv.type=='out_invoice':
                    vals = {
                        'account_id' : int(ml[0]),
                        'date' : inv.date_invoice,
                        'amount': (ml[3]*(ml[1]/100)),
                        'name': ml[2],
                        'move_id': inv_move[ml[9]],
                        'ref': ml[4],
                        'unit_amount': ml[5],
                        'product_id': ml[6],
                        'tag_ids': [(6,0,ml[7])],
                        'product_uom_id': ml[8]
                    }
                    record = self.env['account.analytic.line'].create(vals)
                elif inv.type=='in_invoice':
                    vals = {
                        'account_id' : int(ml[0]),
                        'date' : inv.date_invoice,
                        'amount': (ml[3]*(ml[1]/100))*-1,
                        'name': ml[2],
                        'move_id': inv_move[ml[9]],
                        'ref': ml[4],
                        'unit_amount': ml[5],
                        'product_id': ml[6],
                        'tag_ids': [(6,0,ml[7])],
                        'product_uom_id': ml[8]
                    }
                    record = self.env['account.analytic.line'].create(vals)
                

            for mlc in my_list_cost:
                vals = {
                    'account_id' : int(mlc[0]),
                    'date' : inv.date_invoice,
                    'amount': (mlc[3]*(mlc[1]/100))*-1,
                    'name': mlc[2],
                    'move_id': inv_move[(((mlc[9]+1)*2)+(n_line-1))],
                    'ref': mlc[4],
                    'unit_amount': mlc[5],
                    'product_id': mlc[6],
                    'tag_ids': [(6,0,mlc[7])],
                    'product_uom_id': mlc[8]
                }
                record = self.env['account.analytic.line'].create(vals)
            
        return res

class ProductTemplate(models.Model):
    _inherit = "product.template"
    analytic_tag_ids = fields.Many2many('account.analytic.tag', 'product_ids', string="Analytic Tag")

class AnalyticTag(models.Model):
    _inherit = "account.analytic.tag"
    product_ids = fields.Many2many('product.template', 'analytic_tag_ids',string="Product")

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    @api.multi
    @api.onchange('product_id')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        product_template = self.env['product.template'].search([('name','=',self.product_id.name)])
        tags=[]
        for tag in product_template.analytic_tag_ids:
            tags.append(tag.id)
        self.analytic_tag_ids = [(6,0,tags)]

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    @api.onchange('product_id')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        product_template = self.env['product.template'].search([('name','=',self.product_id.name)])
        tags=[]
        for tag in product_template.analytic_tag_ids:
            tags.append(tag.id)
        self.analytic_tag_ids = [(6,0,tags)]

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.multi
    @api.onchange('product_id')
    def _onchange_add_tag(self):
        "This method load the analytic tags from product.template"
        product_template = self.env['product.template'].search([('name','=',self.product_id.name)])
        tags=[]
        for tag in product_template.analytic_tag_ids:
            tags.append(tag.id)
        self.analytic_tag_ids = [(6,0,tags)]
                

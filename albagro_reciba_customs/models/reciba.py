from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class RecibaOrder(models.Model):
    _name = 'reciba.order'
    _description = 'Reciba'

    @api.one
    @api.depends('gross_weight', 'tare_weight')
    def _get_net(self):
        self.net_weight=self.gross_weight-self.tare_weight

    @api.one
    @api.depends('net_weight', 'discount_kilos_humidity')
    def _calculate_d_humidity(self):
        self.discount_humidity = (self.net_weight * self.discount_kilos_humidity) / 1000

    @api.one
    @api.depends('net_weight', 'discount_kilos_impurity')
    def _calculate_d_impurity(self):
        self.discount_impurity = (self.net_weight * self.discount_kilos_impurity) / 1000

    @api.one
    @api.depends('net_weight', 'discount_kilos_damaged')
    def _calculate_d_damaged(self):
        self.discount_damaged = (self.net_weight * self.discount_kilos_damaged) / 1000

    @api.one
    @api.depends('net_weight', 'discount_kilos_broken')
    def _calculate_d_broken(self):
        self.discount_broken = (self.net_weight * self.discount_kilos_broken) / 1000

    @api.one
    @api.depends('discount_humidity', 'discount_impurity', 'discount_damaged', 'discount_broken')
    def _sum_discount(self):
        self.sum_discounts = self.discount_humidity + self.discount_impurity + self.discount_damaged + self.discount_broken


    @api.one
    @api.depends('sum_discounts')
    def _discount_applied(self):
        self.discount_applied = self.sum_discounts

    @api.one
    @api.depends('net_weight', 'discount_applied')
    def _get_net_discount(self):
        self.net_weight_w_discount = self.net_weight - self.discount_applied

    @api.one
    @api.depends('net_weight_w_discount')
    def _get_free_qty(self):
        self.free_qty = self.net_weight_w_discount

    @api.one
    @api.depends('net_weight_w_discount', 'unit_price')
    def _get_amount_pay(self):
        self.amount_pay = self.net_weight_w_discount * self.unit_price

    @api.one
    @api.depends('amount_pay', 'freigh_threshing_discount')
    def _get_amount_cheque(self):
        self.amount_cheque = self.amount_pay - self.freigh_threshing_discount

    date = fields.Date(string="Date")
    customer_id = fields.Many2one('res.partner', string="Productor name")
    cycle_id = fields.Many2one('reciba.cycle', string="Cycle")
    #=======================Bascula====================
    no_ticket = fields.Char(string="No. ticket", required=True)
    third_folio = fields.Char(string="Third folio")
    reciba_third = fields.Char(string="Reciba for third customer")
    product_id = fields.Many2one('product.product', string="Product")
    modality_id = fields.Many2one('reciba.modality', string="Modality")
    silo = fields.Char(string='Warehouse or silo')
    #======================Descuentos==================
    percentage_humidity = fields.Many2one('reciba.datatd', string="Humidity %", domain="['&',('product_id', '=', product_id),('condition', '=', 'humedad')]")
    discount_kilos_humidity = fields.Float(related='percentage_humidity.discount', string="Discount in kilos humidity", store=True)
    discount_humidity = fields.Float(string="Discount or humidity 14% to more", compute="_calculate_d_humidity", store=True, digits = (12,5))
    percentage_impurity = fields.Many2one('reciba.datatd', string="Impurity %", domain="['&',('product_id', '=', product_id),('condition', '=', 'impureza')]")
    discount_kilos_impurity = fields.Float(related='percentage_impurity.discount', string="Discount in kilos impurity", store=True)
    discount_impurity = fields.Float(string="Discount of impurity 2.5% to more", compute="_calculate_d_impurity", store=True, digits = (12,5))
    percentage_damaged = fields.Many2one('reciba.datatd', string="Damaged grain %", domain="['&',('product_id', '=', product_id),('condition', '=', 'danado')]")
    discount_kilos_damaged = fields.Float(related='percentage_damaged.discount', string="Discount in kilos damaged grain", store=True)
    discount_damaged = fields.Float(string="Discount of damaged grain", compute="_calculate_d_damaged", store=True, digits = (12,5))
    percentage_broken = fields.Many2one('reciba.datatd', string="Broken grain %", domain="['&',('product_id', '=', product_id),('condition', '=', 'quebrado')]")
    discount_kilos_broken = fields.Float(related='percentage_broken.discount', string="Discount in kilos broken grain", store=True)
    discount_broken = fields.Float(string="Discount of broken grain 5.5% to more", compute="_calculate_d_broken", store=True, digits = (12,5))
    sum_discounts = fields.Float(string="Sum calculated discounts", compute="_sum_discount", readonly=False, digits = (12,4))
    discount_applied = fields.Float(string="Discount applied", compute="_discount_applied", readonly=False, digits = (12,3))

    net_weight_w_discount = fields.Float(string="Net weight to pay with discount tons", compute="_get_net_discount", store=True, digits = (12,3))
    free_qty = fields.Float(string="Free quantity", compute="_get_free_qty", store=True, digits = (12,3), readonly=False)
    #========================Logistica================================
    operator = fields.Char(string="Operator name")
    plate = fields.Char(string="Placas")
    gross_weight = fields.Float(string="Gross weight")
    tare_weight = fields.Float(string="Tare weight")
    net_weight = fields.Float(string="Net weight", compute="_get_net", store=True)
    #========================Pago====================================
    change_type = fields.Float(string="Change type")
    price_usd = fields.Char(string="Price agreed USD")
    unit_price = fields.Float(string="Unit price tons")
    currency = fields.Many2one('res.currency', string="Currency")
    amount_pay = fields.Float(string="Import to pay cheque", compute="_get_amount_pay", store=True)
    incentive = fields.Float(string="Incent.")
    freigh_threshing_discount = fields.Float("Freight and threshing discount")
    #=========================Programacion de pagos==================
    number_cheque = fields.Char("Cheque number")
    amount_cheque = fields.Float("Amount cheque", compute="_get_amount_cheque", store=True)
    collection_date = fields.Date("Collection date")
    folio_bill = fields.Char("Folio Bill")
    payment_date = fields.Date("Payment date")
    observations = fields.Text("Observations")
    error_message = fields.Text(compute='display_debts_pop_up')

    
    #=========================Nombre que se muestra en los campos relacionados con este modelo==============
    def name_get(self):
        res=[]
        for reciba in self:
            res.append((reciba.id,reciba.no_ticket))
        return res


    def display_debts_pop_up(self):
        _logger.info('\n\n\n contexto: %s\n\n\n', self.env.context)
        #Retrieve rows from "account.invoice" model where the present provider
        #is revised to detect if has open invoices indicating that must pay its debts:         
        msg = ""; summatory_residual = 0
        sql_query = """SELECT company_id, SUM(residual_signed) 
                         FROM account_invoice 
                        WHERE partner_id = %s
                          AND state = 'open'   
                          AND (type = 'out_invoice' OR type = 'out_refund') 
                        GROUP BY company_id;"""
                        
        self.env.cr.execute(sql_query, (self.customer_id.id,))
        residual_companies = self.env.cr.fetchall()           
        _logger.info('\n\n\n residual_companies: %s\n\n\n', residual_companies)

        #Validate if query has results:
        if residual_companies:   
            _logger.info('\n\n\n sí entra \n\n\n')
            #Construct the error message, beginning with client with open sales invoices:
            debtor = self.env['res.partner'].search([('id', '=', self.customer_id.id)]).name
            msg = _('The related contact on the purchase order %s has outstanding balances on sales: \n') % (debtor)
                          
            for val in residual_companies:
                #Iterate companies with residual (outstanding balance) and concatenate
                company_name = self.env['res.company'].search([('id', '=', val[0])]).name
                msg += _('\n[+] %s balance by $%s') % (company_name, val[1])                    
                #Sum up residuals in order to indicate how much is debted
                summatory_residual += val[1] 
                         
            #Concatenate last part of error message:
            msg += _('\n\nConsider making discounts for settlement.')
            self.error_message = msg
            _logger.info('\n\n\n self.error_message\n: %s\n\n\n', self.error_message)
    
    #=========================Search para encontrar el nombre en un campo relacionado=======================
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.browse()
        if name:
            recs = self.search([('no_ticket', '=', name)] + args, limit=limit)
        if not recs:
            recs = self.search([('no_ticket', operator, name)] + args, limit=limit)
        return recs.name_get()

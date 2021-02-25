from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError

class SaleCommission(models.TransientModel):
    #Comisiones de venta    
    _name='sale.commission'
    
    product = fields.Many2one('product.product', string="Producto")
    init_date = fields.Datetime(string="Fecha inicio")
    end_date = fields.Datetime(string="Fecha fin")

class ReportSaleCommission(models.AbstractModel):
    #Reporte recepciones por facturar
    _name = 'report.fertico_reports.report_sale_commission'

    @api.model
    def get_report_values(self, docids, data=None):
        print("====================")
        report = self.env['sale.commission'].browse(docids)
        invoices = self.env['account.invoice'].search([('date','>',report.init_date),('date','<',report.end_date)])
        print("===========-------=======")
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'report_data' : report,
            'invoices' : invoices
        }
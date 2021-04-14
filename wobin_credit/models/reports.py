from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError

class CreditAccountStatus(models.TransientModel):
    #Recepciones por facturar    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")

class ReportAccountStatus(models.AbstractModel):
    #Reporte recepciones por facturar
    _name = 'report.wobin_credit.report_account_status'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['credit.account.status'].browse(docids)
        print("========================", report.partner_id.name)
        invoices = self.env['account.invoice'].search([('partner_id','=',report.partner_id.id)])
        
        print("========================", invoices)

        '''sum_net = 0
        count = 0
        tickets_uninvoiced = []
        for receipt in tickets:
            sum_net += receipt.net_weight
            count += 1
            data = {
                'name': receipt.name,
                'date': receipt.date.strftime("%d/%m/%Y %H:%M:%S"),
                'partner_id': receipt.partner_id,
                'net_weight': "{:,.0f}".format(receipt.net_weight)
            }
            tickets_uninvoiced.append(data)
        

        report_data = {
            'i_date' : report.init_date.strftime("%d/%m/%Y"),
            'e_date': report.end_date.strftime("%d/%m/%Y"),
            'today' : date.today(),
            'product' : report.product.name,
            'location' : report.location.name,
            'sum_net' : "{:,.0f}".format(sum_net),
            'count' : count
        }'''

        return {
            'doc_ids': docids,
            'doc_model': 'credit.preapplication',
            'docs' : report,
            'invoices' : invoices
        }

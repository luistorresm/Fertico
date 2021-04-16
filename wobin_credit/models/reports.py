from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError

class CreditAccountStatus(models.TransientModel):
    #Recepciones por facturar    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")
    insurance = fields.Float(string="Seguro Agrícola")

class ReportAccountStatus(models.AbstractModel):
    #Reporte recepciones por facturar
    _name = 'report.wobin_credit.report_account_status'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['credit.account.status'].browse(docids)
        credit = self.env['credit.preapplication'].search([('partner_id','=',report.partner_id.id)], limit=1)
        invoices = self.env['account.invoice'].search([('partner_id','=',report.partner_id.id),('type','=','out_invoice'),('state','=','open')])
        inv_data = []
        total = 0
        sum_invoices = 0
        sum_interest = 0

        for invoice in invoices:
            interest = invoice.amount_total*(credit.interest/100)
            interest_mo = 0
            date_invoice = datetime.strptime(invoice.date, '%Y-%m-%d')
            date_now = datetime.now()

            term = credit.payment_terms.line_ids[1].days
            
            if term == 30:
                days = (date_now - date_invoice).days
            
                if  days > 30 and days <= 60:
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days-30)
                elif days > 60:
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days-30)
                    interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days-60)
            
            elif term == 180:
                days = (date_now - date_invoice).days
                date_limit = datetime.strptime(credit.date_limit, '%Y-%m-%d')
                days_limit = (date_limit - date_invoice).days

                if  date_now <= date_limit:
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days)
                elif days > date_limit:
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days)
                    interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days-days_limit)
            
            total_inv = invoice.amount_total+interest+interest_mo
            total += total_inv
            sum_invoices += invoice.amount_total
            sum_interest += interest + interest_mo

            inv = {
                'number': invoice.number,
                'date': invoice.date_invoice,
                'amount' : invoice.amount_total,
                'date_payment' : date.today(),
                'interest': interest,
                'interest_mo': interest_mo,
                'total': total_inv
            }
            inv_data.append(inv)
        
        data = {
            'authorized' : credit.authorized_amount,
            'interest' : credit.interest,
            'sum_invoices' : sum_invoices,
            'sum_interest' : sum_interest,
            'total' : total,
            'date' : date.today()
        }


        return {
            'doc_ids': docids,
            'doc_model': 'credit.preapplication',
            'docs' : report,
            'data' : data,
            'invoices' : inv_data
        }

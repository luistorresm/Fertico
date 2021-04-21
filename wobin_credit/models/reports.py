from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError

class CreditAccountStatus(models.TransientModel):
    #Recepciones por facturar    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")
    date = fields.Date(string="Fecha de cálculo")

class ReportAccountStatus(models.AbstractModel):
    #Reporte recepciones por facturar
    _name = 'report.wobin_credit.report_account_status'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['credit.account.status'].browse(docids)
        credit = self.env['credit.preapplication'].search([('partner_id','=',report.partner_id.id)], limit=1)
        invoices = self.env['account.invoice'].search([('partner_id','=',report.partner_id.id),('type','=','out_invoice'),('state','=','open')])
        date_payment = datetime.strptime(report.date, '%Y-%m-%d')
        inv_data = []
        total = 0
        sum_invoices = 0
        sum_interest = 0

        for invoice in invoices:
            interest = invoice.amount_total*(credit.interest/100)
            interest_mo = 0
            date_invoice = datetime.strptime(invoice.date, '%Y-%m-%d')
            term = credit.payment_terms.line_ids[1].days
            days = 0
            days_limit = 0
            days_nat = 0
            days_int = 0
            days_mo = 0

            if term == 30:
                days = (date_payment - date_invoice).days
                days_nat = days
                if  days > 30 and days <= 60:
                    days_nat = 30
                    days_int = days-30
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                elif days > 60:
                    days_nat = 30
                    days_int = days-30
                    days_mo = days-60
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                    interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days_mo)
            
            elif term == 180:
                days = (date_payment - date_invoice).days
                date_limit = datetime.strptime(credit.date_limit, '%Y-%m-%d')
                days_limit = (date_limit - date_invoice).days

                if  date_payment <= date_limit:
                    days_int = days
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                elif date_payment > date_limit:
                    days_int = days_limit
                    days_mo = days-days_limit
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                    interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days_mo)
            
            total_inv = invoice.amount_total+interest+interest_mo
            total += total_inv
            sum_invoices += invoice.amount_total
            sum_interest += interest + interest_mo

            inv = {
                'number': invoice.number,
                'date': date_invoice.strftime("%d/%m/%Y"),
                'amount' : "{:,.2f}".format(invoice.amount_total),
                'date_payment' : date_payment.strftime("%d/%m/%Y"),
                'days_nat' : days_nat,
                'days_int' : days_int,
                'days_mo': days_mo,
                'interest': "{:,.2f}".format(interest),
                'interest_mo': "{:,.2f}".format(interest_mo),
                'total': "{:,.2f}".format(total_inv)
            }
            inv_data.append(inv)
        
        total += credit.insurance
        
        data = {
            'cycle' : credit.cycle,
            'authorized' : "{:,.2f}".format(credit.authorized_amount),
            'interest' : "{:,.2f}".format(credit.interest),
            'sum_invoices' : "{:,.2f}".format(sum_invoices),
            'sum_interest' : "{:,.2f}".format(sum_interest),
            'total' : "{:,.2f}".format(total),
            'date' : date_payment.strftime("%d/%m/%Y"),
            'insurance' : "{:,.2f}".format(credit.insurance)
        }


        return {
            'doc_ids': docids,
            'doc_model': 'credit.preapplication',
            'docs' : report,
            'data' : data,
            'invoices' : inv_data,
            'company' : self.env.user.company_id
        }

from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError

class CreditAccountStatus(models.TransientModel):
    #Estado de cuenta    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")
    insurance = fields.Float(string="Seguro Agrícola")

class ReportAccountStatus(models.AbstractModel):
    #Reporte estado de cuenta
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
            days = 0
            days_limit = 0
            days_nat = 0
            days_mo = 0

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
                    days_nat = days
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days)
                elif date_now > date_limit:
                    days_nat = days_limit
                    days_mo = days-days_limit
                    interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_nat)
                    interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days_mo)
            
            total_inv = invoice.amount_total+interest+interest_mo
            total += total_inv
            sum_invoices += invoice.amount_total
            sum_interest += interest + interest_mo

            inv = {
                'number': invoice.number,
                'date': date_invoice.strftime("%d/%m/%Y"),
                'amount' : "{:,.2f}".format(invoice.amount_total),
                'date_payment' : date.today().strftime("%d/%m/%Y"),
                'days_nat' : days_nat,
                'days_mo' : days_mo,
                'interest': "{:,.2f}".format(interest),
                'interest_mo': "{:,.2f}".format(interest_mo),
                'total': "{:,.2f}".format(total_inv)
            }
            inv_data.append(inv)
        
        total += report.insurance
        
        data = {
            'cycle' : credit.cycle,
            'authorized' : "{:,.2f}".format(credit.authorized_amount),
            'interest' : "{:,.2f}".format(credit.interest),
            'sum_invoices' : "{:,.2f}".format(sum_invoices),
            'sum_interest' : "{:,.2f}".format(sum_interest),
            'total' : "{:,.2f}".format(total),
            'date' : date.today().strftime("%d/%m/%Y")
        }


        return {
            'doc_ids': docids,
            'doc_model': 'credit.preapplication',
            'docs' : report,
            'data' : data,
            'invoices' : inv_data
        }

#=====================================================================================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_commitment'

    @api.model
    def get_report_values(self, docids, data=None):
        record = self.env['credit.record'].browse(docids)

        

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : record,
            'company' : self.env.user.company_id,
        }
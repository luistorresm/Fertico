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
            'invoices' : inv_data,
            'company' : self.env.user.company_id,
        }

#===============================================Carta compromiso========================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_commitment'

    @api.model
    def get_report_values(self, docids, data=None):
        record = self.env['credit.record'].browse(docids)
        date_now =  date.today().strftime("%d/%m/%Y")
        
        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : record,
            'date' : date_now,
            'company' : self.env.user.company_id,
        }

#===============================================Solicitud========================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application'

    @api.model
    def get_report_values(self, docids, data=None):
        pre_application = self.env['credit.preapplication'].browse(docids)
        date_now =  date.today().strftime("%d/%m/%Y")
        
        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : pre_application,
            'date' : date_now,
            'company' : self.env.user.company_id,
            'user' : self.env.user,
        }

#===============================================Carta buro========================================================

class CreditAccountStatus(models.TransientModel):
    #Estado de cuenta    
    _name='credit.application.buro'
    
    applicant = fields.Selection([('pf','Persona Física'),
    ('pfae','Persona Física con Actividad Empresarial'),
    ('pm','Persona Moral')], string="Solicitante")
    agent = fields.Char(string="Nombre del representante")
    partner_authorization = fields.Many2one('res.partner', string="Funcionario que recaba la Autorización")
    application_id = fields.Many2one('credit.preapplication')
    location = fields.Char(string="Lugar donde se firma la autorización")


class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application_buro'

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['credit.application.buro'].browse(docids)

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : report.application_id,
            'data' : report,
            'date' : date_now,
            'company' : self.env.user.company_id,
            'user' : self.env.user,
        }
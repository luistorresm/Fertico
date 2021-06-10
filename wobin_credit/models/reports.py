from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError
from num2words import num2words

class CreditAccountStatus(models.TransientModel):
    #Estado de cuenta    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")
    insurance = fields.Float(string="Seguro Agrícola")

class ReportAccountStatus(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_account_status'

    @api.model
    def _get_report_values(self, docids, data=None):
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

'''class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_commitment'

    @api.model
    def _get_report_values(self, docids, data=None):
        record = self.env['credit.record'].browse(docids)
        date_now =  date.today().strftime("%d/%m/%Y")
        
        return {
            'lines': record
        }'''

'''class ReportCommitment(models.AbstractModel):
    _name = 'report.wobin_credit.report_commitment'

    @api.model
    def _get_report_values(self, docids, data=None):
        # get the records selected for this rendering of the report
        obj = self.env['credit.record'].browse(docids)
        # return a custom rendering context

        print("=============================", obj)
        return {
            'docs': obj
        }'''

#===============================================Solicitud========================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application'

    @api.model
    def _get_report_values(self, docids, data=None):
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

class CreditApplicationBuro(models.TransientModel):
    #Estado de cuenta    
    _name='credit.application.buro'
    
    applicant = fields.Selection([('pf','Persona Física'),
    ('pfae','Persona Física con Actividad Empresarial'),
    ('pm','Persona Moral')], string="Solicitante")
    agent = fields.Char(string="Nombre del representante")
    partner_authorization = fields.Many2one('res.partner', string="Funcionario que recaba la Autorización")
    application_id = fields.Many2one('credit.preapplication')
    location = fields.Char(string="Lugar donde se firma la autorización")


class ReportBuro(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application_buro'

    @api.model
    def _get_report_values(self, docids, data=None):
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

#===============================================Contrato========================================================

class CreditApplicationContract(models.TransientModel):
    #Estado de cuenta    
    _name='credit.application.contract'
    
    constitutive = fields.Text(string="Constitutiva")
    registral = fields.Text(string="Datos registrales")
    application_id = fields.Many2one('credit.preapplication')


class ReportContract(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application_contract'

    def _number_to_text(self, amount):
        
        number = "{:.2f}".format(amount).split(".")
        text = num2words(number[0], lang='es').upper().split("PUNTO CERO")[0] + "PUNTO " + num2words(number[1], lang='es').upper().split("PUNTO CERO")[0]
        return text

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['credit.application.contract'].browse(docids)
        preapplication = report.application_id
        total_hectares = 0

        for crop in preapplication.crop_type_ids:
            total_hectares += crop.hectares

        contract_data = {
            'company': self.env.user.company_id.name,
            'address_company': self.env.user.company_id.street+','+self.env.user.company_id.city+','+self.env.user.company_id.state_id.name+','+self.env.user.company_id.zip,
            'address_partner': preapplication.address+','+preapplication.suburb+','+preapplication.locality+','+preapplication.state_address+','+preapplication.postal_code,
            'amount_text': self._number_to_text(preapplication.authorized_amount),
            'total_hectares': total_hectares
        }

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : preapplication,
            'data' : report,
            'contract' : contract_data,
            'date' : date_now,
            'company' : self.env.user.company_id,
            'user' : self.env.user,
        }

#===============================================Pagare========================================================

class CreditApplicationPromissoryNote(models.TransientModel):
    #Pagare    
    _name='credit.application.promissory.note'
    
    place = fields.Char(string="Lugar")
    date = fields.Date(string="Fecha")
    application_id = fields.Many2one('credit.preapplication')

class ReportPromissoryNote(models.AbstractModel):
    #Reporte pagare
    _name = 'report.wobin_credit.report_application_promissory_note'

    def _number_to_text(self, amount):
        
        number = "{:.2f}".format(amount).split(".")
        text = num2words(number[0], lang='es').upper().split("PUNTO CERO")[0] + "PUNTO " + num2words(number[1], lang='es').upper().split("PUNTO CERO")[0]
        return text

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['credit.application.promissory.note'].browse(docids)
        preapplication = report.application_id
        total_hectares = 0

        for crop in preapplication.crop_type_ids:
            total_hectares += crop.hectares

        contract_data = {
            'company': self.env.user.company_id.name,
            'address_company': self.env.user.company_id.street+','+self.env.user.company_id.city+','+self.env.user.company_id.state_id.name+','+self.env.user.company_id.zip,
            'address_partner': preapplication.address+','+preapplication.suburb,
            'amount_text': self._number_to_text(preapplication.authorized_amount),
            'total_hectares': total_hectares,
            'amount': "{:,.2f}".format(preapplication.authorized_amount),
            'date': datetime.strptime(report.date, '%Y-%m-%d').strftime("%d/%m/%Y")
        }

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : preapplication,
            'data' : report,
            'contract' : contract_data,
            'date' : date_now,
            'company' : self.env.user.company_id,
            'user' : self.env.user,
        }

    
#===============================================Firmas========================================================

class CreditApplicationSignature(models.TransientModel):
    #Firmas    
    _name='credit.application.signature'
    
    place = fields.Char(string="Sucursal")
    names = fields.One2many('credit.application.signature.names', 'signature_id', string="Firmas autorizadas")
    application_id = fields.Many2one('credit.preapplication')

class CreditApplicationSignatureNames(models.TransientModel):
    #Firmas nombres   
    _name='credit.application.signature.names'
    
    name_signature = fields.Char(string="Nombre")
    signature_id = fields.Many2one('credit.application.signature')


class ReportSignature(models.AbstractModel):
    #Reporte firmas
    _name = 'report.wobin_credit.report_application_signature'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['credit.application.signature'].browse(docids)
        preapplication = report.application_id

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : preapplication,
            'data' : report,
            'date' : date_now,
            'company' : self.env.user.company_id,
            'user' : self.env.user,
        }


#===============================================Recibo de pago========================================================

class CreditApplicationPayment(models.TransientModel):
    #Pagos    
    _name='credit.application.payment'
    
    date = fields.Date(string="Fecha")
    amount = fields.Float(string="Cantidad")
    concept = fields.Char(string="Concepto")
    receiver = fields.Char(string="Recibió")
    payment_type = fields.Selection([('efectivo', 'Efectivo'),
    ('cheque', 'Cheque'),
    ('trans','Transferencia')], string="Forma de pago")
    application_id = fields.Many2one('credit.preapplication')


class ReportPayment(models.AbstractModel):
    #Reporte pagos
    _name = 'report.wobin_credit.report_application_payment'

    def _number_to_text(self, amount):
        
        number = "{:.2f}".format(amount).split(".")
        text = num2words(number[0], lang='es').upper().split("PUNTO CERO")[0] + "PUNTO " + num2words(number[1], lang='es').upper().split("PUNTO CERO")[0]
        return text

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['credit.application.payment'].browse(docids)
        preapplication = report.application_id

        return {
            'doc_ids': docids,
            'doc_model': 'credit.record',
            'docs' : preapplication,
            'data' : report,
            'date' : datetime.strptime(report.date, '%Y-%m-%d').strftime("%d/%m/%Y"),
            'company' : self.env.user.company_id,
            'user' : self.env.user,
            'amount_text': self._number_to_text(report.amount)
        }



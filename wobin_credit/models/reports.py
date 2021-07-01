from odoo import models, fields, api
from datetime import date, datetime
from odoo.exceptions import UserError
from num2words import num2words

#===========================================Estado de cuenta==================================================

class CreditAccountStatus(models.TransientModel):
    #Estado de cuenta    
    _name='credit.account.status'
    
    partner_id = fields.Many2one('res.partner', string="Cliente")
    date = fields.Date(string="Fecha de cálculo")

class ReportAccountStatus(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_account_status'

    @api.model
    def get_report_values(self, docids, data=None):
        #Obtenermos la informacion del la ventana emergente
        report = self.env['credit.account.status'].browse(docids)
        #Buscamos los registros del credito y facturas con los que vamos a trabajar
        credit = self.env['credit.preapplication'].search([('partner_id','=',report.partner_id.id)], limit=1)
        invoices = self.env['account.move'].search([('partner_id','=',report.partner_id.id),('move_type','=','out_invoice'),('state','=','posted'),'|',('payment_state','=','in_payment'),('payment_state','=','partial')])
        date_payment = report.date
        inv_data = []
        total = 0
        sum_invoices = 0
        sum_interest = 0
        payments = []

        for invoice in invoices:
            #Recorremos todas las factura para hacer los calculos
            interest = 0
            interest_mo = 0
            date_invoice = invoice.invoice_date
            term = credit.payment_terms.line_ids[1].days
            days = 0
            days_limit = 0
            days_nat = 0
            days_int = 0
            days_mo = 0

            if term == 30:
                #Si el credito es comercial, revisamos si tiene pagos provisionales o abonos
                if invoice.line_ids:
                    date_init = date_invoice
                    date_end = ''
                    total_invoice = invoice.amount_total
                    pay = {}

                    payments_array = []
                    for payment in invoice.line_ids:
                        payments_array.append(payment)
                    payments_array.reverse()

                    for payment in payments_array:
                        #Por cada pago revisamos los intereses que generó
                    
                        pay_date = datetime.strptime(payment.date, '%Y-%m-%d').strftime("%d/%m/%Y")
                        date_end = datetime.strptime(payment.date, '%Y-%m-%d')
                        days_init = (date_init - date_invoice).days
                        days_end = (date_end - date_invoice).days
                            
                        if  days_end <= 30:
                            #C1 si el pago se hizo antes de 30 dias - este no genera ningun tipo de interes
                            days_nat = days_end-days_init                      
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : days_nat,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : 0,
                                'total_mo' : 0}
                            
                        elif  days_init <= 30 and days_end > 30 and days_end <= 60:
                            #C2 si el pago abarca un periodo de menos de antes de 30 dias y antes de 60 - genera interes normal despues del dia 30
                            days_nat = 30
                            days_int = days_end-30
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_int)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 30-days_init,
                                'days_int' : days_int,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_int)),
                                'days_mo' : 0,
                                'total_mo' : 0}
                            
                        elif days_init > 30 and days_end <= 60:
                            #C3 si el pago abarga un periodo despues del dia 30 y antes del dia 60 - genera interes normal
                            days_nat = 30
                            days_int = days_end-30
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : days_int,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_int)),
                                'days_mo' : 0,
                                'total_mo' : 0}
                            
                        elif days_init > 30 and days_init <= 60 and days_end > 60:
                            #C4 si el pago abarca un periodo despues del dia 30 y desues del 60 - genera interes normal e interes moratorio
                            days_nat = 30
                            days_int = 30
                            days_mo = days_end-60
                            interest += ((total_invoice*(credit.interest/100))/30)*(60 - days_init)
                            interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : 60 - days_init,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(60 - days_init)),
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                            
                        elif days_init <= 30 and days_end > 60:
                            #C5 si el pago abarca un periodo antes del dia 30 y despues del dia 60 - genera interes normal e interes moratorio
                            days_nat = 30
                            days_int = 30
                            days_mo = days_end-60
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_int)
                            interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 30-days_init,
                                'days_int' : days_int,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_int)),
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                            
                        elif days_init > 60:
                            #C6 si el pago abarca un periodo despues del dia 60 - genera solo interes moratorio
                            days_nat = 30
                            days_int = 30
                            days_mo = days_end-60
                            interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_end-days_init)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_end-days_init))}

                        payments.append(pay)
                        date_init = date_end
                        total_invoice -= payment.amount_currency
                    
                    days_init = (date_init - date_invoice).days
                    days_end = (date_payment - date_invoice).days
                    #Hacemos el proceso una vez mas tomando la fecha en que se va a liquidar el crédito siguiendo los mismos parametros

                    if  days_end <= 30:
                        days_nat = days_end-days_init
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : days_end-days_init,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : 0,
                                'total_mo' : 0}                  
                
                    elif  days_init <= 30 and days_end > 30 and days_end <= 60:
                        days_nat = 30
                        days_int = days_end-30
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_int)
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : 30-days_init,
                                'days_int' : days_end-30,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_int)),
                                'days_mo' : 0,
                                'total_mo' : 0} 
                        
                    elif days_init > 30 and days_end <= 60:
                        days_nat = 30
                        days_int = days_end-30
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : days_end-days_init,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_end-days_init)),
                                'days_mo' : 0,
                                'total_mo' : 0}
                        
                    elif days_init > 30 and days_init <= 60 and days_end > 60:
                        days_nat = 30
                        days_int = 30
                        days_mo = days_end-60
                        interest += ((total_invoice*(credit.interest/100))/30)*(60 - days_init)
                        interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : 60 - days_init,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(60 - days_init)),
                                'days_mo' :days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                        
                    elif days_init <= 30 and days_end > 60:
                        days_nat = 30
                        days_int = 30
                        days_mo = days_end-60
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_int)
                        interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : 30 - days_init,
                                'days_int' : days_int,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_int)),
                                'days_mo' :days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                        
                    elif days_init > 60:
                        days_nat = 30
                        days_int = 30
                        days_mo = days_end-60
                        interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_end-days_init)
                        pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : ' - ',
                                'date' : '-',
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : days_end-days_init,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_end-days_init))}
                        
                    payments.append(pay)
                        
                else:
                    #Si no hay pagos parciales tomamos en cuanta un solo pago a la fecha seleccionada y calculamos los intereses
                    interest = 0
                    days = (date_payment - date_invoice).days
                    days_nat = days
                    if  days > 30 and days <= 60:
                        days_nat = 30
                        days_int = days-30
                        interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                    elif days > 60:
                        days_nat = 30
                        days_int = 30
                        days_mo = days-60
                        interest = ((invoice.amount_total*(credit.interest/100))/30)*(days_int)
                        interest_mo = ((invoice.amount_total*(credit.interest_mo/100))/30)*(days_mo)
            
            elif term == 180:
                #Si el credito es avio, revisamos si tiene pagos provisionales o abonos
                if invoice.payment_ids:
                    date_init = date_invoice
                    date_end = ''
                    date_limit = datetime.strptime(credit.date_limit, '%Y-%m-%d')
                    days_limit = (date_limit - date_invoice).days
                    total_invoice = invoice.amount_total
                    pay = {}

                    payments_array = []
                    for payment in invoice.payment_ids:
                        payments_array.append(payment)
                    payments_array.reverse()

                    for payment in payments_array:
                        #Por cada pago revisamos los intereses que generó
                        pay_date = datetime.strptime(payment.date, '%Y-%m-%d').strftime("%d/%m/%Y")
                        date_end = datetime.strptime(payment.date, '%Y-%m-%d')
                        days_init = (date_init - date_invoice).days
                        days_end = (date_end - date_invoice).days
                            
                        if date_init <= date_limit and date_end <= date_limit:
                            #C1 si el pago abarca un intervalo antes del día limite
                            days_int = (date_end-date_invoice).days
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : days_nat,
                                'days_int' : days_end-days_init,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_end-days_init)),
                                'days_mo' : 0,
                                'total_mo' : 0}

                        elif date_init <= date_limit and date_end > date_limit:
                            #C2 si el pago abarca un intervalo antes y despues del día límite
                            days_int = (date_limit-date_invoice).days
                            days_mo = (date_end-date_limit).days
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_limit-days_init)
                            interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : days_nat,
                                'days_int' : days_limit-days_init,
                                'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_limit-days_init)),
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}

                        elif date_init > date_limit and date_end > date_limit:
                            #C3 si el pago abarca un intervalo despues del dia límite
                            days_int = (date_limit-date_invoice).days
                            days_mo = (date_end-date_limit).days
                            interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                            pay = {'invoice' : invoice.name,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment.amount_currency),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : days_nat,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                            
                        payments.append(pay)
                        date_init = date_end
                        total_invoice -= payment.amount_currency
                    
                    date_end = date_payment
                    days_end = (date_end - date_invoice).days
                    days_init = (date_init - date_invoice).days
                            
                    #Hacemos un ultimo registro con el pago a realizar
                    if date_init <= date_limit and date_end <= date_limit:
                        days_int = (date_end-date_invoice).days
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                        pay = {'invoice' : invoice.name,
                            'total' : "{:,.2f}".format(total_invoice),
                            'payment_amount' : ' - ',
                            'date' : '-',
                            'days' : days_end-days_init,
                            'days_nat' : days_nat,
                            'days_int' : days_end-days_init,
                            'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_end-days_init)),
                            'days_mo' : 0,
                            'total_mo' : 0}

                    elif date_init <= date_limit and date_end > date_limit:
                        days_int = (date_limit-date_invoice).days
                        days_mo = (date_end-date_limit).days
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_limit-days_init)
                        interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                        pay = {'invoice' : invoice.name,
                            'total' : "{:,.2f}".format(total_invoice),
                            'payment_amount' : ' - ',
                            'date' : '-',
                            'days' : days_end-days_init,
                            'days_nat' : days_nat,
                            'days_int' : days_limit-days_init,
                            'total_int' : "{:,.2f}".format(((total_invoice*(credit.interest/100))/30)*(days_limit-days_init)),
                            'days_mo' : days_mo,
                            'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                    
                    elif date_init > date_limit and date_end > date_limit:
                        days_int = (date_limit-date_invoice).days
                        days_mo = (date_end-date_limit).days
                        interest_mo += ((total_invoice*(credit.interest_mo/100))/30)*(days_mo)
                        pay = {'invoice' : invoice.name,
                            'total' : "{:,.2f}".format(total_invoice),
                            'payment_amount' : ' - ',
                            'date' : '-',
                            'days' : days_end-days_init,
                            'days_nat' : days_nat,
                            'days_int' : 0,
                            'total_int' : 0,
                            'days_mo' : days_mo,
                            'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                    
                    payments.append(pay)
                        

                else:
                    #Si no hay pagos  parciales se hace el calculo con la fecha del reporte para obtener los intereses
                    days = (date_payment - date_invoice).days
                    date_limit = datetime.strptime(credit.date_limit, '%Y-%m-%d')
                    days_limit = (date_limit - date_invoice).days

                    if  date_payment <= date_limit:
                        days_int = days
                        interest = ((invoice.amount_residual*(credit.interest/100))/30)*(days_int)
                    elif date_payment > date_limit:
                        days_int = days_limit
                        days_mo = days-days_limit
                        interest = ((invoice.amount_residual*(credit.interest/100))/30)*(days_int)
                        interest_mo = ((invoice.amount_residual*(credit.interest_mo/100))/30)*(days_mo)
            
            #Sumamos los totales de los intereses y la factura para determinar el pago final
            total_inv = invoice.amount_residual+interest+interest_mo
            total += total_inv
            sum_invoices += invoice.amount_residual
            sum_interest += interest + interest_mo
            #Se guarda un objeto con la información de la factura para mostrar el historial
            inv = {
                'number': invoice.name,
                'date': date_invoice.strftime("%d/%m/%Y"),
                'amount' : "{:,.2f}".format(invoice.amount_residual),
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
        #Objeto con los totales a pagar para mostrar en el informe
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
            'payments' : payments,
            'company' : self.env.user.company_id
        }


#===============================================Carta compromiso========================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_commitment'

    @api.model
    def _get_report_values(self, docids, data=None):
        record = self.env['credit.record'].browse(docids)
        date_now =  date.today().strftime("%d/%m/%Y")
        
        return {
            'docs': record,
            'date': date_now
        }

#===============================================Solicitud========================================================

class ReportCommitment(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application'

    @api.model
    def _get_report_values(self, docids, data=None):
        pre_application = self.env['credit.preapplication'].browse(docids)
        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'docs' : pre_application,
            'date' : date_now,
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
    location = fields.Char(string="Lugar donde se firma la autorización")
    application_id = fields.Many2one('credit.preapplication')


class ReportBuro(models.AbstractModel):
    #Reporte estado de cuenta
    _name = 'report.wobin_credit.report_application_buro'

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['credit.application.buro'].browse(docids)

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'docs' : report,
            'data' : report.application_id,
            'date' : date_now,
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
            'docs' : report,
            'data' : preapplication,
            'contract' : contract_data,
            'date' : date_now,
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
            'date': report.date.strftime("%d/%m/%Y")
        }

        date_now =  date.today().strftime("%d/%m/%Y")

        return {
            'docs' : report,
            'data' : preapplication,
            'contract' : contract_data,
            'date' : date_now,
            'user' : self.env.user,
            'company' : self.env.user.company_id,
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
            'docs' : report,
            'data' : preapplication,
            'date' : date_now,
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
            'docs' : report,
            'data' : preapplication,
            'date' : report.date.strftime("%d/%m/%Y"),
            'company' : self.env.user.company_id,
            'user' : self.env.user,
            'amount_text': self._number_to_text(report.amount)
        }



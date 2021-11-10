from odoo import models, fields, api
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from num2words import num2words
import json

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
        invoices = self.env['account.invoice'].search([('partner_id','=',report.partner_id.id),('type','=','out_invoice'),('state','=','open')])
        date_payment = datetime.strptime(report.date, '%Y-%m-%d')
        inv_data = []
        total = 0
        sum_invoices = 0
        sum_interest = 0
        payments = []

        for invoice in invoices:
            #Recorremos todas las factura para hacer los calculos
            payments_text = invoice.payments_widget
            interest = 0
            interest_mo = 0
            date_invoice = datetime.strptime(invoice.date, '%Y-%m-%d')
            term = credit.payment_terms.line_ids[1].days
            days = 0
            days_limit = 0
            days_nat = 0
            days_int = 0
            days_mo = 0

            if term == 30:
                #Si el credito es comercial, revisamos si tiene pagos provisionales o abonos
                
                if payments_text != 'false':
                    date_init = date_invoice
                    date_end = ''
                    total_invoice = invoice.amount_total
                    pay = {}

                    payments_json = json.loads(payments_text)['content']
                    payments_array=[]
                    for pay in payments_json:
                        payments_array.append({'amount':pay['amount'],'date':pay['date']})

                    for payment in payments_array:
                        #Por cada pago revisamos los intereses que generó

                        pay_date = payment['date']
                        date_end = datetime.strptime(payment['date'], '%Y-%m-%d')
                        days_init = (datetime.strptime(date_init, '%Y-%m-%d') - datetime.strptime(date_invoice,'%Y-%m-%d')).days
                        days_end = (date_end - date_invoice).days
                            
                        if  days_end <= 30:
                            #C1 si el pago se hizo antes de 30 dias - este no genera ningun tipo de interes
                            days_nat = days_end-days_init                      
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : 0,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_end-days_init))}

                        payments.append(pay)
                        date_init = date_end
                        total_invoice -= payment['amount']
                    
                    days_init = (date_init - date_invoice).days
                    days_end = (date_payment - date_invoice).days
                    #Hacemos el proceso una vez mas tomando la fecha en que se va a liquidar el crédito siguiendo los mismos parametros

                    if  days_end <= 30:
                        days_nat = days_end-days_init
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                if payments_text != 'false':
                    date_init = date_invoice
                    date_end = ''
                    date_limit = datetime.strptime(credit.date_limit, '%Y-%m-%d')
                    days_limit = (date_limit - date_invoice).days
                    total_invoice = invoice.amount_total
                    pay = {}

                    payments_json = json.loads(payments_text)['content']
                    payments_array=[]
                    for pay in payments_json:
                        payments_array.append({'amount':pay['amount'],'date':pay['date']})

                    for payment in payments_array:
                        
                        #Por cada pago revisamos los intereses que generó
                        pay_date = payment['date']
                        date_end = datetime.strptime(payment['date'], '%Y-%m-%d')
                        days_init = (date_init - date_invoice).days
                        days_end = (date_end - date_invoice).days
                            
                        if date_init <= date_limit and date_end <= date_limit:
                            #C1 si el pago abarca un intervalo antes del día limite
                            days_int = (date_end-date_invoice).days
                            interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
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
                            pay = {'invoice' : invoice.number,
                                'total' : "{:,.2f}".format(total_invoice),
                                'payment_amount' : "{:,.2f}".format(payment['amount']),
                                'date' : pay_date,
                                'days' : days_end-days_init,
                                'days_nat' : days_nat,
                                'days_int' : 0,
                                'total_int' : 0,
                                'days_mo' : days_mo,
                                'total_mo' : "{:,.2f}".format(((total_invoice*(credit.interest_mo/100))/30)*(days_mo))}
                            
                        payments.append(pay)
                        date_init = date_end
                        total_invoice -= payment['amount']
                    
                    
                    date_end = date_payment
                    days_end = (date_end - date_invoice).days
                    days_init = (date_init - date_invoice).days
                            
                    #Hacemos un ultimo registro con el pago a realizar
                    if date_init <= date_limit and date_end <= date_limit:
                        days_int = (date_end-date_invoice).days
                        interest += ((total_invoice*(credit.interest/100))/30)*(days_end-days_init)
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        pay = {'invoice' : invoice.number,
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
                        interest = ((invoice.residual*(credit.interest/100))/30)*(days_int)
                    elif date_payment > date_limit:
                        days_int = days_limit
                        days_mo = days-days_limit
                        interest = ((invoice.residual*(credit.interest/100))/30)*(days_int)
                        interest_mo = ((invoice.residual*(credit.interest_mo/100))/30)*(days_mo)

            

            
            #Sumamos los totales de los intereses y la factura para determinar el pago final
            total_inv = invoice.residual+interest+interest_mo
            total += total_inv
            sum_invoices += invoice.residual
            sum_interest += interest + interest_mo
            #Se guarda un objeto con la información de la factura para mostrar el historial
            inv = {
                'number': invoice.number,
                'date': date_invoice.strftime("%d/%m/%Y"),
                'amount' : "{:,.2f}".format(invoice.residual),
                'date_payment' : date_payment.strftime("%d/%m/%Y"),
                'days_nat' : days_nat,
                'days_int' : days_int,
                'days_mo': days_mo,
                'interest': "{:,.2f}".format(interest),
                'interest_mo': "{:,.2f}".format(interest_mo),
                'total': "{:,.2f}".format(total_inv)
            }
            inv_data.append(inv)
        
        #Calculamos los intereses del seguro
        insurance_interest = 0
        insurance_interest_mo = 0
        date_init_in = datetime.strptime(credit.cycle.date_init, '%Y-%m-%d')
        date_limit_in = datetime.strptime(credit.date_limit, '%Y-%m-%d')
        if date_payment > date_init_in and date_payment < date_limit_in:
            days_interest_inurance = (date_payment - date_init_in).days
            insurance_interest = credit.insurance*((0.019/30)*days_interest_inurance)
        elif date_payment > date_init_in and date_payment >= date_limit_in:
            days_interest_inurance = (date_limit_in - date_init_in).days
            insurance_interest = credit.insurance*((0.019/30)*days_interest_inurance)
            days_interest_mo_inurance = (date_payment - date_limit_in).days
            insurance_interest_mo = credit.insurance*((0.038/30)*days_interest_mo_inurance)

        
        total += credit.insurance+insurance_interest+insurance_interest_mo
        
        #Objeto con los totales a pagar para mostrar en el informe
        data = {
            'cycle' : credit.cycle,
            'authorized' : "{:,.2f}".format(credit.authorized_amount),
            'interest' : "{:,.2f}".format(credit.interest),
            'sum_invoices' : "{:,.2f}".format(sum_invoices),
            'sum_interest' : "{:,.2f}".format(sum_interest),
            'total' : "{:,.2f}".format(total),
            'date' : date_payment.strftime("%d/%m/%Y"),
            'date_now' : (datetime.now()-timedelta(hours=5)).strftime("%d/%m/%Y %H:%M:%S"),
            'insurance' : "{:,.2f}".format(credit.insurance),
            'insurance_int': "{:,.2f}".format(insurance_interest),
            'insurance_mo': "{:,.2f}".format(insurance_interest_mo)
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

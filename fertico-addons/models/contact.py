from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def create(self, values):
        if values.get('parent_id'):
            if values.get('vat'):
                parent_vat= self.env['res.partner'].search([('id', '=', values.get('parent_id'))])
                if values['vat'] != parent_vat:
                    if values['vat'] != "XAXX010101000":
                        dup_ids = self.env['res.partner'].search([('vat', '=', values['vat'])])
                        if dup_ids:
                            raise Warning('RFC debe ser unico, este ya ha sido registrado!')
        else:
            if values.get('vat'):
                if values['vat']:
                    if values['vat'] != "XAXX010101000":
                        dup_ids = self.env['res.partner'].search([('vat', '=', values['vat'])])
                        if dup_ids:
                            raise Warning('RFC debe ser unico, este ya ha sido registrado!')
            
        contact = super(ResPartner, self).create(values)

        return contact

    @api.multi
    def write(self, values):

        if values.get('parent_id'):
            if values.get('vat'):
                parent_vat= self.env['res.partner'].search([('id', '=', values.get('parent_id'))])
                if values['vat'] != parent_vat:
                    if values['vat'] != "XAXX010101000":
                        dup_ids = self.env['res.partner'].search([('vat', '=', values['vat'])])
                        if dup_ids:
                            raise Warning('RFC debe ser unico, este ya ha sido registrado!')
        else:
            for contact in self:
                if contact.parent_id:
                    if values.get('vat'):
                        parent_vat= contact.env['res.partner'].search([('id', '=', contact.parent_id.id)]).vat
                        if values['vat'] != parent_vat:
                            if values['vat'] != "XAXX010101000":
                                dup_ids = contact.env['res.partner'].search([('vat', '=', values['vat'])])
                                if dup_ids:
                                    raise Warning('RFC debe ser unico, este ya ha sido registrado!')
                else:
                    if values.get('vat'):
                        if values['vat']:
                            if values['vat'] != "XAXX010101000":
                                dup_ids = contact.env['res.partner'].search([('vat', '=', values['vat'])])
                                if dup_ids:
                                    raise Warning('RFC debe ser unico, este ya ha sido registrado!')
            
        contact = super(ResPartner, self).write(values)

        return contact

    #=======================================agregar reporte de facturas en vista de contacto==========================
    # ================================================================================================================
    # ================================================================================================================  
    @api.depends('invoices')
    def _get_total(self):
        total_inv=0
        #recorremos todas las facturas relacionadas con el contacto
        for invoice in self.invoices:    
            if invoice.type == 'out_invoice':
                #si es una factura de venta sumamos la cantidad que se debe al total
                total_inv+=invoice.residual_signed
            elif invoice.type == 'in_invoice':
                #si es una factura de compra restamos lo que se debe al total
                total_inv-=invoice.residual_signed
        if total_inv >= 0:
            #si el total es positivo, se marca como saldo a favor de la empresa
            self.balance_client=False
        else:
            #si es negativo se marca como saldo a favor del cliente
            total_inv*=-1
            self.balance_client=True
        self.total=total_inv
    
    #creamos un campo onetomany para relacionar al contacto con las facturas, solo las que estan en estado abierto
    invoices = fields.One2many('account.invoice', 'partner_id', domain=[('state','=','open')])
    #dos campos calculados que nos daran el total que se adeuda y si es a favor del cliente
    total = fields.Float(compute="_get_total")
    balance_client = fields.Boolean(compute="_get_total")
    
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    '''
    @api.model
    def write(self, values):
        if values.vat:
            dup_ids = self.env['hr.employee'].search(['&','&', ('vat', '=', values.vat), ('id', '!=', values.id), ('id', 'not in', values.child_ids.ids)])
            if dup_ids:
                raise Warning('RFC debe ser unico, este ya ha sido registrado!')
        
        contact = super(ResPartner, self).write(values)
        return contact
        '''

    @api.model
    def create(self, values):
        print("============00",values['vat'])
        
        contact = super(ResPartner, self).create(values)

        '''if contact.vat != '':
            dup_ids = self.env['res.partner'].search([('vat', '=', contact.vat)])
            if dup_ids:
                raise Warning('RFC debe ser unico, este ya ha sido registrado!')
        else:
            print("entrooooooooooooooooooo aqui")
        '''
        return contact
        
        
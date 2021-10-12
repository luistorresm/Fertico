from odoo import models, fields, api
import xlrd
import tempfile
import binascii
from odoo.exceptions import UserError

class PricelistLoadXls(models.TransientModel):

    _name='pricelist.load.xls'

    excel_file = fields.Binary(string='Excel File')

    
    def import_pricelist(self):
        #read the xls file in the sheet, for obtain pricelist
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.excel_file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_index(0)

        #load the data in an array "data"
        data=[]
        for row_no in range(sheet.nrows):
            
            if row_no == 0:
                r_data=['']
                col_data=[]
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                for col, row_line in enumerate(line):
                    if row_line != '':
                        pricelist = self.env['product.pricelist'].search([('name','=',row_line.decode("utf-8"))], limit=1)
                        if pricelist:
                            r_data.append(pricelist)
                            col_data.append(col)
                        else:
                            msg = 'La lista de precio ' + row_line.decode("utf-8") + ' no se encuentra disponible'
                            raise UserError(msg)

                data.append(r_data)
            
            if row_no > 2:
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if(line[0]!=''):
                    product = self.env['product.template'].search([('default_code','=',line[0].decode("utf-8"))], limit = 1)
                    if product:
                        r_data=[product]
                        for col_d in col_data:
                            r_data.append(line[col_d])
                        
                        data.append(r_data)
                    else:
                        msg = 'El producto ' + line[0].decode("utf-8") + ' ' + line[1].decode("utf-8") + ' no se encuentra disponible'
                        raise UserError(msg)


        #add the new data
        for col_dl, data_line in enumerate(data[0]):
            for row_dr, data_row in enumerate(data): 
                if col_dl > 0 and row_dr:
                    price = self.env['product.pricelist.item'].create({
                                    'applied_on': '1_product',
                                    'product_tmpl_id': data[row_dr][0].id,
                                    'min_quantity': 1,
                                    'compute_price': 'fixed',
                                    'fixed_price': data[row_dr][col_dl]
                                })
                    
                    data[0][col_dl].write({'item_ids':[(4, price.id)]})
                
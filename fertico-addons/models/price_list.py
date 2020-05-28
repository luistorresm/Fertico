from odoo import models, fields, api
import xlrd
import tempfile
import binascii

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
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                r_data=['',line[4].decode("utf-8"),line[6].decode("utf-8"),line[8].decode("utf-8")]
                data.append(r_data)
            if row_no > 2:
                line = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                if(line[0]!=''):
                    cred=''
                    cont=''
                    dist=''

                    if line[4]!='':
                        cred=float(line[4])
                    if line[6]!='':
                        cont=float(line[6])
                    if line[8]!='':
                        dist=float(line[8])
                    
                    r_data=[line[0].decode("utf-8"),cred,cont,dist]
                    data.append(r_data)


        #remove the current pricelis
        
        cred_pl=self.env['product.pricelist'].search([('name','=',data[0][1])])
        for item in cred_pl.item_ids:
            cred_pl.item_ids=[(2,item.id)]

        cont_pl=self.env['product.pricelist'].search([('name','=',data[0][2])])
        for item in cont_pl.item_ids:
            cont_pl.item_ids=[(2,item.id)]

        dist_pl=self.env['product.pricelist'].search([('name','=',data[0][3])])
        for item in dist_pl.item_ids:
            dist_pl.item_ids=[(2,item.id)]

        #add the new data
        for r, row in enumerate(data):
            if r > 0:
                
                prod=self.env['product.template'].search([('default_code','=',row[0])])

                if row[1] != '':

                    record_cred = self.env['product.pricelist.item'].create({
                                'applied_on': '1_product',
                                'product_tmpl_id': prod.id,
                                'min_quantity': 1,
                                'compute_price': 'fixed',
                                'fixed_price': row[1]
                            })
                            
                    cred_pl.write({'item_ids':[(4, record_cred.id)]})

                if row[2] != '':

                    record_cont = self.env['product.pricelist.item'].create({
                                'applied_on': '1_product',
                                'product_tmpl_id': prod.id,
                                'min_quantity': 1,
                                'compute_price': 'fixed',
                                'fixed_price': row[2]
                            })

                    cont_pl.write({'item_ids':[(4, record_cont.id)]})

                if row[3] != '':

                    record_dist = self.env['product.pricelist.item'].create({
                                'applied_on': '1_product',
                                'product_tmpl_id': prod.id,
                                'min_quantity': 1,
                                'compute_price': 'fixed',
                                'fixed_price': row[3]
                            })
                    
                    dist_pl.write({'item_ids':[(4, record_dist.id)]})
                
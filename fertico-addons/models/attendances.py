from odoo import models, fields, api
import xlrd
import tempfile
import binascii
from datetime import datetime, timedelta
from pytz import timezone



class Employee(models.Model):
    _inherit = "hr.employee"

    schedule_ids=fields.Many2many('hr.schedule','employee_id',string="Schedule")

class Schedule(models.Model):
    _name="hr.schedule"

    name=fields.Char(string="Name", required=True)
    check_in=fields.Float(string="Check-In")
    check_out=fields.Float(string="Check-Out")
    employee_id=fields.Many2many('hr.employee','schedule_ids')

class HrAttendance(models.Model):
    _inherit="hr.attendance"

    retards=fields.Float(string="Retards")
    extras=fields.Float(string="Extras")

class AttendancesXls(models.TransientModel):
    
    _name='attendance.load.xls'
    excel_file = fields.Binary(string='Excel File')

    def convert_TZ_UTC(self, TZ_datetime):
        fmt = "%Y-%m-%d %H:%M:%S"
        # Current time in UTC
        now_utc = datetime.now(timezone('UTC'))
        # Convert to current user time zone
        now_timezone = now_utc.astimezone(timezone(self.env.user.tz))
        UTC_OFFSET_TIMEDELTA = datetime.strptime(now_utc.strftime(fmt), fmt) - datetime.strptime(now_timezone.strftime(fmt), fmt)
        local_datetime = datetime.strptime(TZ_datetime, fmt)
        result_utc_datetime = local_datetime + UTC_OFFSET_TIMEDELTA
        return result_utc_datetime.strftime(fmt)

    def convertSchedule(self, date):
        now = datetime.now()
        date=now.strftime("%Y-%m-%d")+" "+str(timedelta(hours=date))
        str_date=self.convert_TZ_UTC(date)[-8:]
        time_check=datetime.strptime(str_date, '%H:%M:%S')
        check=timedelta(hours=time_check.hour, minutes=time_check.minute, seconds=time_check.second)
        return check

    def convertToTimeDelta(self, time):
        hour_aux=time[-8:]
        t=datetime.strptime(hour_aux,"%H:%M:%S")
        hour=timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
        return hour

    def difHours(self,h1,h2):
        dif = h1 - h2
        dif_hours = float(dif.seconds)/3600
        return dif_hours


    
    
    @api.multi
    def load_attendance(self):
        """This method read a xls file and take the data to add records 
        for register the attendances of the employees"""
        
        #read the xls file in the sheet 'Reporte de Asistencias'
        fp = tempfile.NamedTemporaryFile(suffix=".xlsx")
        fp.write(binascii.a2b_base64(self.excel_file))
        fp.seek(0)
        workbook = xlrd.open_workbook(fp.name)
        sheet = workbook.sheet_by_name("Reporte de Asistencia")
        
        #load the data in an array "data"
        data=[]
        for row_no in range(sheet.nrows):
            if row_no <= 0:
                fields = map(lambda row:row.value.encode('utf-8'), sheet.row(row_no))
            else:
                row_data=[]
                lines = list(map(lambda row:isinstance(row.value, str) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                
                if lines[0]=='1.0':
                    row_data=lines
                elif lines[0]==b'ID:':
                    for line in lines:
                        if line != '':
                            row_data.append(line.decode("utf-8"))
                else:
                    for line in lines:
                        if line != '':
                            row_data.append(line.decode("utf-8"))
                        else:
                            row_data.append(line)
                
                if len(row_data)==0:
                    row_data.append(False)
                data.append(row_data)
        
        #add only the necesary data in a new array "new_data", in each row the employee information and the asistance data
        #array with the period
        new_data=[]
        period=[]
        n_d=0
        for d in data:
            if d[0]=='1.0':
                for i in d:
                    if i != '':
                        period.append(float(i))

            if n_d!=len(data):
                if d[0]=='ID:':
                    if n_d!=(len(data)-1):     
                        new_data.append(data[n_d]+data[(n_d+1)])
                    else:
                        array_aux=[]
                        for n in data[(n_d-1)]:
                            array_aux.append('')
                        new_data.append(data[n_d]+array_aux)
                n_d+=1
        
        #create the init date from data array
        date_init=data[1][6][0]+data[1][6][1]+data[1][6][2]+data[1][6][3]+data[1][6][4]+data[1][6][5]+data[1][6][6]+data[1][6][7]+data[1][6][8]+data[1][6][9]
        date_object = datetime.strptime(date_init, '%Y-%m-%d').date()
        
        #new array with the period integer
        period_int=[]
        for p in period:
            period_int.append(round(p))
        
        #separate the dates in arrays and join the time to the date
        for nd in new_data:
            
            for n in period_int:
                if nd[n+5] != '':
                    check=[]
                    array_check=''
                    count=0
                    for d in nd[n+5]:
                        if count==0:
                            date_add=date_object+timedelta(days=(n-1))
                            array_check+=str(date_add.day)+'/'+str(date_add.month)+'/'+str(date_add.year)+' '
                        count+=1
                        array_check+=d
                        if count==5:
                            array_check+=':00'
                            datetime_object=str(datetime.strptime(array_check, '%d/%m/%Y %H:%M:%S'))
                            check.append(datetime_object)
                            count=0
                            array_check=''
                    
                    nd[n+5]=check
        
        #register the records from the array data
        for n in period_int:

            for nd in new_data:

                employee = self.env['hr.employee'].search([('name','=',nd[3])])
                schedules_ids = employee.schedule_ids
                schedules=[]
                for sc in schedules_ids:
                    schedules.append([timedelta(hours=sc.check_in),timedelta(hours=sc.check_out)])
                    
                
                if nd[n+5]!='':
                    if len(nd[n+5])==1:
                        
                        vals={
                            'employee_id' : employee.id,
                            'check_in' : self.convert_TZ_UTC(str(nd[n+5][0])),
                            'check_out' : self.convert_TZ_UTC(str(nd[n+5][0]))
                        }
                        record = self.env['hr.attendance'].create(vals)
                    
                    elif len(nd[n+5])==2:
                        hour=self.convertToTimeDelta(nd[n+5][0])
                        hour2=self.convertToTimeDelta(nd[n+5][1])
                        
                        retard=0
                        extra=0
                        
                
                        if len(schedules) > 0:
                            print(hour, " ", schedules[0][0])
                            print(hour2, " ", schedules[0][1])
                            if hour > schedules[0][0]:
                                retard=self.difHours(hour,schedules[0][0])
                            if hour2 > schedules[0][1]:  
                                extra=self.difHours(hour2,schedules[0][1])

                        vals={
                            'employee_id' : employee.id,
                            'check_in' : self.convert_TZ_UTC(str(nd[n+5][0])),
                            'check_out' : self.convert_TZ_UTC(str(nd[n+5][1])),
                            'retards' : retard,
                            'extras' : extra
                        }
                        record = self.env['hr.attendance'].create(vals)
                    elif len(nd[n+5])==3:
                        hour_aux=nd[n+5][1][-8:]
                        if int(hour_aux[:2])<15:
                            
                            hour=self.convertToTimeDelta(nd[n+5][0])
                            hour2=self.convertToTimeDelta(nd[n+5][1])
                            
                            retard=0
                            extra=0
                            
                            if len(schedules) > 0:
                                if hour > schedules[0][0]:
                                    retard=self.difHours(hour,schedules[0][0])
                                if hour2 > schedules[0][1]:  
                                    extra=self.difHours(hour2,schedules[0][1])
                            
                            vals={
                                'employee_id' : employee.id,
                                'check_in' : self.convert_TZ_UTC(str(nd[n+5][0])),
                                'check_out' : self.convert_TZ_UTC(str(nd[n+5][1])),
                                'retards' : retard,
                                'extras' : extra
                            }
                            record = self.env['hr.attendance'].create(vals)
                            vals={
                                'employee_id' : employee.id,
                                'check_in' : self.convert_TZ_UTC(str(nd[n+5][2])),
                                'check_out' : self.convert_TZ_UTC(str(nd[n+5][2]))
                            }
                            record = self.env['hr.attendance'].create(vals)
                        else:
                            
                            hour=self.convertToTimeDelta(nd[n+5][1])
                            hour2=self.convertToTimeDelta(nd[n+5][2])
                            
                            retard=0
                            extra=0
                            
                           
                            if len(schedules) > 1:
                                if hour > schedules[1][0]:  
                                    retard=self.difHours(hour,schedules[1][0])
                                if hour2 > schedules[1][1]:
                                    extra=self.difHours(hour2,schedules[1][1])
                            vals={
                                'employee_id' : employee.id,
                                'check_in' : self.convert_TZ_UTC(str(nd[n+5][0])),
                                'check_out' : self.convert_TZ_UTC(str(nd[n+5][0]))
                            }
                            record = self.env['hr.attendance'].create(vals)
                            vals={
                                'employee_id' : employee.id,
                                'check_in' : self.convert_TZ_UTC(str(nd[n+5][1])),
                                'check_out' : self.convert_TZ_UTC(str(nd[n+5][2])),
                                'retards' : retard,
                                'extras' : extra
                            }
                            record = self.env['hr.attendance'].create(vals)
                    elif len(nd[n+5])==4:

                        hour=self.convertToTimeDelta(nd[n+5][0])
                        hour2=self.convertToTimeDelta(nd[n+5][1])
                        hour3=self.convertToTimeDelta(nd[n+5][2])
                        hour4=self.convertToTimeDelta(nd[n+5][3])
                        
                        retard=0
                        extra=0
                        retard2=0
                        extra2=0

                        if len(schedules) > 0:
                            if hour > schedules[0][0]:
                                retard=self.difHours(hour,schedules[0][0])
                            if hour2 > schedules[0][1]:
                                extra=self.difHours(hour2,schedules[0][1])    
                        if len(schedules) > 1:
                            if hour3 > schedules[1][0]:  
                                retard2=self.difHours(hour3,schedules[1][0])
                            if hour4 > schedules[1][1]:
                                extra2=self.difHours(hour4,schedules[1][1])

                        vals={
                            'employee_id' : employee.id,
                            'check_in' : self.convert_TZ_UTC(str(nd[n+5][0])),
                            'check_out' : self.convert_TZ_UTC(str(nd[n+5][1])),
                            'retards' : retard,
                            'extras' : extra
                        }
                        record = self.env['hr.attendance'].create(vals)
                        vals={
                            'employee_id' : employee.id,
                            'check_in' : self.convert_TZ_UTC(str(nd[n+5][2])),
                            'check_out' : self.convert_TZ_UTC(str(nd[n+5][3])),
                            'retards' : retard2,
                            'extras' : extra2
                        }
                        record = self.env['hr.attendance'].create(vals)
        







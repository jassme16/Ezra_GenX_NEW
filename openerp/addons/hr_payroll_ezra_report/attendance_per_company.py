from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from openerp.addons.hr_payroll_ezra.parameters import constants

import datetime
import xlwt
import xlrd
from xlutils.copy import copy
from xlutils.styles import Styles
from cStringIO import StringIO
import base64

MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')]

MONTH_QUARTER_SELECTION = [
    (1, '1st Half'),
    (2, '2nd Half')
]

ATTENDANCE_RIGHTS_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Post to Payroll')
]


class AttendanceCompanyMain(models.Model):
    _name = 'hr.attendance.main.company'
    _description = 'Attendance Main per Company'

    @api.one
    def _getFilename(self):
        self.filename = '%s.xls' % self.name

    name = fields.Char('Name')

    company_id = fields.Many2one('res.customers.main', 'Company', required = True)

    month_of = fields.Selection(constants.MONTH_SELECTION, 'for the Month of', reguired = True)
    month_quarter = fields.Selection(MONTH_QUARTER_SELECTION, required = True)
    year = fields.Integer('Year', default = constants.YEAR_NOW)
    attendance_status = fields.Selection(ATTENDANCE_RIGHTS_STATUS, required = True, default = 'draft')
    attendance_detail_ids = fields.One2many('hr.attendance.detail.company','attendance_company_id', readonly=False,copy=False)
    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    attendance_file = fields.Binary('Excel File')

    @api.one
    def generateReportData(self):
        model_hr_attendance_detail_company = self.env['hr.attendance.detail.company'].search([('attendance_company_id','=', self.id)])
        model_hr_attendance_detail_company.unlink()
        dict_branches = []
        for branches in self.company_id.main_cust_id:
           dict_branches.append(branches.customer_info.id)


        model_hr_attendance_main = self.env['hr.attendance.main'].search([('month_of', '=', self.month_of),
                                                                          ('month_quarter', '=', self.month_quarter),
                                                                          ('attendance_status', '=', self.attendance_status),
                                                                          ('assign_projects', 'in', dict_branches)])
        self.name = self.company_id.name
        for hr_attendance_main in model_hr_attendance_main:
            int_year = datetime.datetime.strptime(str(self.year) + '-' + str(hr_attendance_main.month_of) + '-01', '%Y-%m-%d').year
            if int_year == self.year:
                model_hr_attendance_detail_company = self.env['hr.attendance.detail.company']
                model_hr_attendance_detail_company.create({
                    'attendance_company_id':self.id,
                    'assign_projects': hr_attendance_main.assign_projects.id,
                    'hr_payroll_attendance_id': hr_attendance_main.id
                })
        self.generateExcelFile()

    def generateExcelFile(self):
        model_hr_attendance_detail_company = self.env['hr.attendance.detail.company'].search([('attendance_company_id','=', self.id)])
        str_dir = constants.GenXUtils.get_data_dir_excel_template
        int_rowindex = 6

        workbook_xlrd = xlrd.open_workbook(str_dir + 'Attendance 2.xls', formatting_info=True)

        workbook = copy(workbook_xlrd)

        sheet_xlrd = workbook_xlrd.sheet_by_index(0)
        sheet = workbook.get_sheet(0)

        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21,  196, 215, 155)
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_LEFT
        alignment.vert = xlwt.Alignment.VERT_CENTER
        alignment.Wrap = 1
        job_background_color = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
        job_background_color.alignment = alignment
        job_background_color.alignment.wrap = 1

        #border 1
        border = xlwt.Borders()
        border.bottom = xlwt.Borders.THIN
        border.top = xlwt.Borders.THIN
        border.left = xlwt.Borders.THIN
        border.right = xlwt.Borders.THIN
        job_background_color.borders = border
        job_background_color.font.bold =True

        for hr_attendance_detail_main in model_hr_attendance_detail_company:

            #Title
            sheet.write(1,2,self.company_id.name)
            sheet.write(2,2,str(hr_attendance_detail_main.hr_payroll_attendance_id.schedule_datefrom) + ' - ' + str(hr_attendance_detail_main.hr_payroll_attendance_id.schedule_dateto))

            model_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',hr_attendance_detail_main.hr_payroll_attendance_id.id)])
            model_attendance = model_attendances.sorted(key=lambda r: r.employee_sequence)
            sheet.write_merge(int_rowindex,int_rowindex,0,15,hr_attendance_detail_main.assign_projects.name,job_background_color)
            int_rowindex +=1
            if len(model_attendance) > 0:
                styleColumns =xlwt.XFStyle()
                border = xlwt.Borders()
                border.bottom = xlwt.Borders.THIN
                border.top = xlwt.Borders.THIN
                border.left = xlwt.Borders.THIN
                border.right = xlwt.Borders.THIN
                styleColumns.borders = border

                for employee in model_attendance:
                    fontData = xlwt.Font()
                    if employee.has_a_reliever == True:
                        fontData.colour_index = 0x0A
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,0,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)
                    elif employee.is_reliever == True:
                        fontData.colour_index = 0x0C
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,0,2, '**' + employee.employee_reliever.last_name + ',' + employee.employee_reliever.first_name,styleColumns)
                    else:
                        fontData.colour_index = 0x08
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,0,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)

                    sheet.write(int_rowindex,3,employee.regular_days_work,styleColumns)
                    sheet.write(int_rowindex,4,employee.absent,styleColumns)
                    sheet.write(int_rowindex,5,employee.tardiness,styleColumns)
                    sheet.write(int_rowindex,6,employee.straight_duty,styleColumns)
                    sheet.write(int_rowindex,7,employee.night_differential,styleColumns)
                    sheet.write(int_rowindex,8,employee.regular_overtime,styleColumns )
                    sheet.write(int_rowindex,9,employee.rest_day_work,styleColumns)
                    sheet.write(int_rowindex,10,employee.restday_overtime,styleColumns)
                    sheet.write(int_rowindex,11,employee.special_day_work,styleColumns)
                    sheet.write(int_rowindex,12,employee.special_overtime,styleColumns)
                    sheet.write(int_rowindex,13,employee.legal_holiday_day,styleColumns)
                    sheet.write(int_rowindex,14,employee.holiday_day_work,styleColumns)
                    sheet.write(int_rowindex,15,employee.holiday_overtime,styleColumns)
                    int_rowindex +=1
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.attendance_file = byte_arr

class AttendanceCompanyMain(models.Model):
    _name = 'hr.attendance.detail.company'
    _description = 'Attendance detail per Company'
    _order = 'assign_projects'
    attendance_company_id = fields.Many2one('hr.attendance.main.company')
    assign_projects = fields.Many2one('res.partner', 'Per Project')
    hr_payroll_attendance_id = fields.Many2one('hr.attendance.main')

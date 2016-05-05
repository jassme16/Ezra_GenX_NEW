from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp import models, fields, api
from datetime import datetime
from openerp import tools

from cStringIO import StringIO
import xlwt
import base64
import xlrd
from xlutils.copy import copy
from xlutils.styles import Styles

#import openpyxl


#TODO : WORKAROUND XLRD MUST BE CHECK IF JUST CPYING THE PACKAGE WILL BE USED IN GENERATION OF EXCEL PACKAGE

class AlphalistConfiguration(models.Model):
    _name = 'payroll.alphalist.config'
    _description = 'Alphalist Configuration'
    # Constant Code
    # THMONTH = 85000

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required =True)
    description = fields.Text('Description', required = True)
    amount = fields.Float('Amount', digits=(18,2))

    @api.model
    def GetAmount(self, code = '',pcurr_amount = 0.00):
        configs = self.env['payroll.alphalist.config'].search([])
        for config in configs:
            if config.code == code:
                return config.amount
        return 0


class AnnualTaxTable(models.Model):
    _name = 'payroll.annual.tax.table'
    _description = 'Annual Tax Table'
    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    amount_rangefrom = fields.Float('Range from', digits=(18,2), required=True)
    amount_rangeto = fields.Float('Range To', digits=(18,2), required=True)
    tax_amount = fields.Float('Tax', digits=(18,2), required=True)
    rate_in_excess = fields.Float('Rate in Excess', digits=(18,2), required=True)

    @api.model
    @api.multi
    def getAnnualTaxAmount(self, amount = 0):
        tax_infos = self.env['payroll.annual.tax.table'].search([])
        #print(self.ids)
        for tax_info in tax_infos:
            if amount >= tax_info.amount_rangefrom and amount <= tax_info.amount_rangeto:

                amount_inexcess = amount - tax_info.amount_rangefrom
                amount_inexcess = amount_inexcess * (tax_info.rate_in_excess / constants.ONE_HUNDRED_PERCENT)
                print(amount_inexcess)
                print(tax_info.tax_amount)
                return round(amount_inexcess + tax_info.tax_amount,2)
        return 0


class AlphalistMain(models.Model):
    _name = 'payroll.alphalist.main'
    _description = 'Alphalist main file'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = '%s.xls' % self.name

    name = fields.Char('Alphalist name', required =True)
    payroll_date_from = fields.Date('Payroll Date From', required=True)
    payroll_date_to = fields.Date('Payroll Date To', required=True)
    annual_for_the_year = fields.Integer('For the Year', required = True , default =constants.YEAR_NOW)
    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    alphalist_file = fields.Binary('Excel File')

    employee = fields.Many2one('hr.employee', 'Search Employee')
    state = fields.Selection(constants.STATE_ALPHA, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')
    alphalist_detail_id = fields.One2many('payroll.alphalist.detail', 'alphalist_main_id', readonly=False, copy=False)
    alphalist_mwe_detail_id = fields.One2many('payroll.alphalist7_5.detail', 'alphalist_mwe_detail_id', readonly=False, copy=False)


    @api.one
    def generateExcel(self, main_id = 0):
        model_alphalist_73s = self.env['payroll.alphalist.detail'].search([('alphalist_main_id','=',main_id),
                                                                           ('with_previous_employer','=',False)])
        model_alphalist_73 = model_alphalist_73s.sorted(key=lambda r: r.last_name)

        model_alphalist_74s = self.env['payroll.alphalist.detail'].search([('alphalist_main_id','=',main_id),
                                                                           ('with_previous_employer','=',True)])
        model_alphalist_74 = model_alphalist_73s.sorted(key=lambda r: r.last_name)

        model_alphalist_75s = self.env['payroll.alphalist7_5.detail'].search([('alphalist_mwe_detail_id','=',main_id)])
        model_alphalist_75 = model_alphalist_75s.sorted(key=lambda r: r.last_name)
        str_dir = constants.GenXUtils.get_data_dir_excel_template

        workbook_xlrd = xlrd.open_workbook(str_dir + 'SCHEDULE 7.5.xls', formatting_info=True)
        workbook = copy(workbook_xlrd)

        #Schedule 7.3
        if len(model_alphalist_73) > 0:
            styleColumns =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border
            sheet_xlrd = workbook_xlrd.sheet_by_index(2)
            sheet = workbook.get_sheet(2)
            int_rowindex = 6
            int_sequence = 1
            for employee in model_alphalist_73:
                if len(employee.last_name) > 0 and len(employee.first_name) > 0:
                    sheet.write(int_rowindex ,0, int_sequence,styleColumns)
                    sheet.write(int_rowindex,1, employee.tin_no,styleColumns)
                    sheet.write(int_rowindex,2, employee.last_name,styleColumns)
                    sheet.write(int_rowindex,3, employee.first_name,styleColumns)
                    sheet.write(int_rowindex,4, employee.middle_name,styleColumns)
                    sheet.write(int_rowindex,5, employee.non_tax_gross_compensation_income,styleColumns)
                    sheet.write(int_rowindex,6, employee.non_tax_thirteenth_month + employee.non_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,7, employee.non_tax_de_minimis_benefits,styleColumns)
                    sheet.write(int_rowindex,8, employee.non_tax_gov_contributions,styleColumns)
                    sheet.write(int_rowindex,9, employee.non_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,10, employee.non_tax_total,styleColumns)
                    sheet.write(int_rowindex,11, employee.tax_basic_pay,styleColumns)
                    sheet.write(int_rowindex,12, employee.tax_thirteenth_month + employee.tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,13, employee.tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,14, employee.tax_total_compensation_income,styleColumns)
                    sheet.write(int_rowindex,15, employee.exemption_code,styleColumns)
                    sheet.write(int_rowindex,16, employee.exemption_amount,styleColumns)
                    sheet.write(int_rowindex,17, employee.paid_health_insurance + employee.prev_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,18, employee.net_taxable_comp_income,styleColumns)
                    sheet.write(int_rowindex,19, employee.tax_due,styleColumns)
                    sheet.write(int_rowindex,20, employee.tax_withheld ,styleColumns)
                    sheet.write(int_rowindex,21, employee.paid_amount_december,styleColumns)
                    sheet.write(int_rowindex,22, employee.overwithheld_tax,styleColumns)
                    sheet.write(int_rowindex,23, employee.amount_withheld_adjusted,styleColumns)
                    sheet.write(int_rowindex,24, employee.filed,styleColumns)
                    int_sequence += 1
                    int_rowindex += 1

            for intColumn in range(0,25):
                sheet.write(int_rowindex,intColumn,sheet_xlrd.cell(7,intColumn).value,styleColumns)
        #Schedule 7.4
        if len(model_alphalist_74) > 0:
            styleColumns =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border
            sheet_xlrd = workbook_xlrd.sheet_by_index(3)
            sheet = workbook.get_sheet(3)
            int_rowindex = 8
            int_sequence = 1
            for employee in model_alphalist_74:
                if len(employee.last_name) > 0 and len(employee.first_name) > 0:
                    sheet.write(int_rowindex ,0, int_sequence,styleColumns)
                    sheet.write(int_rowindex,1, employee.tin_no,styleColumns)
                    sheet.write(int_rowindex,2, employee.last_name,styleColumns)
                    sheet.write(int_rowindex,3, employee.first_name,styleColumns)
                    sheet.write(int_rowindex,4, employee.middle_name,styleColumns)

                    sheet.write(int_rowindex,5, employee.non_tax_gross_compensation_income,styleColumns)
                    sheet.write(int_rowindex,6, employee.prev_non_tax_thirteenth_month + employee.non_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,7, employee.prev_non_tax_de_minimis_benefits,styleColumns)
                    sheet.write(int_rowindex,8, employee.prev_non_tax_gov_contributions,styleColumns)
                    sheet.write(int_rowindex,9, employee.prev_non_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,10, employee.prev_non_tax_total,styleColumns)
                    sheet.write(int_rowindex,11, employee.prev_tax_basic_pay,styleColumns)
                    sheet.write(int_rowindex,12, employee.prev_tax_thirteenth_month + employee.prev_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,13, employee.prev_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,14, employee.prev_tax_total_compensation_income,styleColumns)

                    sheet.write(int_rowindex,15, employee.non_tax_thirteenth_month + employee.non_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,16, employee.non_tax_de_minimis_benefits,styleColumns)
                    sheet.write(int_rowindex,17, employee.non_tax_gov_contributions,styleColumns)
                    sheet.write(int_rowindex,18, employee.non_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,19, employee.non_tax_total,styleColumns)
                    sheet.write(int_rowindex,20, employee.tax_basic_pay,styleColumns)
                    sheet.write(int_rowindex,21, employee.tax_thirteenth_month + employee.tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,22, employee.tax_other_compensation,styleColumns)

                    sheet.write(int_rowindex,23, employee.tax_total_compensation_income,styleColumns)
                    sheet.write(int_rowindex,24, employee.prev_tax_total_compensation_income,styleColumns)



                    sheet.write(int_rowindex,25, employee.exemption_code,styleColumns)
                    sheet.write(int_rowindex,26, employee.exemption_amount,styleColumns)

                    sheet.write(int_rowindex,27, employee.paid_health_insurance,styleColumns)
                    sheet.write(int_rowindex,28, employee.net_taxable_comp_income,styleColumns)
                    sheet.write(int_rowindex,29, employee.tax_due,styleColumns)
                    sheet.write(int_rowindex,30, employee.tax_withheld ,styleColumns)
                    sheet.write(int_rowindex,31, employee.prev_tax_withheld ,styleColumns)

                    sheet.write(int_rowindex,32, employee.paid_amount_december,styleColumns)
                    sheet.write(int_rowindex,33, employee.overwithheld_tax,styleColumns)
                    sheet.write(int_rowindex,34, employee.amount_withheld_adjusted,styleColumns)
                    int_sequence += 1
                    int_rowindex += 1

            for intColumn in range(0,35):
                sheet.write(int_rowindex,intColumn,sheet_xlrd.cell(7,intColumn).value,styleColumns)



        #Schedule 7.5
        if len(model_alphalist_75) > 0:
            styleColumns =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border

            #workbook_xlrd = xlrd.open_workbook(str_dir + 'SCHEDULE 7.5.xls', formatting_info=True)
            sheet_xlrd = workbook_xlrd.sheet_by_index(4)
            #workbook = copy(workbook_xlrd)

            sheet = workbook.get_sheet(4)
            int_rowindex = 6
            int_sequence = 1
            for employee in model_alphalist_75:
                if len(employee.last_name) > 0 and len(employee.first_name) > 0:
                    sheet.write(int_rowindex ,0, int_sequence,styleColumns)
                    sheet.write(int_rowindex,1, employee.tin_no,styleColumns)
                    sheet.write(int_rowindex,2, employee.last_name,styleColumns)
                    sheet.write(int_rowindex,3, employee.first_name,styleColumns)
                    sheet.write(int_rowindex,4, employee.middle_name,styleColumns)
                    sheet.write(int_rowindex,5, employee.region_assigned.code,styleColumns)
                    sheet.write(int_rowindex,6, employee.prev_total_compensation_income,styleColumns)
                    sheet.write(int_rowindex,7, employee.prev_basic_pay_peryear,styleColumns)
                    sheet.write(int_rowindex,8, employee.prev_non_tax_holiday_pay,styleColumns)
                    sheet.write(int_rowindex,9, employee.prev_non_tax_overtime_pay,styleColumns)
                    sheet.write(int_rowindex,10, employee.prev_non_tax_nightshiff_pay,styleColumns)
                    sheet.write(int_rowindex,11, employee.prev_non_tax_hazard_pay,styleColumns)
                    sheet.write(int_rowindex,12, employee.prev_non_tax_thirteenth_month + employee.prev_non_tax_other_benefits ,styleColumns)
                    sheet.write(int_rowindex,13, employee.prev_non_tax_deminimis_pay,styleColumns)
                    sheet.write(int_rowindex,14, employee.prev_non_tax_gov_contrib,styleColumns)
                    sheet.write(int_rowindex,15, employee.prev_non_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,16, employee.prev_non_tax_total,styleColumns)
                    sheet.write(int_rowindex,17, employee.prev_tax_thirteenth_month + employee.prev_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,18, employee.prev_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,19, employee.prev_tax_total,styleColumns)
                    sheet.write(int_rowindex,20, employee.date_of_employment_from ,styleColumns)
                    sheet.write(int_rowindex,21, employee.date_of_employment_to,styleColumns)

                    sheet.write(int_rowindex,22, employee.total_compensation_income,styleColumns)
                    sheet.write(int_rowindex,23, employee.basic_pay_perday,styleColumns)
                    sheet.write(int_rowindex,24, employee.basic_pay_permonth,styleColumns)
                    sheet.write(int_rowindex,25, employee.basic_pay_peryear,styleColumns)
                    sheet.write(int_rowindex,26, employee.factor_used,styleColumns)
                    sheet.write(int_rowindex,27, employee.non_tax_holiday_pay,styleColumns)
                    sheet.write(int_rowindex,28, employee.non_tax_overtime_pay,styleColumns)
                    sheet.write(int_rowindex,29, employee.non_tax_nightshiff_pay,styleColumns)
                    sheet.write(int_rowindex,30, employee.non_tax_hazard_pay,styleColumns)
                    sheet.write(int_rowindex,31, employee.non_tax_thirteenth_month + employee.non_tax_other_benefits,styleColumns)
                    sheet.write(int_rowindex,32, employee.non_tax_deminimis_pay,styleColumns)
                    sheet.write(int_rowindex,33, employee.non_tax_gov_contrib,styleColumns)
                    sheet.write(int_rowindex,34, employee.non_tax_other_compensation,styleColumns)
                    sheet.write(int_rowindex,35, employee.tax_thirteenth_month + employee.tax_other_benefits ,styleColumns)
                    sheet.write(int_rowindex,36, employee.tax_other_compensation ,styleColumns)
                    sheet.write(int_rowindex,37, employee.tax_total ,styleColumns)

                    sheet.write(int_rowindex,38, employee.total_taxable_comp_income,styleColumns)
                    sheet.write(int_rowindex,39, employee.exemption_code,styleColumns)
                    sheet.write(int_rowindex,40, employee.exemption_amount,styleColumns)
                    sheet.write(int_rowindex,41, employee.paid_health_insurance,styleColumns)
                    sheet.write(int_rowindex,42, employee.net_taxable_comp_income,styleColumns)
                    sheet.write(int_rowindex,43, employee.tax_due,styleColumns)
                    sheet.write(int_rowindex,44, employee.tax_withheld,styleColumns)
                    sheet.write(int_rowindex,45, employee.prev_tax_withheld,styleColumns)
                    sheet.write(int_rowindex,46, employee.paid_amount_december,styleColumns)
                    sheet.write(int_rowindex,47, employee.paid_amount_december,styleColumns)
                    sheet.write(int_rowindex,48, employee.amount_withheld_adjusted,styleColumns)
                    int_sequence += 1
                    int_rowindex += 1
            for intColumn in range(0,49):
                sheet.write(int_rowindex,intColumn,sheet_xlrd.cell(7,intColumn).value,styleColumns)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.alphalist_file = byte_arr

    @api.one
    def generateAlphalist(self):
        model_employee = self.env['hr.employee'].search([]) #.search([('id','=',5717)])
        model_alphalist_config = self.env['payroll.alphalist.config']

        for employee in model_employee:
            print(employee.id)

            if len(employee.contract_id) > 0:
                if employee.contract_id.daily_rate <= model_alphalist_config.GetAmount('MWE'):
                    if len(self.alphalist_mwe_detail_id.search([('employee_id', '=', employee.id),
                                                                ('alphalist_mwe_detail_id', '=', self.id)])) == 0:
                        self.alphalist_mwe_detail_id.create({
                            'employee_id': employee.id,
                            'alphalist_mwe_detail_id': self.id})
                else:
                    if len(self.alphalist_detail_id.search([('employee_id', '=', employee.id),
                                                            ('alphalist_main_id', '=', self.id)])) == 0:
                        self.alphalist_detail_id.create({
                            'employee_id': employee.id,
                            'alphalist_main_id': self.id})
            print('END ' + str(employee.id))
        for employee in self.alphalist_detail_id:
            employee.generate_alphalist(False, employee.employee_id.id,
                                        self.annual_for_the_year,
                                        self.payroll_date_from,
                                        self.payroll_date_to)

        for employee in self.alphalist_mwe_detail_id:
            employee.generate_alphalist(False, employee.employee_id.id,
                                        self.annual_for_the_year,
                                        self.payroll_date_from,
                                        self.payroll_date_to)

        for employee in self.alphalist_detail_id:
            employee.recompute_alphalist()

        self.generateExcel(self.id)




class AlphalistDetail_7_1_3(models.Model):
    # This is the Table for the Schedule of 7.1, 7.3, 7.4
    _name = 'payroll.alphalist.detail'
    _description = 'Alphalist for Schedule 7.1,3,4 details'
    _order = 'sequence_no,last_name asc'
    name = fields.Char('Name')

    alphalist_main_id = fields.Many2one('payroll.alphalist.main')

    employee_id = fields.Many2one('hr.employee','Employee')
    sequence_no = fields.Integer('Sequence')
    tin_no = fields.Char('Tin No', default = '')
    last_name = fields.Char('Last Name',default = '')
    first_name = fields.Char('First Name',default = '')
    middle_name = fields.Char('Last Name',default = '')
    non_tax_gross_compensation_income = fields.Float('Gross Compensation Income', required = True,default = 0)
    non_tax_thirteenth_month = fields.Float('Thirteenth Month', required = True, digits=(18,2),default = 0)
    non_tax_other_benefits = fields.Float('Other Benefits', required = True, digits=(18,2),default = 0)
    non_tax_de_minimis_benefits = fields.Float('De Minimis Benefits', required = True, digits=(18,2),default = 0)
    non_tax_gov_contributions = fields.Float('SSS,GSIS,PHIC, and Pag - ibig Contributions, and Union Dues', required = True, digits=(18,2),default = 0)
    non_tax_other_compensation = fields.Float('Salaries and Other Forms of Compensation', required = True, digits=(18,2),default = 0)
    non_tax_total = fields.Float('Total Non-Taxable/Exempt Compensation Income', required = True, digits=(18,2),default = 0)
    tax_basic_pay = fields.Float('Basic Pay', required = True, digits=(18,2),default = 0)
    tax_thirteenth_month = fields.Float('Taxable Thirteenth Month', required = True, digits=(18,2),default = 0)
    tax_other_benefits = fields.Float('Taxable Other Benefits', required = True, digits=(18,2),default = 0)
    tax_other_compensation = fields.Float('Taxable Salaries and Other Forms of Compensation', required = True, digits=(18,2),default = 0)
    tax_total_compensation_income = fields.Float('Total Taxable Compensation Income', required = True, digits=(18,2),default = 0)
    exemption_code = fields.Char('Code', required = True,default = 0)
    exemption_amount = fields.Float('Amount', required = True, digits=(18,2),default = 0)
    paid_health_insurance = fields.Float('Premium Paid on Health and/or Hospital Insurance', required = True, digits=(18,2),default = 0)
    net_taxable_comp_income = fields.Float('Net Taxable Compensation Income', required = True, digits=(18,2),default = 0)
    tax_due = fields.Float('Tax Due (Jan - Dec)', required = True, digits=(18,2),default = 0)
    tax_withheld = fields.Float('Tax Withheld (Jan - Dec)', required = True, digits=(18,2),default = 0)
    paid_amount_december= fields.Float('Amount Withheld and Paid for December', required = True, digits=(18,2),default = 0)
    overwithheld_tax = fields.Float('Over Withheld', required = True, digits=(18,2),default = 0)
    amount_withheld_adjusted = fields.Float('Amount of Tax Withheld as Adjusted', required = True, digits=(18,2),default = 0)


    # For With Previous Employer
    prev_non_tax_thirteenth_month = fields.Float('Previous Thirteenth Month', required = True, digits=(18,2),default = 0)
    prev_non_tax_other_benefits = fields.Float('Previous Other Benefits', required = True, digits=(18,2),default = 0)
    prev_non_tax_de_minimis_benefits = fields.Float('Previous De Minimis Benefits', required = True, digits=(18,2),default = 0)
    prev_non_tax_gov_contributions = fields.Float('Previous SSS,GSIS,PHIC, and Pag - ibig Contributions, and Union Dues', required = True, digits=(18,2),default = 0)
    prev_non_tax_other_compensation = fields.Float('Previous Salaries and Other Forms of Compensation', required = True, digits=(18,2),default = 0)
    prev_non_tax_total = fields.Float('Previous Total Non-Taxable/Exempt Compensation Income', required = True, digits=(18,2),default = 0)
    prev_tax_basic_pay = fields.Float('Previous Basic Pay', required = True, digits=(18,2),default = 0)
    prev_tax_thirteenth_month = fields.Float('Previous Thirteenth Month', required = True, digits=(18,2),default = 0)
    prev_tax_other_benefits = fields.Float('Previous Other Benefits', required = True, digits=(18,2),default = 0)
    prev_tax_other_compensation = fields.Float('Previous Salaries and Other Forms of Compensation', required = True, digits=(18,2),default = 0)
    prev_tax_total_compensation_income = fields.Float('Previous Total Taxable Compensation Income', required = True, digits=(18,2),default = 0)
    prev_taxable_comp_income = fields.Float('Previous Net Taxable Compensation Income', required = True, digits=(18,2),default = 0)
    prev_tax_withheld = fields.Float('Previous Previous Employer Tax Withheld', required = True, digits=(18,2),default = 0)
    alphalist_schedule = fields.Selection(constants.ALPHALIST_SCHEDULE, 'Schedule Type')
    record_status = fields.Selection(constants.DETAIL_STATUS, 'Record Status', default = 1 )
    filed = fields.Boolean('Substitute Filing', required = True, default = True)
    with_previous_employer = fields.Boolean('With Previous Employer',default = False)


    @api.one
    def generate_alphalist(self,
                           withPreviousEmployer = False,
                           pint_emp_id = 0,
                           pint_Year = constants.YEAR_NOW,
                           pdt_release_date_from='',
                           pdt_release_date_to=''):

        #Get Employee Information and Latest Contract
        model_employee = self.env['hr.employee'].search([('id', '=', pint_emp_id)])

        if len(model_employee) > 0:
            pdt_release_date_from = datetime.strptime(pdt_release_date_from, '%Y-%m-%d')
            pdt_release_date_to = datetime.strptime(pdt_release_date_to, '%Y-%m-%d')
            #Retrieve Payroll Information
            model_payroll = self.env['hr.payroll.main'].search([('payroll_releasedate','>=',pdt_release_date_from),
                                                                       ('payroll_releasedate','<=', pdt_release_date_to),
                                                                       ('state', '=','post')])

            model_payroll_detail = self.env['hr.payroll.detail'].search([('employee_id', '=', pint_emp_id),
                                                                         ('payroll_detail_id', 'in', model_payroll.ids)])

            model_thirteenth_month_pays = self.env['payroll.incentive.13thmonth'].search([('release_date','>=',pdt_release_date_from),
                                                                                         ('release_date','<=', pdt_release_date_to)])
            lst_ids =[]
            for record in model_thirteenth_month_pays:
                lst_ids.append(record.id)

            model_thirteenth_month_pay =  self.env['payroll.incentive.13thmonth.detail'].search([('incentive_main_id' , 'in', lst_ids),
                                                                                                 ('employee_id' , '=', pint_emp_id)])

            model_taxtable = self.env['hr.payroll.taxtable']

            model_annualtax_taxble = self.env['payroll.annual.tax.table']

            model_alphalist_config = self.env['payroll.alphalist.config']
            if len(model_payroll_detail) > 0:

                self.tin_no = model_employee.tin_no
                self.last_name = model_employee.last_name
                self.middle_name = model_employee.middle_name
                self.first_name = model_employee.first_name
                thirteenth_month  = 0
                self.name = model_employee.name + ' Annual Tax for the year' + str(pint_Year)

                # NON TAXABLE AMOUNT
                if len(model_thirteenth_month_pay) > 0:
                    thirteenth_month = sum(employee.amount for employee in model_thirteenth_month_pay)
                if thirteenth_month > model_alphalist_config.GetAmount('THMONTH'):
                    self.non_tax_thirteenth_month = model_alphalist_config.GetAmount('THMONTH')
                    self.tax_thirteenth_month = thirteenth_month - model_alphalist_config.GetAmount('THMONTH')
                else:
                    self.non_tax_thirteenth_month = thirteenth_month

                sss_contrib = sum(amount.sss_premium for amount in model_payroll_detail)
                pagibig_contrib = sum(amount.hdmf_premium for amount in model_payroll_detail)
                phic_contrib = sum(amount.hmo_premium for amount in model_payroll_detail)
                #raise Warning('11')
                self.non_tax_other_compensation = sum(amount.undertime_amount for amount in model_payroll_detail) \
                                                 + sum(amount.tardiness_amount for amount in model_payroll_detail) \
                                                 + sum(amount.cola_amount for amount in model_payroll_detail)

                self.non_tax_gov_contributions = sss_contrib + pagibig_contrib + phic_contrib

                # TAXABLE
                if len(model_payroll_detail) > 0:
                    for employee_wage in model_payroll_detail:
                        wage = employee_wage.employee_id.contract_id.wage
                        break


                self.tax_basic_pay = wage * constants.MONTHS_IN_YEAR
                self.tax_other_compensation = sum(amount.reg_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_nightdiffy_amount for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_restday_amount for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_restday_ot_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_straightduty_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_pay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_work_pay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_spechol_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_spechol_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.other_incentive for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_leaves_amount for amount in model_payroll_detail)

                if model_employee.marital in ('single','widower','divorced')\
                        and model_employee.children == 0:
                    employee_status = "withnodependents"
                else:
                    employee_status = "withdependents"
                employee_status_code =''
                if model_employee.marital in ('single','widower','divorced'):
                    employee_status_code = 'S'
                else:
                    employee_status_code = 'ME'

                if model_employee.children >= 4:
                    employee_status_code = employee_status_code + str(4)
                else:
                    employee_status_code = employee_status_code + str(model_employee.children)

                employee_payment_schedule_raw  = model_employee.contract_id.schedule_pay

                if employee_payment_schedule_raw in constants.SCHEDULE_PAY:
                    if employee_payment_schedule_raw == 'weekly':
                        employee_payment_schedule = 'weekly'
                    elif employee_payment_schedule_raw == 'bi-monthly':
                        employee_payment_schedule = 'semimonthly'
                    elif employee_payment_schedule_raw == 'monthly':
                        employee_payment_schedule = 'monthly'

                #Get Exemption Amount
                dict_amount = model_taxtable.getTaxInformation(employee_status,
                                                               model_employee.children,
                                                               employee_payment_schedule)
                self.exemption_code = employee_status_code
                self.exemption_amount = float(dict_amount['EXEMPTION_AMOUNT'])

                if model_employee.active == 0:
                    # For Terminated Employee (7.1)
                    self.alphalist_schedule = 1

                    self.non_tax_total = self.non_tax_thirteenth_month \
                                         + self.non_tax_de_minimis_benefits \
                                         + self.non_tax_other_benefits \
                                         + self.non_tax_de_minimis_benefits \
                                         + self.non_tax_gov_contributions \
                                         + self.non_tax_other_compensation

                    self.tax_total_compensation_income = self.tax_basic_pay \
                                                         + self.tax_thirteenth_month \
                                                         + self.tax_other_benefits \
                                                         + self.tax_other_compensation
                    self.net_taxable_comp_income = self.tax_total_compensation_income \
                                                   - (self.paid_health_insurance \
                                                      + self.exemption_amount)

                    self.non_tax_gross_compensation_income = (self.non_tax_total + self.tax_total_compensation_income)

                    self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

                    self.tax_withheld = sum(amount.computed_tax for amount in model_payroll_detail)

                    self.paid_amount_december = self.tax_due - self.tax_withheld
                    self.overwithheld_tax = self.tax_withheld - self.tax_due

                    if self.paid_amount_december > self.overwithheld_tax:
                        self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
                    else:
                        self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax

                else:
                    #Get Year
                    dt_year_hired = model_employee.date_hired
                    if model_employee.date_hired != False:
                        int_year_hired = datetime.strptime(model_employee.date_hired, '%Y-%m-%d')
                    else:
                        int_year_hired = constants.YEAR_NOW

                    if int_year_hired != pint_Year:
                        #Employees w/o Prev. Employer(7.3)
                        self.alphalist_schedule = 3
                        self.with_previous_employer =False

                        self.non_tax_total = self.non_tax_thirteenth_month \
                                             + self.non_tax_de_minimis_benefits \
                                             + self.non_tax_other_benefits \
                                             + self.non_tax_de_minimis_benefits \
                                             + self.non_tax_gov_contributions \
                                             + self.non_tax_other_compensation

                        self.tax_total_compensation_income = self.tax_basic_pay \
                                                             + self.tax_thirteenth_month \
                                                             + self.tax_other_benefits \
                                                             + self.tax_other_compensation

                        self.net_taxable_comp_income = self.tax_total_compensation_income \
                                                       - (self.paid_health_insurance + self.exemption_amount)

                        self.non_tax_gross_compensation_income = (self.non_tax_total + self.tax_total_compensation_income)

                        self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

                        self.tax_withheld = sum(amount.computed_tax for amount in model_payroll_detail) + self.prev_tax_withheld

                        self.paid_amount_december = self.tax_due - self.tax_withheld
                        self.overwithheld_tax = self.tax_withheld - self.tax_due

                        if self.paid_amount_december > self.overwithheld_tax:
                            self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
                        else:
                            self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax

                    elif int_year_hired == pint_Year:
                        #Employees w Prev. Employer(7.4)
                        self.alphalist_schedule = 4

                        self.non_tax_total = self.non_tax_thirteenth_month \
                                             + self.non_tax_de_minimis_benefits \
                                             + self.non_tax_other_benefits \
                                             + self.non_tax_de_minimis_benefits \
                                             + self.non_tax_gov_contributions \
                                             + self.non_tax_other_compensation \

                        self.prev_non_tax_total = self.prev_non_tax_thirteenth_month \
                                             + self.prev_non_tax_de_minimis_benefits \
                                             + self.prev_non_tax_other_benefits \
                                             + self.prev_non_tax_gov_contributions \
                                             + self.prev_non_tax_other_compensation \

                        total_non_tax_income = self.non_tax_total + self.prev_non_tax_total

                        self.tax_total_compensation_income = self.tax_basic_pay \
                                                             + self.tax_thirteenth_month \
                                                             + self.tax_other_benefits \
                                                             + self.tax_other_compensation

                        total_tax_income = self.tax_total_compensation_income + self.prev_tax_total_compensation_income

                        self.net_taxable_comp_income = total_tax_income - (self.paid_health_insurance + self.exemption_amount)

                        self.non_tax_gross_compensation_income = (self.non_tax_total + total_tax_income)

                        self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

                        self.tax_withheld = sum(amount.computed_tax for amount in model_payroll_detail)

                        self.paid_amount_december = self.tax_due - self.tax_withheld
                        self.overwithheld_tax = self.tax_withheld - self.tax_due

                        if self.paid_amount_december > self.overwithheld_tax:
                            self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
                        else:
                            self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax

    @api.one
    def recompute_alphalist(self):
        model_annualtax_taxble = self.env['payroll.annual.tax.table']
        if self.alphalist_schedule == 1:
            self.non_tax_total = self.non_tax_thirteenth_month \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_other_benefits \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_gov_contributions \
                                 + self.non_tax_other_compensation

            self.tax_total_compensation_income = self.tax_basic_pay \
                                                 + self.tax_thirteenth_month \
                                                 + self.tax_other_benefits \
                                                 + self.tax_other_compensation

            self.net_taxable_comp_income = self.tax_total_compensation_income \
                                           - (self.paid_health_insurance \
                                              + self.exemption_amount)

            self.non_tax_gross_compensation_income = (self.non_tax_total + self.tax_total_compensation_income)

            self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

            self.paid_amount_december = self.tax_due - self.tax_withheld
            self.overwithheld_tax = self.tax_withheld - self.tax_due

            if self.paid_amount_december > self.overwithheld_tax:
                self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
            else:
                self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax

        elif self.alphalist_schedule == 3:

            self.non_tax_total = self.non_tax_thirteenth_month \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_other_benefits \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_gov_contributions \
                                 + self.non_tax_other_compensation

            self.tax_total_compensation_income = self.tax_basic_pay \
                                                 + self.tax_thirteenth_month \
                                                 + self.tax_other_benefits \
                                                 + self.tax_other_compensation

            self.net_taxable_comp_income = self.tax_total_compensation_income \
                                           - (self.paid_health_insurance \
                                              + self.exemption_amount)

            self.non_tax_gross_compensation_income = (self.non_tax_total + self.tax_total_compensation_income)

            self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

            self.paid_amount_december = self.tax_due - self.tax_withheld
            self.overwithheld_tax = self.tax_withheld - self.tax_due

            if self.paid_amount_december > self.overwithheld_tax:
                self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
            else:
                self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax

        elif self.alphalist_schedule == 4:

            self.non_tax_total = self.non_tax_thirteenth_month \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_other_benefits \
                                 + self.non_tax_de_minimis_benefits \
                                 + self.non_tax_gov_contributions \
                                 + self.non_tax_other_compensation \

            self.prev_non_tax_total = self.prev_non_tax_thirteenth_month \
                                 + self.prev_non_tax_de_minimis_benefits \
                                 + self.prev_non_tax_other_benefits \


            total_non_tax_income = self.non_tax_total + self.prev_non_tax_total

            self.tax_total_compensation_income = self.tax_basic_pay \
                                                 + self.tax_thirteenth_month \
                                                 + self.tax_other_benefits \
                                                 + self.tax_other_compensation

            self.prev_tax_total_compensation_income = self.prev_tax_basic_pay \
                                                 + self.prev_tax_thirteenth_month \
                                                 + self.prev_tax_other_benefits \
                                                 + self.prev_tax_other_compensation

            total_tax_income = self.tax_total_compensation_income + self.prev_tax_total_compensation_income

            self.net_taxable_comp_income = (total_tax_income) \
                                           - (self.paid_health_insurance \
                                              + self.exemption_amount)

            self.non_tax_gross_compensation_income = (self.non_tax_total + total_tax_income)

            self.tax_due = model_annualtax_taxble.getAnnualTaxAmount(self.net_taxable_comp_income)

            self.paid_amount_december = self.tax_due - self.tax_withheld
            self.overwithheld_tax = self.tax_withheld - self.tax_due

            if self.paid_amount_december > self.overwithheld_tax:
                self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
            else:
                self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax


class AlphalistDetail_7_5(models.Model):
    # This is the Table for the Schedule of 7.1, 7.3, 7.4
    _name = 'payroll.alphalist7_5.detail'
    _description = 'Alphalist for Schedule 7.5 details'
    _order = 'sequence_no'
    name = fields.Char('Name')

    alphalist_mwe_detail_id = fields.Many2one('payroll.alphalist.main')

    employee_id = fields.Many2one('hr.employee','Employee')
    sequence_no = fields.Integer('Sequence')
    tin_no = fields.Char('Tin No', default = '')
    last_name = fields.Char('Last Name',default = '')
    first_name = fields.Char('First Name',default = '')
    middle_name = fields.Char('Last Name',default = '')

    region_assigned = fields.Many2one('hr.regions','Region Assigned')
    total_compensation_income = fields.Float('Gross Compensation Income', required=True, digits=(18,2), default=0)
    basic_pay_perday = fields.Float('Basic SMW Per day', required=True, digits=(18,2), default=0)
    basic_pay_permonth = fields.Float('Basic SMW Per month', required=True, digits=(18,2), default=0)
    basic_pay_peryear = fields.Float('Basic SMW Per year', required=True, digits=(18,2), default=0)
    factor_used = fields.Float('Factor used (No of days/Years Used)', required=True, digits=(18,2), default=0)
    non_tax_holiday_pay = fields.Float('Holiday Pay', required=True, digits=(18,2), default=0)
    non_tax_overtime_pay = fields.Float('Overtime Pay', required=True, digits=(18,2), default=0)
    non_tax_nightshiff_pay = fields.Float('Night Shiftt Differential', required=True, digits=(18,2), default=0)
    non_tax_hazard_pay = fields.Float('Hazard Pay', required=True, digits=(18,2), default=0)
    non_tax_thirteenth_month = fields.Float('13th Month Pay', required=True, digits=(18,2), default=0)
    non_tax_other_benefits = fields.Float('Other Benefits', required=True, digits=(18,2), default=0)
    non_tax_deminimis_pay = fields.Float('De Minimis Benefits', required=True, digits=(18,2), default=0)
    non_tax_gov_contrib = fields.Float('SSS,GSIS,PHIC, and Pag - ibig Contributions, and Union Dues', required=True, digits=(18,2), default=0)
    non_tax_other_compensation = fields.Float('Salaries and Other Form of Compensation', required=True, digits=(18,2), default=0)
    non_tax_total = fields.Float('Total Non Taxable Income', required=True, digits=(18,2), default=0)
    tax_thirteenth_month = fields.Float('13th Month Pay', required=True, digits=(18,2), default=0)
    tax_other_benefits = fields.Float('Other Benefits', required=True, digits=(18,2), default=0)
    tax_other_compensation = fields.Float('Salaries and Other Form of Compensation', required=True, digits=(18,2), default=0)
    tax_total = fields.Float('Total Taxable Income', required=True, digits=(18,2), default=0)


    prev_total_compensation_income = fields.Float('Gross Compensation Income', required=True, digits=(18,2), default=0)
    prev_basic_pay_peryear = fields.Float('Holiday Pay', required=True, digits=(18,2), default=0)
    prev_non_tax_holiday_pay = fields.Float('Holiday Pay', required=True, digits=(18,2), default=0)
    prev_non_tax_overtime_pay = fields.Float('Overtime Pay', required=True, digits=(18,2), default=0)
    prev_non_tax_nightshiff_pay = fields.Float('Night Shiftt Differential', required=True, digits=(18,2), default=0)
    prev_non_tax_hazard_pay = fields.Float('Hazard Pay', required=True, digits=(18,2), default=0)
    prev_non_tax_thirteenth_month = fields.Float('13th Month Pay', required=True, digits=(18,2), default=0)
    prev_non_tax_other_benefits = fields.Float('Other Benefits', required=True, digits=(18,2), default=0)
    prev_non_tax_deminimis_pay = fields.Float('De Minimis Benefits', required=True, digits=(18,2), default=0)
    prev_non_tax_gov_contrib = fields.Float('SSS,GSIS,PHIC, and Pag - ibig Contributions, and Union Dues', required=True, digits=(18,2), default=0)
    prev_non_tax_other_compensation = fields.Float('Salaries and Other Form of Compensation', required=True, digits=(18,2), default=0)
    prev_non_tax_total = fields.Float('Total Non Taxable Income', required=True, digits=(18,2), default=0)
    prev_tax_thirteenth_month = fields.Float('13th Month Pay', required=True, digits=(18,2), default=0)
    prev_tax_other_benefits = fields.Float('Other Benefits', required=True, digits=(18,2), default=0)
    prev_tax_other_compensation = fields.Float('Salaries and Other Form of Compensation', required=True, digits=(18,2), default=0)
    prev_tax_total = fields.Float('Total Taxable Income', required=True, digits=(18,2), default=0)
    date_of_employment_from = fields.Date('Date of Employment From')
    date_of_employment_to = fields.Date('Date of Employment To')

    total_taxable_comp_income = fields.Float('Total Compensation Income (Previous & Present Employers )', required = True, digits=(18,2),default = 0)
    exemption_code = fields.Char('Code')
    exemption_amount = fields.Char('Amount', required=True, digits=(18,2), default=0)
    paid_health_insurance = fields.Float('Premium Paid on Health and/or Hospital Insurance', required = True, digits=(18,2),default = 0)
    net_taxable_comp_income = fields.Float('Net Taxable Compensation Income', required = True, digits=(18,2),default = 0)
    tax_due = fields.Float('Tax Due (Jan - Dec)', required = True, digits=(18,2),default = 0)
    tax_withheld = fields.Float('Tax Withheld', required = True, digits=(18,2),default = 0)
    prev_tax_withheld = fields.Float('Previous Tax Withheld', required = True, digits=(18,2),default = 0)
    paid_amount_december= fields.Float('Amount Withheld and Paid for December', required = True, digits=(18,2),default = 0)
    overwithheld_tax = fields.Float('Over Withheld', required = True, digits=(18,2),default = 0)
    amount_withheld_adjusted = fields.Float('Amount of Tax Withheld as Adjusted', required = True, digits=(18,2),default = 0)

    alphalist_schedule = fields.Selection(constants.ALPHALIST_SCHEDULE, 'Schedule Type')
    record_status = fields.Selection(constants.DETAIL_STATUS, 'Record Status', default = 1 )
    filed = fields.Boolean('Substitute Filing', required = True, default = True)
    with_previous_employer = fields.Boolean('With Previous Employer',default = False)

    @api.one
    def generate_alphalist(self,
                           withPreviousEmployer = False,
                           pint_emp_id = 0,
                           pint_Year = constants.YEAR_NOW,
                           pdt_release_date_from='',
                           pdt_release_date_to=''):

        #Get Employee Information and Latest Contract
        #raise Warning(pint_emp_id)
        model_employee = self.env['hr.employee'].search([('id', '=', pint_emp_id)])

        if len(model_employee) > 0:

            pdt_release_date_from = datetime.strptime(pdt_release_date_from, '%Y-%m-%d')
            pdt_release_date_to = datetime.strptime(pdt_release_date_to, '%Y-%m-%d')
            #Retrieve Payroll Information
            model_payroll = self.env['hr.payroll.main'].search([('payroll_releasedate','>=',pdt_release_date_from),
                                                                       ('payroll_releasedate','<=', pdt_release_date_to),
                                                                       ('payroll_main_id.employee_id','=', pint_emp_id),
                                                                       ('state', '=','approved')])


            model_payroll_detail = self.env['hr.payroll.detail'].search([('employee_id', '=', pint_emp_id),
                                                                         ('payroll_detail_id', 'in', model_payroll.ids)])

            model_thirteenth_month_pays = self.env['payroll.incentive.13thmonth'].search([('release_date','>=',pdt_release_date_from),
                                                                                         ('release_date','<=', pdt_release_date_to),
                                                                                         ('incentive_detail_id.employee_id','=', pint_emp_id)])
            model_thirteenth_month_pay = model_thirteenth_month_pays.incentive_detail_id.search([('employee_id', '=', pint_emp_id)])
            model_alphalist_config = self.env['payroll.alphalist.config']

            model_annualtax_taxble = self.env['payroll.annual.tax.table']

            model_taxtable = self.env['hr.payroll.taxtable']

            if len(model_payroll_detail) > 0:
                thirteenth_month  = 0

                self.tin_no = model_employee.tin_no
                self.last_name = model_employee.last_name
                self.middle_name = model_employee.middle_name
                self.first_name = model_employee.first_name
                self.name = model_employee.name + ' Annual Tax for the year' + str(pint_Year)
                self.alphalist_schedule = 5

                if len(model_employee.assignto_region) > 0:
                    self.region_assigned = model_employee.assignto_region
                else:
                    self.region_assigned = ""

                self.basic_pay_perday = model_employee.contract_id.daily_rate
                self.basic_pay_permonth = model_employee.contract_id.wage
                self.basic_pay_peryear =  model_employee.contract_id.daily_rate * (model_employee.contract_id.weeks_in_years * model_employee.contract_id.workdays_in_weeks)
                self.factor_used = (model_employee.contract_id.weeks_in_years * model_employee.contract_id.workdays_in_weeks)

                self.non_tax_holiday_pay = sum(amount.reg_hol_work_pay_amount for amount in model_payroll_detail) \
                                           + sum(amount.reg_spechol_amount for amount in model_payroll_detail)

                self.non_tax_overtime_pay = sum(amount.basic_pay_restday_ot_amount for amount in model_payroll_detail) \
                                           + sum(amount.reg_otpay_amount for amount in model_payroll_detail) \
                                           + sum(amount.reg_straightduty_amount for amount in model_payroll_detail) \
                                           + sum(amount.reg_hol_otpay_amount for amount in model_payroll_detail) \
                                           + sum(amount.reg_spechol_otpay_amount for amount in model_payroll_detail)

                self.non_tax_nightshiff_pay = sum(amount.reg_nightdiffy_amount for amount in model_payroll_detail)


                if len(model_thirteenth_month_pay) > 0:
                    thirteenth_month = sum(amount.amount for amount in model_thirteenth_month_pay)
                if thirteenth_month > model_alphalist_config.GetAmount('THMONTH'):
                    self.non_tax_thirteenth_month = model_alphalist_config.GetAmount('THMONTH')
                    self.tax_thirteenth_month = thirteenth_month - model_alphalist_config.GetAmount('THMONTH')
                else:
                    self.non_tax_thirteenth_month = thirteenth_month

                sss_contrib = sum(amount.sss_premium for amount in model_payroll_detail)
                pagibig_contrib = sum(amount.hdmf_premium for amount in model_payroll_detail)
                phic_contrib = sum(amount.hmo_premium for amount in model_payroll_detail)
                self.non_tax_other_compensation = sum(amount.undertime_amount for amount in model_payroll_detail) \
                                                 + sum(amount.tardiness_amount for amount in model_payroll_detail) \
                                                 + sum(amount.cola_amount for amount in model_payroll_detail)

                self.non_tax_gov_contrib = sss_contrib + pagibig_contrib + phic_contrib

                # TAXABLE
                self.tax_other_compensation = sum(amount.reg_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_nightdiffy_amount for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_restday_amount for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_restday_ot_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_straightduty_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_pay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_work_pay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_hol_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_spechol_amount for amount in model_payroll_detail) \
                                            + sum(amount.reg_spechol_otpay_amount for amount in model_payroll_detail) \
                                            + sum(amount.other_incentive for amount in model_payroll_detail) \
                                            + sum(amount.basic_pay_leaves_amount for amount in model_payroll_detail)

                #Get Year
                dt_year_hired = model_employee.date_hired
                if model_employee.date_hired != False:
                    int_year_hired = datetime.strptime(model_employee.date_hired, '%Y-%m-%d')
                else:
                    int_year_hired = constants.YEAR_NOW
                if int_year_hired != pint_Year:
                    self.with_previous_employer = True
                else:
                    self.with_previous_employer = False

                # Get Exemption


                if model_employee.marital in ('single','widower','divorced')\
                        and model_employee.children == 0:
                    employee_status = "withnodependents"
                else:
                    employee_status = "withdependents"
                employee_status_code =''
                if model_employee.marital in ('single','widower','divorced'):
                    employee_status_code = 'S'
                else:
                    employee_status_code = 'ME'

                if model_employee.children >= 4:
                    employee_status_code = employee_status_code + str(4)
                else:
                    employee_status_code = employee_status_code + str(model_employee.children)

                employee_payment_schedule_raw  = model_employee.contract_id.schedule_pay

                if employee_payment_schedule_raw in constants.SCHEDULE_PAY:
                    if employee_payment_schedule_raw == 'weekly':
                        employee_payment_schedule = 'weekly'
                    elif employee_payment_schedule_raw == 'bi-monthly':
                        employee_payment_schedule = 'semimonthly'
                    elif employee_payment_schedule_raw == 'monthly':
                        employee_payment_schedule = 'monthly'

                #Get Exemption Amount
                dict_amount = model_taxtable.getTaxInformation(employee_status,
                                                               model_employee.children,
                                                               employee_payment_schedule)
                self.exemption_code = employee_status_code
                self.exemption_amount = float(dict_amount['EXEMPTION_AMOUNT'])

                self.date_of_employment_from = model_employee.contract_id.date_start
                self.date_of_employment_to = model_employee.contract_id.date_end


                self.non_tax_total = self.non_tax_thirteenth_month \
                                     + self.non_tax_deminimis_pay \
                                     + self.non_tax_other_benefits \
                                     + self.non_tax_gov_contrib \
                                     + self.non_tax_other_compensation \
                                     + self.non_tax_holiday_pay \
                                     + self.non_tax_overtime_pay \
                                     + self.non_tax_nightshiff_pay \
                                     + self.non_tax_hazard_pay \
                                     + self.basic_pay_peryear

                self.tax_total = self.tax_thirteenth_month \
                                + self.tax_other_benefits \
                                + self.tax_other_compensation

                self.prev_non_tax_total =  self.prev_non_tax_thirteenth_month \
                                     + self.prev_non_tax_deminimis_pay \
                                     + self.prev_non_tax_other_benefits \
                                     + self.prev_non_tax_gov_contrib \
                                     + self.prev_non_tax_other_compensation \
                                     + self.prev_non_tax_holiday_pay \
                                     + self.prev_non_tax_overtime_pay \
                                     + self.prev_non_tax_nightshiff_pay \
                                     + self.prev_non_tax_hazard_pay \
                                     + self.prev_basic_pay_peryear

                self.prev_tax_total = self.prev_tax_thirteenth_month \
                                + self.prev_tax_other_benefits \
                                + self.prev_tax_other_compensation

                self.total_compensation_income = self.non_tax_total + self.tax_total
                self.prev_total_compensation_income = self.prev_non_tax_total + self.prev_tax_total

                self.total_taxable_comp_income = self.prev_total_compensation_income + self.total_compensation_income

                self.net_taxable_comp_income = self.total_taxable_comp_income \
                                               - ( (self.non_tax_total + self.prev_non_tax_total)
                                                  + self.paid_health_insurance
                                                  + float(self.exemption_amount) )


                self.tax_due = 0

                self.tax_withheld = sum(amount.computed_tax for amount in model_payroll_detail) + self.prev_tax_withheld

                self.paid_amount_december = self.tax_due - self.tax_withheld
                self.overwithheld_tax = self.tax_withheld - self.tax_due

                if self.paid_amount_december > self.overwithheld_tax:
                    self.amount_withheld_adjusted = self.paid_amount_december + self.overwithheld_tax
                else:
                    self.amount_withheld_adjusted = self.paid_amount_december - self.overwithheld_tax




class AlphalistDetail_7_2(models.Model):
    # This is the Table for the Schedule of 7.2
    _name = 'payroll.alphalist_7_2.detail'
    _description = 'Alphalist for Schedule 7.2 details'
    _order = 'sequence_no,last_name desc'

    name = fields.Char('Name')
    sequence_no = fields.Integer('Sequence')
    tin_no = fields.Char('Tin No', required = True)
    last_name = fields.Char('Last Name', required = True)
    first_name = fields.Char('First Name', required = True)
    middle_name = fields.Char('Last Name', required = True)
    gross_compensation_income = fields.Float('Gross Compensation Income', required = True)
    thirteenth_month = fields.Float('Thirteenth Month', required = True, digits=(18,2))
    other_benefits = fields.Float('Other Benefits', required = True, digits=(18,2))
    de_minimis_benefits = fields.Float('De Minimis Benefits', required = True, digits=(18,2))
    gov_contributions = fields.Float('SSS,GSIS,PHIC, and Pag - ibig Contributions, and Union Dues', required = True, digits=(18,2))
    other_compensation = fields.Float('Salaries and Other Forms of Compensation', required = True, digits=(18,2))
    total_non_taxable_comp_income = fields.Float('Total Non-Taxable/Exempt Compensation Income', required = True, digits=(18,2))
    taxable_basic_salary = fields.Float('Basic Salary', required = True, digits=(18,2))
    taxable_other_compensation = fields.Float('Salaries and Other Forms of Compensation', required = True, digits=(18,2))
    exemption_code = fields.Char('Code', required = True)
    exemption_amount = fields.Float('Amount', required = True, digits=(18,2))
    paid_health_insurance = fields.Float('Premium Paid on Health and/or Hospital Insurance', required = True, digits=(18,2))
    net_taxable_comp_income = fields.Float('Net Taxable Compensation Income', required = True, digits=(18,2))




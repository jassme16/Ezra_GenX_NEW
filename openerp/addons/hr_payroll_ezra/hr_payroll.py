# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from parameters import constants

import datetime
import xlwt
import xlrd
from xlutils.copy import copy
from xlutils.styles import Styles
from cStringIO import StringIO
import base64


YEAR = 365
MONTH = 30

DATE_NOW = datetime.datetime.now()
MWE = constants.MINIMUM_WAGE_AMOUNT
EXEMPTION = constants.ComputeTaxExemption()


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


PAYROLL_STATE_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid to Employees')
]

MARITAL_STATUS = [
    'single',
    'married',
    'widower',
    'divorced'
]


SCHEDULE_PAY=[
    'quarterly',
    'monthly',
    'semi-annually'
    'weekly',
    'bi-weekly',
    'bi-monthly',
    'annually'
]


class hrExtendedEmployee(models.Model):
    _name ='hr.employee'
    _inherit = ['hr.employee']
    _description = 'Extension of Employee Information for Ezra'

    #---------------- Functions/Methods

    # Overrides
    @api.multi
    def write(self, vals):
        super(hrExtendedEmployee, self).write(vals)
        return True
    # End Override Functions

    @api.model
    def create(self, vals):
        #Update first the Sequence
        #sequences = self.env['ir.sequence']
        #employeeSequences = sequences.search([('code','=','hr.employee.sequence')])

        new_record = super(hrExtendedEmployee, self).create(vals)

        #employeeSequences.write({'number_next': int(self.employee_number)})
        return new_record

    @api.model
    def _getEmpId(self):

        cr = self._cr
        uid = self._uid
        context =self._context
        obj_sequence = self.pool.get('ir.sequence')
        return obj_sequence.next_by_code(cr, uid, 'hr.employee.sequence', context=context)
        #sequences = self.env['ir.sequence']
        #employeeSequences = sequences.search([('code','=','hr.employee.sequence')])
        #raise Warning(employeeSequences.number_next)
        #self.employee_number = employeeSequences.number_next + 1
        #return employeeSequences.number_next + 1

    @api.onchange('first_name','middle_name','last_name')
    def getFullname(self):
        if self.first_name == False:
            self.first_name=''
            self.first_name=''
        if self.middle_name == False:
            self.middle_name=''
        if self.last_name == False:
            self.last_name=''
        #self.name_related = self.first_name + " " + self.middle_name + " " + self.last_name
        #self.name = self.first_name + " " + self.middle_name + " " + self.last_name

        self.name_related = self.last_name + ", " + self.first_name + " " + self.middle_name
        self.name = self.last_name + ", " + self.first_name + " " + self.middle_name

    def getEmployeeID(self):
        prim_key = None
        empids = self.env['hr.employee'].search([('employee_number', '=', self.employee_number)])
        if len(empids) >0:
            prim_key = int(empids[0])
        else:
            prim_key = 0
        self.employee_id = prim_key
        return prim_key
    # End Functions/Methods

    #Override Functions
    @api.one
    def _payslip_count(self):
        Payslip = self.env['hr.payroll.detail']
        self.payslip_count =  Payslip.search_count([('employee_id', '=', self.id)])

    @api.one
    def _timesheet_count1(self):
        Sheet = self.env['hr.payroll.attendance']
        self.timesheet_count = Sheet.search_count([('employee_id', '=', self.id)])

    @api.onchange('assignto')
    def checkAssignProjectChange(self):
        #raise Warning(111)
        #if len(self.assignto) == 0:
        self.assignto_branch_2 =""

    @api.constrains('sss_no', 'philhealth_no')
    def _check_SSS(self):
        if len(self.sss_no) < 10 or len(self.sss_no) > 10:
            raise ValidationError('SSS Number must be in 10 digits')
        if len(self.philhealth_no) < 12 or len(self.philhealth_no) > 12:
            raise ValidationError('PhilHealth Number must be in 12 digits')
        if len(self.hdmf_no) < 12 or len(self.hdmf_no) > 12:
            raise ValidationError('Pag-ibig number must be in 12 digits')

    def _set_remaining_days(self, cr, uid, empl_id, name, value, arg, context=None):
        return True

    employee_number = fields.Char('Employee Number',select = True, default = _getEmpId)
    first_name = fields.Char('First name', required = True, default = ' ')
    last_name = fields.Char('Last name', required = True, default = ' ')
    middle_name = fields.Char('Middle name', default = ' ')
    sss_no = fields.Char('SSS No', size=10)
    hdmf_no = fields.Char('HDMF No', size=12)
    philhealth_no = fields.Char('Philhealth No',size=12)
    tin_no = fields.Char('Tin')
    bankacctno = fields.Text('Bank account number')
    assignto = fields.Many2one('res.customers.main', 'Project Assign',required =True)
    payslip_count =  fields.Integer('Payslips', store = False, compute = "_payslip_count")
    timesheet_count = fields.Integer('Timesheets', store=False,compute= "_timesheet_count1")
    date_hired = fields.Date('Date Hired')
    date_resigned = fields.Date('Date Resigned')
    job_id = fields.Many2one('hr.job', 'Job Title', required =True)

    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender', required=True)
    marital =  fields.Selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Marital Status', required=True)

    #Add fields for Loans 
    # #SSS Premium 
    sss_premium_monthly_amortization = fields.Float('Monthly Amortization')
    sss_premium_remaining_months=fields.Integer("Month's  Remaining", default = 0)


    #SSS Loans
    sss_loans_monthly_amortization=fields.Float("Monthly Amortization")
    sss_loans_remaining_months=fields.Integer("Month's  Remaining", default = 0)
    sss_loans_start_Month = fields.Selection(constants.MONTH_SELECTION, 'Month Start')
    sss_loans_start_year = fields.Integer('Year Start', default = constants.YEAR_NOW)
    #Pag­ibig Premium 
    pagibig_premium_monthly_amortization=fields.Float("Monthly Amortization")
    pagibig_premium_remaining_months=fields.Integer("Month's Remaining", default = 0)


    #Pag­ibig Salary Loans 
    pagibig_salaryloan_monthly_amortization=fields.Float("Monthly Amortization")
    pagibig_salaryloan_remaining_months= fields.Integer("Month's Remaining", default = 0)
    pagibig_salaryloan_start_Month = fields.Selection(constants.MONTH_SELECTION, 'Month Start')
    pagibig_salaryloan_start_year = fields.Integer('Year Start', default = constants.YEAR_NOW)

    #Pag­ibig Calamity Loans 
    pagibig_calamityloan_monthly_amortization=fields.Float("Monthly Amortization")
    pagibig_calamityloan_remaining_months=fields.Integer("Month's Remaining", default = 0)
    pagibig_calamityloan_start_Month = fields.Selection(constants.MONTH_SELECTION, 'Month Start')
    pagibig_calamityloan_start_year = fields.Integer('Year Start', default = constants.YEAR_NOW)

    #Add the fields: Region, Working Days, Branch
    assignto_region = fields.Many2one('hr.regions','Region',required =True)
    assignto_workingdays = fields.Selection(constants.WORKING_DAYS, 'Working Days', required =True)
    assignto_branch = fields.Char('Branch', required = True,default = ' ')
    assignto_branch_2 = fields.Many2one('res.customer.branches','Branch', required =True)


    #Other Info
    thirteenth_month_amount = fields.Float('Paid 13th Month', default=0, digits=(18,2))
    thirteenth_month_date_paid = fields.Date('Date Paid')
    remaining_leave = fields.Integer('Remaining Leaves', default = 0)



class payrollMainInformation(models.Model):
    _name ='hr.payroll.main'
    _description = 'Summary of Information about the Payroll Generated'
    _inherit = 'mail.thread'
    _order = 'write_date desc'

    @api.one
    def _getFilename(self):
        if self.name == False:
            str_excelname = "Payroll"
        else:
            str_excelname = self.name
        self.filename = '%s.xls' % str_excelname

    @api.one
    def getTotalEmployeePayroll(self):
        self.total_payroll_count = len(self.payroll_main_id)

    @api.onchange('total_payroll_count')
    def changeTotalPayrollCount(self):
        self.total_payroll_count = len(self.payroll_main_id)

    name = fields.Char('Payroll Name',reguired = True)
    payroll_releasedate = fields.Date('Payroll Date',reguired = True)
    payroll_attendance = fields.Many2one('hr.attendance.main', 'Attendance', reguired = True)
    payroll_month_of = fields.Selection(constants.MONTH_SELECTION, 'for the Month of', reguired = True)
    payroll_month_quarter = fields.Selection(MONTH_QUARTER_SELECTION, required = True)
    payment_release = fields.Date('Released Date',reguired = True)

    payroll_main_id = fields.One2many('hr.payroll.detail','payroll_detail_id', readonly=False,copy=False)
    state = fields.Selection(PAYROLL_STATE_STATUS, 'Status', default = 'draft')

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    payroll_file = fields.Binary('Excel File')

    total_payroll_count = fields.Integer('Payroll Count', readonly = True,store = False,compute ='getTotalEmployeePayroll')
    # is_attendanceChange = False

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    # Override Function
    @api.multi
    def unlink(self):
        for perSelf in self:
            if perSelf.state == PAYROLL_STATE_STATUS[1][0] or \
               perSelf.state == PAYROLL_STATE_STATUS[2][0]:
                if isinstance(perSelf.name, object):
                    if perSelf.name == '':
                        stname = ''
                    else:
                        stname = perSelf.name
                else:
                    stname = perSelf.name

                raise Warning("The " + stname + " you've trying to delete is already processed.")
        super(payrollMainInformation, self).unlink()
        return True

    @api.one
    def createDeductionIncentive(self, pint_payrolldetail = 0):
        model_incentives = self.env['hr.incentives'].search([])
        model_deductions = self.env['hr.deductions'].search([])
        if pint_payrolldetail == 0:
            payroll_details = self.payroll_main_id
        else:
            payroll_details = self.env['hr.payroll.detail'].search([('id', '=', pint_payrolldetail)])

        for payroll_detail in payroll_details:
            #Creation of Other Incentive
            #Create Main
            model_payroll_main = self.env['payroll.incentive.main']
            model_payroll_inc_breakdown = self.env['payroll.incen.breakdown']

            model_payroll_main_exists = model_payroll_main.search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_payroll_main_exists) > 0:
                #Update or Create another Incentive Breakdown
                for incentive_data in model_incentives:
                    model_incentives_exist = model_payroll_inc_breakdown.search([('main_id', '=', model_payroll_main_exists.id),
                                                                                 ('name', '=', incentive_data.id)])
                    #Update Breakdown
                    if len(model_incentives_exist) == 0:
                        model_payroll_inc_breakdown.create({
                            'main_id': model_payroll_main_exists.id,
                            'name': incentive_data.id,
                            'amount': incentive_data.amount})
            else:
                create_inc_id = model_payroll_main.create({
                    'payroll_detail_id' : payroll_detail.id,
                    'name' : payroll_detail.employee_id.name + ' ' + self.name}).id
                #Incentive Breakdown
                for incentive_data in model_incentives:
                        model_payroll_inc_breakdown.create({
                            'main_id': create_inc_id,
                            'name': incentive_data.id,
                            'amount': incentive_data.amount})



            model_payroll_main = self.env['payroll.incentive.main'].search([('payroll_detail_id', '=', payroll_detail.id)])
            model_payroll_inc_breakdown = self.env['payroll.incen.breakdown'].search([('main_id', '=', model_payroll_main.id)])
            payroll_detail.other_incentive = round(sum(incen.amount for incen in model_payroll_inc_breakdown),2)


        for payroll_detail in payroll_details:
            model_incentives = self.env['hr.incentives'].search([])
            model_deductions = self.env['hr.deductions'].search([])
            model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_incentive_breakdown) == 0:
                for incentive in model_incentives:
                    model_incentive_breakdown.create({
                        'payroll_detail_id' : payroll_detail.id,
                        'name' : incentive.id,
                        'amount':incentive.amount
                    })
            else:
                for incentive in model_incentives:
                    model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', payroll_detail.id),
                                                                                              ('name', '=', incentive.id)])
                    if len(model_incentive_breakdown) == 0:
                        model_incentive_breakdown.create({
                            'payroll_detail_id': payroll_detail.id,
                            'name' : incentive.id,
                            'amount': incentive.amount
                        })

            #Deductions
            model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_deduction_breakdown) == 0:
                for deduction in model_deductions:
                    model_deduction_breakdown.create({
                        'payroll_detail_id' : payroll_detail.id,
                        'name' : deduction.id,
                        'amount': deduction.amount
                    })
            else:
                for deduction in model_deductions:
                    model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', payroll_detail.id),
                                                                                              ('name', '=', deduction.id)])
                    if len(model_deduction_breakdown) == 0:
                        model_deduction_breakdown.create({
                            'payroll_detail_id': payroll_detail.id,
                            'name' : deduction.id,
                            'amount': deduction.amount
                        })

            payroll_detail.other_incentive = self.env['payroll.detail.incentives'].getTotal(payroll_detail.id)
            payroll_detail.other_deductions = self.env['payroll.detail.deduction'].getTotal(payroll_detail.id)

        model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', False)])
        model_incentive_breakdown.unlink()

        model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', False)])
        model_deduction_breakdown.unlink()

    @api.one
    def computeSummary(self, pint_payrolldetail = 0):
        if pint_payrolldetail == 0:
            payroll_details = self.payroll_main_id
        else:
            payroll_details = self.env['hr.payroll.detail'].search([('id', '=', pint_payrolldetail)])

        for payroll_detail in payroll_details:
            #Gross Salary
            payroll_detail.gross_salary = 0

            payroll_detail.gross_salary += (payroll_detail.basic_pay_amount + payroll_detail.basic_pay_leaves_amount) - \
                                            (payroll_detail.tardiness_amount + payroll_detail.undertime_amount)

            payroll_detail.gross_salary += payroll_detail.basic_pay_restday_amount + \
                                            payroll_detail.basic_pay_restday_ot_amount + \
                                            payroll_detail.reg_otpay_amount + \
                                            payroll_detail.reg_nightdiffy_amount + \
                                            payroll_detail.reg_straightduty_amount + \
                                            payroll_detail.reg_hol_work_pay_amount + \
                                            payroll_detail.reg_hol_otpay_amount + \
                                            payroll_detail.reg_spechol_amount + \
                                            payroll_detail.reg_spechol_otpay_amount + \
                                            payroll_detail.cola_amount + \
                                            payroll_detail.other_incentive + \
                                            payroll_detail.reg_hol_pay_amount + \
                                            payroll_detail.allowance_amount

            #Deductions
            payroll_detail.deductions = 0
            payroll_detail.deductions += payroll_detail.sss_premium + payroll_detail.hdmf_premium +payroll_detail.hmo_premium #+ payroll_detail.sss_loan + payroll_detail.hdmf_salary_loan + payroll_detail.hdmf_calamity_loan
            payroll_detail.deductions += payroll_detail.other_deductions + payroll_detail.sss_loan + payroll_detail.hdmf_salary_loan + payroll_detail.hdmf_calamity_loan

            #Tax

            #Net Pay
            payroll_detail.deductions = payroll_detail.deductions + payroll_detail.computed_tax
            #Net pay
            payroll_detail.net_pay = (payroll_detail.gross_salary - payroll_detail.deductions)

    # Functions for Payroll Computation
    #Add First all the employee/s and its attendance in Selected Attendance form
    @api.one
    def createPayrollInitData(self):
        #--------Objects Declared
        payroll_detail = self.env['hr.payroll.detail']
        model_sss =self.env['hr.payroll.ssscontrib']
        model_hmo= self.env['hr.payroll.hmo']
        model_hdmf= self.env['hr.payroll.hdmf']


        model_gov_contrib = self.env['payroll.sss.deductions']
        model_tax = self.env['hr.payroll.taxtable']


        # remove_payroll_detail = self.env['hr.payroll.detail']
        # remove_payroll_detail.search([('payroll_detail_id', '=', self.id)])
        # remove_payroll_detail.unlink()

        # Getting all The Rate of Work Type
        work_hour_type = self.env['hr.workhourtype']

        regular_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('DRATE'),2)
        regular_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('ROT'),2)
        regular_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('NDIFF'),2)
        restday_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTDRATE'),2)
        restday_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTOT'),2)
        restday_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTNDIFF'),2)
        spec_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHDRATE'),2)
        spec_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHOT'),2)
        restday_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHNDIFF'),2)
        hol_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHDRATE'),2)
        hol_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHOT'),2)
        hol_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHNDIFF'),2)
        straigthduty_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('STRDUTY'),2)

        attendances = self.payroll_attendance
        # Generation of Employee
        employee_id_list  =[]
        for attenndances in attendances.employee_ids:
            employee_id_list.append(attenndances.employee_id.id)


        #raise Warning(employee_id_list)
        payroll_detail = self.env['hr.payroll.detail']

        remove_payroll_detail = payroll_detail.search([('employee_id', 'not in', employee_id_list),
                                      ('payroll_detail_id', '=', self.id)])
        remove_payroll_detail.unlink()

    @api.model
    def createDeductionIncentiveExternal(self, pint_payrolldetail = 0):
        model_incentives = self.env['hr.incentives'].search([])
        model_deductions = self.env['hr.deductions'].search([])

        payroll_details = self.env['hr.payroll.detail'].search([('id', '=', pint_payrolldetail)])

        for payroll_detail in payroll_details:
            #Creation of Other Incentive
            #Create Main
            model_payroll_main = self.env['payroll.incentive.main']
            model_payroll_inc_breakdown = self.env['payroll.incen.breakdown']

            model_payroll_main_exists = model_payroll_main.search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_payroll_main_exists) > 0:
                #Update or Create another Incentive Breakdown
                for incentive_data in model_incentives:
                    model_incentives_exist = model_payroll_inc_breakdown.search([('main_id', '=', model_payroll_main_exists.id),
                                                                                 ('name', '=', incentive_data.id)])
                    #Update Breakdown
                    if len(model_incentives_exist) == 0:
                        model_payroll_inc_breakdown.create({
                            'main_id': model_payroll_main_exists.id,
                            'name': incentive_data.id,
                            'amount': incentive_data.amount})
            else:
                create_inc_id = model_payroll_main.create({
                    'payroll_detail_id' : payroll_detail.id,
                    'name' : payroll_detail.employee_id.name + ' ' + self.name}).id
                #Incentive Breakdown
                for incentive_data in model_incentives:
                        model_payroll_inc_breakdown.create({
                            'main_id': create_inc_id,
                            'name': incentive_data.id,
                            'amount': incentive_data.amount})



            model_payroll_main = self.env['payroll.incentive.main'].search([('payroll_detail_id', '=', payroll_detail.id)])
            model_payroll_inc_breakdown = self.env['payroll.incen.breakdown'].search([('main_id', '=', model_payroll_main.id)])
            payroll_detail.other_incentive = round(sum(incen.amount for incen in model_payroll_inc_breakdown),2)


        for payroll_detail in payroll_details:
            model_incentives = self.env['hr.incentives'].search([])
            model_deductions = self.env['hr.deductions'].search([])
            model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_incentive_breakdown) == 0:
                for incentive in model_incentives:
                    model_incentive_breakdown.create({
                        'payroll_detail_id' : payroll_detail.id,
                        'name' : incentive.id,
                        'amount':incentive.amount
                    })
            else:
                for incentive in model_incentives:
                    model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', payroll_detail.id),
                                                                                              ('name', '=', incentive.id)])
                    if len(model_incentive_breakdown) == 0:
                        model_incentive_breakdown.create({
                            'payroll_detail_id': payroll_detail.id,
                            'name' : incentive.id,
                            'amount': incentive.amount
                        })

            #Deductions
            model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', payroll_detail.id)])
            if len(model_deduction_breakdown) == 0:
                for deduction in model_deductions:
                    model_deduction_breakdown.create({
                        'payroll_detail_id' : payroll_detail.id,
                        'name' : deduction.id,
                        'amount': deduction.amount
                    })
            else:
                for deduction in model_deductions:
                    model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', payroll_detail.id),
                                                                                              ('name', '=', deduction.id)])
                    if len(model_deduction_breakdown) == 0:
                        model_deduction_breakdown.create({
                            'payroll_detail_id': payroll_detail.id,
                            'name' : deduction.id,
                            'amount': deduction.amount
                        })

            payroll_detail.other_incentive = self.env['payroll.detail.incentives'].getTotal(payroll_detail.id)
            payroll_detail.other_deductions = self.env['payroll.detail.deduction'].getTotal(payroll_detail.id)

        model_incentive_breakdown = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', False)])
        model_incentive_breakdown.unlink()

        model_deduction_breakdown = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', False)])
        model_deduction_breakdown.unlink()

    @api.model
    def computeSummaryExternal(self, pint_payrolldetail = 0):

        payroll_details = self.env['hr.payroll.detail'].search([('id', '=', pint_payrolldetail)])

        for payroll_detail in payroll_details:
            #Gross Salary
            payroll_detail.gross_salary = 0

            payroll_detail.gross_salary += (payroll_detail.basic_pay_amount + payroll_detail.basic_pay_leaves_amount) - \
                                            (payroll_detail.tardiness_amount + payroll_detail.undertime_amount)

            payroll_detail.gross_salary += payroll_detail.basic_pay_restday_amount + \
                                            payroll_detail.basic_pay_restday_ot_amount + \
                                            payroll_detail.reg_otpay_amount + \
                                            payroll_detail.reg_nightdiffy_amount + \
                                            payroll_detail.reg_straightduty_amount + \
                                            payroll_detail.reg_hol_work_pay_amount + \
                                            payroll_detail.reg_hol_otpay_amount + \
                                            payroll_detail.reg_spechol_amount + \
                                            payroll_detail.reg_spechol_otpay_amount + \
                                            payroll_detail.cola_amount + \
                                            payroll_detail.other_incentive + \
                                            payroll_detail.reg_hol_pay_amount

            #Deductions
            payroll_detail.deductions = 0
            payroll_detail.deductions += payroll_detail.sss_premium + payroll_detail.hdmf_premium +payroll_detail.hmo_premium #+ payroll_detail.sss_loan + payroll_detail.hdmf_salary_loan + payroll_detail.hdmf_calamity_loan
            payroll_detail.deductions += payroll_detail.other_deductions + payroll_detail.sss_loan + payroll_detail.hdmf_salary_loan + payroll_detail.hdmf_calamity_loan

            #Tax

            #Net Pay
            payroll_detail.deductions = payroll_detail.deductions + payroll_detail.computed_tax
            #Net pay
            payroll_detail.net_pay = (payroll_detail.gross_salary - payroll_detail.deductions)

    @api.model
    def computePayrollExternal(self, pint_payrolldetail = 0):
        self.createDeductionIncentiveExternal(pint_payrolldetail)
        self.computeSummaryExternal(pint_payrolldetail)
        res = {
                'type': 'ir.actions.client',
                'tag': 'reload'}
        return res


    def getAmountWithoutRoundOff(self, pamount = 0.00):
        str_amount = str(pamount)
        str_decimal_amount = str_amount[-str_amount.find('.'):]
        str_decimal_amount = str_decimal_amount[0:2]
        str_whole_amount = str_amount[0:str_amount.find('.')]
        if str_decimal_amount.find('.') <0:
            str_new_amount = str_whole_amount  +'.'+ str_decimal_amount
        else:
            str_new_amount = str_whole_amount  + str_decimal_amount
        curr_amount = float(str_new_amount)
        return curr_amount


    @api.one
    def computePayroll(self):
        #--------Objects Declared
        payroll_detail = self.env['hr.payroll.detail']
        model_sss =self.env['hr.payroll.ssscontrib']
        model_hmo= self.env['hr.payroll.hmo']
        model_hdmf= self.env['hr.payroll.hdmf']


        model_gov_contrib = self.env['payroll.sss.deductions']
        model_tax = self.env['hr.payroll.taxtable']
        model_audit = self.env['sys.genx.audit']


        # remove_payroll_detail = self.env['hr.payroll.detail']
        # remove_payroll_detail.search([('payroll_detail_id', '=', self.id)])
        # remove_payroll_detail.unlink()

        # Getting all The Rate of Work Type
        work_hour_type = self.env['hr.workhourtype']

        regular_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('DRATE'),2)
        regular_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('ROT'),2)
        regular_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('NDIFF'),2)
        restday_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTDRATE'),2)
        restday_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTOT'),2)
        restday_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('RESTNDIFF'),2)
        spec_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHDRATE'),2)
        spec_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHOT'),2)
        restday_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('SPEHNDIFF'),2)
        hol_daily_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHDRATE'),2)
        hol_ot_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHOT'),2)
        hol_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('REGHNDIFF'),2)
        straigthduty_nightdiff_rate_decimal = round(work_hour_type.getWorkHourRateinDecimal('STRDUTY'),2)


        attendances = self.payroll_attendance
        # Generation of Employee
        employee_id_list  =[]
        for attenndances in attendances.employee_ids:
            employee_id_list.append(attenndances.employee_id.id)

        payroll_detail = self.env['hr.payroll.detail']

        remove_payroll_detail = payroll_detail.search([('employee_id', 'not in', employee_id_list),
                                      ('payroll_detail_id', '=', self.id)])
        remove_payroll_detail.unlink()

        employee_monthly_rate = 0.00
        employee_daily_rate = 0.00
        employee_hourly_rate = 0.00

        PAYROLL_YEAR = datetime.datetime.strptime(self.payroll_attendance.schedule_datefrom, '%Y-%m-%d').year

        #Employee who is assigned to this project and for Immediate Duty
        for attendance in attendances:
            for employee_attendance_info in attendance.employee_ids.search([('is_reliever','=',False),
                                                                            ('employee_attendance_child_id','=',attendance.id)]):
                payroll_employee = payroll_detail.search([('payroll_detail_id', '=', self.id),
                                                          ('employee_id','=',employee_attendance_info.employee_id.id)])
                if len(payroll_employee) == 0:
                        payroll_detail.create(
                            {
                                'payroll_detail_id': self.id,
                                'name': self.name + ' ' + employee_attendance_info.employee_id.name + ' ' + str(self.id),
                                'employee_id': employee_attendance_info.employee_id.id,
                                'employee_project_assign': self.payroll_attendance.assign_projects.id,
                                'is_reliever': employee_attendance_info.is_reliever,
                                'is_additional_employee' : employee_attendance_info.is_additional_employee,
                                'basic_pay_perday': employee_attendance_info.regular_days_work,
                                'basic_pay_perday_rate': 0,
                                'basic_pay_amount': 0,
                                'reg_otpay_perhour': employee_attendance_info.regular_overtime,
                                'reg_otpay_amount': 0,
                                'reg_nightdiff_perhour': employee_attendance_info.night_differential,
                                'reg_nightdiffy_amount': 0,
                                'reg_straightduty_perhour': employee_attendance_info.straight_duty,
                                'reg_straightduty_amount': 0,
                                'cola_rate_perday': 0,
                                'cola_amount': 0,
                                'allowance_rate_perday':0,
                                'allowance_amount':0,
                                'reg_hol_pay_perday': employee_attendance_info.legal_holiday_day,
                                'reg_hol_pay_amount': 0,
                                'reg_hol_work_pay_perhour': employee_attendance_info.holiday_day_work,
                                'reg_hol_work_pay_amount': 0,
                                'reg_hol_otpay_perhour': employee_attendance_info.holiday_overtime,
                                'reg_hol_otpay_amount': 0,
                                'reg_spechol_perhour': employee_attendance_info.special_day_work,
                                'reg_spechol_amount': 0,
                                'reg_spechol_otpay_perhour': employee_attendance_info.special_overtime,
                                'reg_spechol_otpay_amount': 0,
                                'other_incentive': 0,
                                'tardiness': employee_attendance_info.tardiness,
                                'tardiness_permin_rate': 0,
                                'tardiness_amount': 0,
                                'undertime': employee_attendance_info.undertime,
                                'tardiness_pay_permin_rate': 0,
                                'undertime_amount': 0,
                                'gross_salary': 0,
                                'sss_premium': 0,
                                'sss_loan': 0,
                                'hdmf_premium': 0,
                                'hdmf_salary_loan': 0,
                                'hdmf_calamity_loan': 0,
                                'hmo_premium': 0,
                                'other_deductions': 0,
                                'deductions': 0,
                                'net_pay': 0,
                                'basic_pay_leaves_perhour': employee_attendance_info.leaves,
                                'basic_pay_leaves_amount': 0,
                                'basic_pay_restday_perhour': employee_attendance_info.rest_day_work,
                                'basic_pay_restday_amount': 0,
                                'basic_pay_restday_ot_perhour': employee_attendance_info.restday_overtime,
                                'basic_pay_restday_ot_amount': 0,
                                'month_half_period': self.payroll_month_quarter ,
                                'month_name_period': self.payroll_month_of ,
                                'year_payroll_period': PAYROLL_YEAR,
                                'basic_pay_leaves_perday': employee_attendance_info.leaves,
                            })
                        employee_attendance_info.computed_payroll = True

        #Employee who is become reliever to this project (e.g. Employee within the assigned projects, reg. relievers and in Other Projects)
        for attendance in attendances:
            for employee_attendance_info in attendance.employee_ids.search([('is_reliever','=',True),
                                                                            ('employee_attendance_child_id','=',attendance.id)]):
                payroll_employee = payroll_detail.search([('payroll_detail_id', '=', self.id),
                                                          ('employee_id','=',employee_attendance_info.employee_reliever.id)])
                # If Employee is a regular reliever and in Other Projects Assigned.
                if len(payroll_employee) == 0:
                    payroll_detail.create(
                        {
                            'payroll_detail_id': self.id,
                            'name': self.name + ' ' + employee_attendance_info.employee_reliever.name + ' ' + str(self.id),
                            'employee_id': employee_attendance_info.employee_reliever.id,
                            'employee_project_assign': self.payroll_attendance.assign_projects.id,
                            'is_reliever': employee_attendance_info.is_reliever,
                            'basic_pay_perday': employee_attendance_info.regular_days_work,
                            'basic_pay_perday_rate': 0,
                            'basic_pay_amount': 0,
                            'reg_otpay_perhour': employee_attendance_info.regular_overtime,
                            'reg_otpay_amount': 0,
                            'reg_nightdiff_perhour': employee_attendance_info.night_differential,
                            'reg_nightdiffy_amount': 0,
                            'reg_straightduty_perhour': employee_attendance_info.straight_duty,
                            'reg_straightduty_amount': 0,
                            'cola_rate_perday': 0,
                            'cola_amount': 0,
                            'allowance_rate_perday':0,
                            'allowance_amount':0,
                            'reg_hol_pay_perday': employee_attendance_info.legal_holiday_day,
                            'reg_hol_pay_amount': 0,
                            'reg_hol_work_pay_perhour': employee_attendance_info.holiday_day_work,
                            'reg_hol_work_pay_amount': 0,
                            'reg_hol_otpay_perhour': employee_attendance_info.holiday_overtime,
                            'reg_hol_otpay_amount': 0,
                            'reg_spechol_perhour': employee_attendance_info.special_day_work,
                            'reg_spechol_amount': 0,
                            'reg_spechol_otpay_perhour': employee_attendance_info.special_overtime,
                            'reg_spechol_otpay_amount': 0,
                            'other_incentive': 0,
                            'tardiness': employee_attendance_info.tardiness,
                            'tardiness_permin_rate': 0,
                            'tardiness_amount': 0,
                            'undertime': employee_attendance_info.undertime,
                            'tardiness_pay_permin_rate': 0,
                            'undertime_amount': 0,
                            'gross_salary': 0,
                            'sss_premium': 0,
                            'sss_loan': 0,
                            'hdmf_premium': 0,
                            'hdmf_salary_loan': 0,
                            'hdmf_calamity_loan': 0,
                            'hmo_premium': 0,
                            'other_deductions': 0,
                            'deductions': 0,
                            'net_pay': 0,
                            'basic_pay_leaves_perhour': employee_attendance_info.leaves,
                            'basic_pay_leaves_amount': 0,
                            'basic_pay_restday_perhour': employee_attendance_info.rest_day_work,
                            'basic_pay_restday_amount': 0,
                            'basic_pay_restday_ot_perhour': employee_attendance_info.restday_overtime,
                            'basic_pay_restday_ot_amount': 0,
                            'month_half_period': self.payroll_month_quarter ,
                            'month_name_period': self.payroll_month_of ,
                            'year_payroll_period': PAYROLL_YEAR})
                    employee_attendance_info.computed_payroll = True
                else:
                    payroll_employees = payroll_detail.search([('payroll_detail_id', '=', self.id),
                                                               ('employee_id','=',employee_attendance_info.employee_reliever.id)])
                    if employee_attendance_info.computed_payroll == False:
                        payroll_employee.write({
                                'basic_pay_perday': payroll_employees.basic_pay_perday + employee_attendance_info.regular_days_work,
                                'reg_otpay_perhour': payroll_employees.reg_otpay_perhour + employee_attendance_info.regular_overtime,
                                'reg_nightdiff_perhour':payroll_employees.reg_nightdiff_perhour + employee_attendance_info.night_differential,
                                'reg_straightduty_perhour':payroll_employees.reg_straightduty_perhour + employee_attendance_info.straight_duty,
                                'reg_hol_pay_perday':payroll_employees.reg_hol_pay_perday + employee_attendance_info.legal_holiday_day,
                                'reg_hol_work_pay_perhour':payroll_employees.reg_hol_work_pay_perhour + employee_attendance_info.holiday_day_work,
                                'reg_hol_otpay_perhour':payroll_employees.reg_hol_otpay_perhour + employee_attendance_info.holiday_overtime,
                                'reg_spechol_perhour':payroll_employees.reg_spechol_perhour + employee_attendance_info.special_day_work,
                                'reg_spechol_otpay_perhour':payroll_employees.reg_spechol_otpay_perhour + employee_attendance_info.special_overtime,
                                'tardiness':payroll_employees.tardiness + employee_attendance_info.tardiness,
                                'undertime':payroll_employees.undertime + employee_attendance_info.undertime,
                                'basic_pay_leaves_perhour':payroll_employees.basic_pay_leaves_perhour + employee_attendance_info.leaves,
                                'basic_pay_restday_perhour':payroll_employees.basic_pay_restday_perhour + employee_attendance_info.rest_day_work,
                                'basic_pay_restday_ot_perhour':payroll_employees.basic_pay_restday_ot_perhour + employee_attendance_info.restday_overtime})
                        employee_attendance_info.computed_payroll = True

        # Get all The Payroll Detail
        payroll_details = self.env['hr.payroll.detail'].search([('payroll_detail_id', '=',self.id)])
        if len(payroll_details) > 0:
            for payroll_detail in payroll_details:
                employee_monthly_rate = round(payroll_detail.employee_id.contract_id.wage,2)
                employee_daily_rate = round(payroll_detail.employee_id.contract_id.daily_rate,2)
                employee_hourly_rate =round(payroll_detail.employee_id.contract_id.hourly_rate,2)
                employee_civil_status_raw = payroll_detail.employee_id.marital
                employee_dependent = payroll_detail.employee_id.children
                employee_payment_schedule_raw  = payroll_detail.employee_id.contract_id.schedule_pay

                curr_cola_amount = payroll_detail.employee_id.contract_id.cola_amount
                curr_allowance_amount = payroll_detail.employee_id.contract_id.amount_allowance

                if (employee_civil_status_raw in MARITAL_STATUS) and employee_dependent ==0:
                    tax_status = 'withnodependents'
                else:
                    tax_status = 'withdependents'

                if employee_payment_schedule_raw in SCHEDULE_PAY:
                    if employee_payment_schedule_raw == 'weekly':
                        employee_payment_schedule = 'weekly'
                    elif employee_payment_schedule_raw == 'bi-monthly':
                        employee_payment_schedule = 'semimonthly'
                    elif employee_payment_schedule_raw == 'monthly':
                        employee_payment_schedule = 'monthly'

                # Dictionary Initialization
                payroll_dict= {
                            'basic_pay_perday_rate': 0 ,
                            'basic_pay_amount': 0 ,
                            'reg_otpay_amount': 0 ,
                            'reg_nightdiffy_amount': 0 ,
                            'reg_straightduty_amount': 0,
                            'cola_rate_perday': 0 ,
                            'cola_amount': 0 ,
                            'reg_hol_pay_amount': 0 ,
                            'reg_hol_work_pay_amount': 0 ,
                            'reg_hol_otpay_amount': 0,
                            'reg_spechol_amount': 0 ,
                            'reg_spechol_otpay_amount': 0 ,
                            'tardiness_permin_rate': 0,
                            'tardiness_amount': 0 ,
                            'tardiness_pay_permin_rate': 0 ,
                            'undertime_amount': 0 ,
                            'gross_salary': 0 ,
                            'sss_premium': 0 ,
                            'hdmf_premium': 0 ,
                            'hmo_premium': 0 ,
                            'deductions': 0 ,
                            'net_pay': 0 ,
                            'computed_tax':0,
                            'basic_pay_leaves_amount': 0 ,
                            'basic_pay_restday_amount' :0 ,
                            'basic_pay_restday_ot_amount': 0,
                            'sss_loan': 0,
                            'hdmf_salary_loan': 0,
                            'hdmf_calamity_loan': 0,
                            'payroll_detail_date': False,
                            'basic_pay_leaves_amount': 0,
                            'allowance_rate_perday':0,
                            'allowance_amount':0,}

                # Gross
                # Daily Rate Regular Date
                payroll_dict['basic_pay_perday_rate'] = round(employee_daily_rate,2)
                payroll_dict['basic_pay_amount'] = payroll_detail.basic_pay_perday * round(employee_daily_rate,2)

                # Basic Leave
                payroll_dict['basic_pay_leaves_amount'] = payroll_detail.basic_pay_leaves_amount #payroll_detail.basic_pay_leaves_perhour * round(employee_hourly_rate,2)

                # Daily Rate OT Rate
                payroll_dict['reg_otpay_amount'] = payroll_detail.reg_otpay_perhour * round((employee_hourly_rate * regular_ot_rate_decimal),2)

                # Daily Rate NDIFF Rate

                #Incetive Leave Amount
                payroll_dict['basic_pay_leaves_amount'] = payroll_detail.basic_pay_leaves_perday * round(employee_daily_rate,2)

                # Straight Duty

                payroll_dict['reg_straightduty_amount'] = (payroll_detail.reg_straightduty_perhour) * round(employee_hourly_rate * straigthduty_nightdiff_rate_decimal,2)
                if payroll_dict['reg_straightduty_amount']  > 0:
                    curr_cola = payroll_detail.reg_straightduty_perhour * (curr_cola_amount/8.00)
                    payroll_dict['reg_straightduty_amount'] += curr_cola
                #Night Differential
                payroll_dict['reg_nightdiffy_amount'] = payroll_detail.reg_nightdiff_perhour * round(employee_hourly_rate * regular_nightdiff_rate_decimal,2)


                # Restday
                payroll_dict['basic_pay_restday_amount'] = payroll_detail.basic_pay_restday_perhour * round((employee_hourly_rate * restday_daily_rate_decimal),2)
                payroll_dict['basic_pay_restday_ot_amount'] = payroll_detail.basic_pay_restday_ot_perhour * round((employee_hourly_rate * restday_ot_rate_decimal),2)

                #Regular Holiday
                payroll_dict['reg_hol_pay_amount'] = payroll_detail.reg_hol_pay_perday * round(employee_daily_rate,2)


                employee_daily_rate_in_reg_hol = employee_hourly_rate + (curr_cola_amount/8.00)

                #round(payroll_detail.reg_hol_work_pay_perhour,2) * round((round(employee_daily_rate_in_reg_hol,2)  * round(hol_daily_rate_decimal,2)),2)
                hold_work_amount =  payroll_detail.reg_hol_work_pay_perhour * (employee_daily_rate_in_reg_hol* hol_daily_rate_decimal)  #self.getAmountWithoutRoundOff(payroll_detail.reg_hol_work_pay_perhour * (round(employee_daily_rate_in_reg_hol* hol_daily_rate_decimal,2)))
                payroll_dict['reg_hol_work_pay_amount'] = hold_work_amount
                payroll_dict['reg_hol_otpay_amount'] = round(payroll_detail.reg_hol_otpay_perhour,2) * round((round(employee_hourly_rate,2) * round(hol_ot_rate_decimal,2)),2)

                #Special Holiday
                payroll_dict['reg_spechol_amount'] = payroll_detail.reg_spechol_perhour * round((employee_hourly_rate * spec_daily_rate_decimal),2)
                payroll_dict['reg_spechol_otpay_amount'] = payroll_detail.reg_spechol_otpay_perhour *round((employee_hourly_rate * spec_ot_rate_decimal),2)

                payroll_dict['tardiness_pay_permin_rate'] = round(((employee_hourly_rate)/60) + (curr_cola_amount/constants.HOURS_PER_DAY/60) ,2)
                payroll_dict['tardiness_permin_rate'] = round(((employee_hourly_rate)/60) + (curr_cola_amount/constants.HOURS_PER_DAY/60) ,2)

                tardiness_cola = curr_cola_amount/constants.HOURS_PER_DAY/60

                payroll_dict['tardiness_amount'] = (round(payroll_detail.tardiness,2) * round(payroll_dict['tardiness_permin_rate'],2))

                payroll_dict['undertime_amount'] = round(payroll_detail.undertime,2) * round(payroll_dict['tardiness_pay_permin_rate'],2)



                # Cola Special Case
                # Employee must have a Cola even the Employee is late or UT
                # Employee have no must be Absent, Event if Absent W Leaves
                # Employee must have a Cola if he/she worked on Legal Holiday or Special Holiday
                work_in_days = payroll_detail.basic_pay_perday

                payroll_dict['cola_rate_perday'] = curr_cola_amount
                payroll_dict['cola_amount'] = (work_in_days ) * round(payroll_dict['cola_rate_perday'], 2)

                payroll_dict['allowance_rate_perday'] = curr_allowance_amount
                payroll_dict['allowance_amount'] = (work_in_days) * curr_allowance_amount

                #Gross
                #Seperate the Computation of Gross Pay
                payroll_dict['gross_salary'] = 0

                payroll_dict['gross_salary'] += (round(payroll_dict['basic_pay_amount'],2) + round(payroll_dict['basic_pay_leaves_amount'],2)) - \
                                                (round(payroll_dict['tardiness_amount'],2) + round(payroll_dict['undertime_amount'],2))

                payroll_dict['gross_salary'] += round(round(payroll_dict['basic_pay_restday_amount'],2) + \
                                                round(payroll_dict['basic_pay_restday_ot_amount'],2) + \
                                                round(payroll_dict['reg_otpay_amount'],2) + \
                                                round(payroll_dict['reg_nightdiffy_amount'],2) + \
                                                round(payroll_dict['reg_straightduty_amount'],2) + \
                                                round(payroll_dict['reg_hol_work_pay_amount'],2) + \
                                                round(payroll_dict['reg_hol_otpay_amount'],2) + \
                                                round(payroll_dict['reg_spechol_amount'],2) + \
                                                round(payroll_dict['reg_spechol_otpay_amount'],2) + \
                                                round(payroll_dict['cola_amount'],2) + \
                                                round(payroll_detail.other_incentive,2),2) + \
                                                round(payroll_dict['allowance_amount'],2)

                #Deductions
                payroll_dict['deductions'] = 0
                if payroll_dict['basic_pay_amount'] > 0:
                    if payroll_detail.is_reliever == False and payroll_detail.is_additional_employee == False:
                        if self.payroll_month_quarter == 1:
                            payroll_dict['hdmf_premium'] = round(model_gov_contrib.getPagibig(payroll_detail.employee_id.id)['EE'],2)
                            payroll_dict['hmo_premium'] = round(model_gov_contrib.getPHICDeductions(payroll_detail.employee_id.id)['EE'],2)
                        else:
                            payroll_dict['sss_premium'] = round(model_gov_contrib.getSSSDeductions(payroll_detail.employee_id.id)['EE'],2)

                        #raise Warning(payroll_dict['sss_premium'])
                        #loans
                        if payroll_detail.employee_id.sss_loans_remaining_months > 0:
                            if self.payroll_month_quarter == 2:
                                if self.payroll_month_of >= payroll_detail.employee_id.sss_loans_start_Month and \
                                   payroll_detail.year_payroll_period >= payroll_detail.employee_id.sss_loans_start_year:
                                    payroll_dict['sss_loan'] = round(payroll_detail.employee_id.sss_loans_monthly_amortization,2)
                        if payroll_detail.employee_id.pagibig_salaryloan_remaining_months > 0:
                            if self.payroll_month_quarter == 1:
                                if self.payroll_month_of >= payroll_detail.employee_id.pagibig_salaryloan_start_Month and \
                                   payroll_detail.year_payroll_period >= payroll_detail.employee_id.pagibig_salaryloan_start_year:
                                    payroll_dict['hdmf_salary_loan'] = round(payroll_detail.employee_id.pagibig_salaryloan_monthly_amortization,2)
                        if payroll_detail.employee_id.pagibig_calamityloan_remaining_months > 0:
                            if self.payroll_month_quarter == 1:
                                if self.payroll_month_of >= payroll_detail.employee_id.pagibig_calamityloan_start_Month and \
                                   payroll_detail.year_payroll_period >= payroll_detail.employee_id.pagibig_calamityloan_start_year:
                                    payroll_dict['hdmf_calamity_loan'] = round(payroll_detail.employee_id.pagibig_calamityloan_monthly_amortization,2)

                #Seperate the Contribution to Loans and Others for Easy Reading
                payroll_dict['deductions'] += round(payroll_dict['sss_premium'],2) + round(payroll_dict['hdmf_premium'],2) + round(payroll_dict['hmo_premium'],2) + round(payroll_dict['sss_loan'],2) +round(payroll_dict['hdmf_salary_loan'],2) + round(payroll_dict['hdmf_calamity_loan'],2)
                payroll_dict['deductions'] += round(payroll_detail.other_deductions,2) + round(payroll_detail.sss_loan,2) + round(payroll_detail.hdmf_salary_loan,2) + round(payroll_detail.hdmf_calamity_loan,2)

                #TAX COMPUTATION

                # Must Be Min. Wage Earner
                net_taxable_amount =0
                if employee_daily_rate <= constants.MINIMUM_WAGE_AMOUNT:
                     payroll_dict['computed_tax'] = 0
                else:
                    taxable_amount = ((round(payroll_dict['basic_pay_amount'],2) + round(payroll_dict['basic_pay_leaves_amount'],2)) - (round(payroll_dict['tardiness_amount'],2) + round(payroll_dict['undertime_amount'],2)))
                    tax_dict = model_tax.getTaxRates(taxable_amount, tax_status,employee_dependent, employee_payment_schedule)

                    #COMPUTE OF EXCESS
                    taxable_excess = (round(taxable_amount,2) - round(tax_dict['EXEMPTION_AMOUNT'],2))

                    taxable_excess = round(taxable_excess,2) + round(payroll_dict['reg_otpay_amount'],2) \
                                    + round(payroll_dict['basic_pay_restday_amount'],2) \
                                    + round(payroll_dict['basic_pay_restday_ot_amount'],2) \
                                    + round(payroll_dict['reg_nightdiffy_amount'],2) \
                                    + round(payroll_dict['reg_straightduty_amount'],2) \
                                    + round(payroll_dict['reg_hol_pay_amount'],2) \
                                    + round(payroll_dict['reg_hol_otpay_amount'],2) \
                                    + round(payroll_dict['reg_spechol_otpay_amount'],2)

                    taxable_excess = round(taxable_excess,2) * tax_dict['RATE_EXCESS']
                    net_taxable_amount = round(tax_dict['TAX'],2) + round(taxable_excess,2)


                    payroll_dict['computed_tax'] = round(net_taxable_amount,2)

                payroll_dict['deductions'] = round(round(payroll_dict['deductions'],2) + round(payroll_dict['computed_tax'],2),2)
                #Net pay
                payroll_dict['net_pay'] = round((round(payroll_dict['gross_salary'],2) - round(payroll_dict['deductions'],2)) - round(net_taxable_amount,2),2)
                if payroll_detail.month_half_period == 1:
                    str_date ='-01'
                else:
                    str_date ='-16'

                str_date =  str(payroll_detail.year_payroll_period) + '-' + str(constants.MONTH_SELECTION[payroll_detail.month_name_period-1][0]) + str_date
                dt_detail_date =datetime.datetime.strptime(str_date, '%Y-%m-%d')
                payroll_dict['payroll_detail_date'] = dt_detail_date

                #Update
                payroll_detail.write(payroll_dict)

        self.createDeductionIncentive()
        self.computeSummary()
        res = {
                'type': 'ir.actions.client',
                'tag': 'reload'}
        model_audit.createAuditTrailForPayrollGeneration('Payroll Generate','Payroll Generation for the Payroll ' + self.name,
                                                         self._uid,
                                                         'Payroll',
                                                         self.name,
                                                         'Payroll Computation',
                                                         '','',
                                                         self.id)
        message ="""<span>Payroll</span>
                    <div><b>Status</b>: Payroll Generation </div>
                    <div><b>Made by</b>: %(user)s </div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)


        return res

    @api.one
    def postApproved(self):

        payroll = self.env['hr.payroll.main'].search([('payroll_month_of','=', self.payroll_month_of),
                                                      ('payroll_month_quarter','=', self.payroll_month_quarter),
                                                      ('state','=', 'approved'),
                                                      ('payroll_attendance', '=', self.payroll_attendance.id)])
        for payroll_main in payroll:
            if datetime.datetime.strptime(payroll_main.payroll_releasedate,'%Y-%m-%d').year \
                    == datetime.datetime.strptime(self.payroll_releasedate,'%Y-%m-%d').year:
                raise Warning('Selected period has already been Approved')

        intRemainingLoan = 0
        if len(self.payroll_main_id) > 0:
            if self.payroll_month_quarter == 1:
                 for employee in self.payroll_main_id:
                    if employee.hdmf_salary_loan > 0:
                        intRemainingLoan = employee.employee_id.pagibig_salaryloan_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'pagibig_salaryloan_remaining_months':intRemainingLoan})
                    if employee.hdmf_calamity_loan > 0:
                        intRemainingLoan = employee.employee_id.pagibig_calamityloan_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'pagibig_calamityloan_remaining_months':intRemainingLoan})
            else:
                 for employee in self.payroll_main_id:
                    if employee.sss_loan > 0:
                        intRemainingLoan = employee.employee_id.sss_loans_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'sss_loans_remaining_months':intRemainingLoan})

        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrailForPayrollGeneration('Payroll Approval',
                                                         'Payroll Approval for the Payroll ' + self.name,
                                                         self._uid,
                                                         'Payroll',
                                                         self.name,
                                                         'Payroll Approval',
                                                         'Draft','Approved',
                                                         self.id)

        message ="""<span>Payroll</span>
                    <div><b>Status</b>: Draft-> Approved </div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approved Payroll</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = ATTENDANCE_RIGHTS_STATUS[1][0]

    @api.one
    def readyforBilling(self):

        payroll = self.env['hr.payroll.main'].search([('payroll_month_of','=', self.payroll_month_of),
                                                      ('payroll_month_quarter','=', self.payroll_month_quarter),
                                                      ('state','=', 'post'),
                                                      ('payroll_attendance', '=', self.payroll_attendance.id)])
        for payroll_main in payroll:
            if datetime.datetime.strptime(payroll_main.payroll_releasedate,'%Y-%m-%d').year \
                    == datetime.datetime.strptime(self.payroll_releasedate,'%Y-%m-%d').year:
                raise Warning('Selected period has already been paid')


        message ="""<span>Payroll</span>
                    <div><b>Status</b>: Approved->Ready for Billing  </div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Ready for Billing</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)
        intRemainingLoan = 0
        if len(self.payroll_main_id) > 0:
            if self.payroll_month_quarter == 1:
                 for employee in self.payroll_main_id:
                    if employee.hdmf_salary_loan > 0:
                        intRemainingLoan = employee.employee_id.pagibig_salaryloan_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'pagibig_salaryloan_remaining_months':intRemainingLoan})
                    if employee.hdmf_calamity_loan > 0:
                        intRemainingLoan = employee.employee_id.pagibig_calamityloan_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'pagibig_calamityloan_remaining_months':intRemainingLoan})
            else:
                 for employee in self.payroll_main_id:
                    if employee.sss_loan > 0:
                        intRemainingLoan = employee.employee_id.sss_loans_remaining_months
                        intRemainingLoan -=1
                        employee.employee_id.write({'sss_loans_remaining_months':intRemainingLoan})


        self.state = ATTENDANCE_RIGHTS_STATUS[2][0]

    @api.one
    def reCheck(self):

        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrailForPayrollGeneration('Payroll Rechecking',
                                                         'Payroll Rechecking for the Payroll ' + self.name,
                                                         self._uid,
                                                         'Payroll',
                                                         self.name,
                                                         'Payroll Recheck',
                                                         'Approved','Draft',
                                                         self.id)
        message ="""<span>Payroll</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of Payroll</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        intRemainingLoan = 0
        if len(self.payroll_main_id) > 0:
            if self.payroll_month_quarter == 1:
                for employee in self.payroll_main_id:
                    if employee.basic_pay_amount > 0:
                        if employee.hdmf_salary_loan > 0:
                            intRemainingLoan = employee.employee_id.pagibig_salaryloan_remaining_months
                            intRemainingLoan +=1
                            employee.employee_id.write({'pagibig_salaryloan_remaining_months':intRemainingLoan})
                        if employee.hdmf_calamity_loan > 0:
                            intRemainingLoan = employee.employee_id.pagibig_calamityloan_remaining_months
                            intRemainingLoan +=1
                            employee.employee_id.write({'pagibig_calamityloan_remaining_months':intRemainingLoan})
            else:
                for employee in self.payroll_main_id:
                    if employee.basic_pay_amount > 0:
                        if employee.sss_loan > 0:
                            intRemainingLoan = employee.employee_id.sss_loans_remaining_months
                            intRemainingLoan +=1
                            employee.employee_id.write({'sss_loans_remaining_months':intRemainingLoan})

        self.state = ATTENDANCE_RIGHTS_STATUS[0][0]


    @api.one
    def generateExcelFile(self):
        # Getting all The Rate of Work Type
        work_hour_type = self.env['hr.workhourtype']

        regular_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('DRATE')
        regular_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('ROT')
        regular_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('NDIFF')
        restday_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTDRATE')
        restday_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTOT')
        restday_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTNDIFF')
        spec_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHDRATE')
        spec_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHOT')
        restday_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHNDIFF')
        hol_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHDRATE')
        hol_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHOT')
        hol_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHNDIFF')
        straigthduty_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('STRDUTY')

        str_dir = constants.GenXUtils.get_data_dir_excel_template
        model_payroll_details = self.env['hr.payroll.detail'].search([('payroll_detail_id','=',self.id)])
        model_payroll_detail = model_payroll_details.sorted(key=lambda r: r.employee_id.last_name)
        workbook_xlrd = xlrd.open_workbook(str_dir + 'Payroll.xls', formatting_info=True)
        workbook = copy(workbook_xlrd)
        if len(model_payroll_detail) > 0:
            styleColumns =xlwt.XFStyle()
            styleColumns1 =xlwt.XFStyle()
            styleColumnsString =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border
            styleColumnsString.borders = border
            styleColumns.num_format_str ="#,##0.00"
            styleColumns1.num_format_str ="#,##0.00"
            sheet_xlrd = workbook_xlrd.sheet_by_index(0)
            sheet = workbook.get_sheet(0)
            int_rowindex = 10
            #Title

            sheet.write(2,4,self.payroll_attendance.assign_projects.name)
            sheet.write(3,4,str(self.payroll_attendance.schedule_datefrom) + ' - ' + str(self.payroll_attendance.schedule_dateto))
            sheet.write(4,4,self.payroll_releasedate)

            for employee in model_payroll_detail:
                if len(employee.employee_id.bank_account_id) > 0:
                    for intColumn in range(1,20):
                        sheet.write(int_rowindex, intColumn,"")
                    curr_employee_daily_rate = round(employee.employee_id.contract_id.daily_rate,2)

                    sheet.write(int_rowindex,1,"",styleColumns )
                    sheet.write_merge(int_rowindex,int_rowindex,2,3,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumnsString)
                    sheet.write(int_rowindex,4,employee.basic_pay_perday,styleColumns )
                    sheet.write(int_rowindex,5,employee.basic_pay_perday_rate,styleColumns )
                    sheet.write(int_rowindex,6,employee.basic_pay_amount,styleColumns )
                    sheet.write(int_rowindex,7,employee.tardiness + employee.undertime,styleColumns)
                    sheet.write(int_rowindex,8,employee.tardiness_pay_permin_rate ,styleColumns)
                    sheet.write(int_rowindex,9,employee.undertime_amount + employee.tardiness_amount ,styleColumns)
                    sheet.write(int_rowindex,10,employee.reg_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,11,round((curr_employee_daily_rate/8,2) * regular_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,12,employee.reg_otpay_amount,styleColumns)
                    sheet.write(int_rowindex,13,employee.cola_rate_perday,styleColumns)
                    sheet.write(int_rowindex,14,employee.cola_amount,styleColumns)
                    sheet.write(int_rowindex,15,employee.gross_salary,styleColumns)
                    sheet.write(int_rowindex,16,employee.sss_premium,styleColumns)
                    sheet.write(int_rowindex,17,employee.sss_loan,styleColumns)

                    sheet.write(int_rowindex,18,employee.hdmf_premium,styleColumns)
                    sheet.write(int_rowindex,19,employee.hdmf_salary_loan,styleColumns)
                    sheet.write(int_rowindex,20,employee.hdmf_calamity_loan,styleColumns)
                    sheet.write(int_rowindex,21,employee.hmo_premium,styleColumns)
                    sheet.write(int_rowindex,22,employee.other_deductions ,styleColumns)
                    sheet.write(int_rowindex,23,employee.deductions,styleColumns)
                    sheet.write(int_rowindex,24,employee.net_pay,styleColumns)
                    int_rowindex +=1

            #Summary Debit
            curr_basic_pay_amount = 0
            curr_ot_amount = 0
            curr_gross_salary = 0
            curr_sss_premium =0
            curr_sss_loan =0
            curr_net = 0
            curr_under_time = 0
            curr_cola = 0
            curr_deduction = 0
            total_gross_debit = 0
            total_gross_check =0

            curr_hdmf_premium = 0
            curr_hdmf_salary_loan = 0
            curr_hdmf_calamity_loan = 0
            curr_hmo_premium = 0
            curr_other_deductions = 0
            for employee in model_payroll_detail:
                for intColumn in range(1,20):
                    sheet.write(int_rowindex, intColumn,"")
                if len(employee.employee_id.bank_account_id) > 0:
                    curr_basic_pay_amount += employee.basic_pay_amount
                    curr_under_time += employee.undertime_amount + employee.tardiness_amount
                    curr_ot_amount += employee.reg_otpay_amount
                    curr_gross_salary +=employee.gross_salary
                    curr_sss_premium += employee.sss_premium
                    curr_sss_loan += employee.sss_loan
                    curr_cola +=employee.cola_amount
                    curr_hdmf_premium += employee.hdmf_premium
                    curr_hdmf_salary_loan += employee.hdmf_salary_loan
                    curr_hdmf_calamity_loan += employee.hdmf_calamity_loan
                    curr_hmo_premium += employee.hmo_premium
                    curr_other_deductions += employee.other_deductions
                    curr_deduction += employee.deductions
                    curr_net += employee.net_pay


                sheet.write(int_rowindex,6,curr_basic_pay_amount)
                sheet.write(int_rowindex,9,curr_under_time)
                sheet.write(int_rowindex,12,curr_ot_amount)
                sheet.write(int_rowindex,14,curr_cola)
                sheet.write(int_rowindex,15,curr_gross_salary)
                sheet.write(int_rowindex,16,curr_sss_premium)
                sheet.write(int_rowindex,17,curr_sss_loan)

                sheet.write(int_rowindex,18,curr_hdmf_premium)
                sheet.write(int_rowindex,19,curr_hdmf_salary_loan)
                sheet.write(int_rowindex,20,curr_hdmf_calamity_loan)
                sheet.write(int_rowindex,21,curr_hmo_premium)
                sheet.write(int_rowindex,22,curr_other_deductions)
                sheet.write(int_rowindex,23,curr_deduction)
                sheet.write(int_rowindex,24,curr_net)

                #sheet.write(int_rowindex,18,curr_deduction)
                #sheet.write(int_rowindex,19,curr_net)
            int_rowindex +=2
            total_gross_debit = curr_gross_salary

            for employee in model_payroll_detail:
                if len(employee.employee_id.bank_account_id) == 0:
                    for intColumn in range(1,20):
                        sheet.write(int_rowindex, intColumn,"")

                    curr_employee_daily_rate = employee.employee_id.contract_id.daily_rate

                    sheet.write(int_rowindex,1,"",styleColumns )
                    sheet.write_merge(int_rowindex,int_rowindex,2,3,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)
                    sheet.write(int_rowindex,4,employee.basic_pay_perday,styleColumns )
                    sheet.write(int_rowindex,5,employee.basic_pay_perday_rate,styleColumns )
                    sheet.write(int_rowindex,6,employee.basic_pay_amount,styleColumns )
                    sheet.write(int_rowindex,7,employee.tardiness + employee.undertime,styleColumns)
                    sheet.write(int_rowindex,8,employee.tardiness_pay_permin_rate ,styleColumns)
                    sheet.write(int_rowindex,9,employee.undertime_amount + employee.tardiness_amount ,styleColumns)
                    sheet.write(int_rowindex,10,employee.reg_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,11,round((curr_employee_daily_rate/8) * regular_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,12,employee.reg_otpay_amount,styleColumns)
                    sheet.write(int_rowindex,13,employee.cola_rate_perday,styleColumns)
                    sheet.write(int_rowindex,14,employee.cola_amount,styleColumns)
                    sheet.write(int_rowindex,15,employee.gross_salary,styleColumns)
                    sheet.write(int_rowindex,16,employee.sss_premium,styleColumns)
                    sheet.write(int_rowindex,17,employee.sss_loan,styleColumns)

                    sheet.write(int_rowindex,18,employee.hdmf_premium,styleColumns)
                    sheet.write(int_rowindex,19,employee.hdmf_salary_loan,styleColumns)
                    sheet.write(int_rowindex,20,employee.hdmf_calamity_loan,styleColumns)
                    sheet.write(int_rowindex,21,employee.hmo_premium,styleColumns)
                    sheet.write(int_rowindex,22,employee.other_deductions ,styleColumns)
                    sheet.write(int_rowindex,23,employee.deductions,styleColumns)
                    sheet.write(int_rowindex,24,employee.net_pay,styleColumns)
                    int_rowindex +=1

            #Summary Check
            curr_basic_pay_amount = 0
            curr_ot_amount = 0
            curr_gross_salary = 0
            curr_sss_premium =0
            curr_sss_loan =0
            curr_net = 0
            curr_under_time = 0
            curr_cola = 0
            curr_deduction = 0
            total_gross_debit = 0
            total_gross_check =0

            curr_hdmf_premium = 0
            curr_hdmf_salary_loan = 0
            curr_hdmf_calamity_loan = 0
            curr_hmo_premium = 0
            curr_other_deductions = 0
            for employee in model_payroll_detail:
                if len(employee.employee_id.bank_account_id)  == 0:
                    for intColumn in range(1,20):
                        sheet.write(int_rowindex, intColumn,"")
                    curr_basic_pay_amount += employee.basic_pay_amount
                    curr_under_time += employee.undertime_amount + employee.tardiness_amount
                    curr_ot_amount += employee.reg_otpay_amount
                    curr_gross_salary +=employee.gross_salary
                    curr_sss_premium += employee.sss_premium
                    curr_sss_loan += employee.sss_loan
                    curr_cola +=employee.cola_amount
                    curr_hdmf_premium += employee.hdmf_premium
                    curr_hdmf_salary_loan += employee.hdmf_salary_loan
                    curr_hdmf_calamity_loan += employee.hdmf_calamity_loan
                    curr_hmo_premium += employee.hmo_premium
                    curr_other_deductions += employee.other_deductions
                    curr_deduction += employee.deductions
                    curr_net += employee.net_pay

                sheet.write(int_rowindex,6,round(curr_basic_pay_amount,2),styleColumns1)
                sheet.write(int_rowindex,9,round(curr_under_time,2),styleColumns1)
                sheet.write(int_rowindex,12,round(curr_ot_amount,2),styleColumns1)
                sheet.write(int_rowindex,14,round(curr_cola,2),styleColumns1)
                sheet.write(int_rowindex,15,round(curr_gross_salary,2),styleColumns1)
                sheet.write(int_rowindex,16,round(curr_sss_premium,2),styleColumns1)
                sheet.write(int_rowindex,17,round(curr_sss_loan,2),styleColumns1)

                sheet.write(int_rowindex,18,round(curr_hdmf_premium,2),styleColumns1)
                sheet.write(int_rowindex,19,round(curr_hdmf_salary_loan,2),styleColumns1)
                sheet.write(int_rowindex,20,round(curr_hdmf_calamity_loan,2),styleColumns1)
                sheet.write(int_rowindex,21,round(curr_hmo_premium,2),styleColumns1)
                sheet.write(int_rowindex,22,round(curr_other_deductions,2),styleColumns1)
                sheet.write(int_rowindex,23,round(curr_deduction,2),styleColumns1)
                sheet.write(int_rowindex,24,round(curr_net,2),styleColumns1)

            int_rowindex +=3
            total_gross_check = round(curr_gross_salary,2)

            #Totals
            sheet.write_merge(int_rowindex,int_rowindex,2,3,"TOTALS")
            sheet.write(int_rowindex,6, round(sum(employee.basic_pay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,9, round(sum(employee.undertime_amount + employee.tardiness_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,12,round(sum(employee.reg_otpay_amount for employee in model_payroll_detail),2),styleColumns1 )
            sheet.write(int_rowindex,14,round(sum(employee.cola_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,15,round(sum(employee.gross_salary for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,16,round(sum(employee.sss_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,17,round(sum(employee.sss_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,18,round(sum(employee.hdmf_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,19,round(sum(employee.hdmf_salary_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,20,round(sum(employee.hdmf_calamity_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,21,round(sum(employee.hmo_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,22,round(sum(employee.other_deductions for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,23,round(sum(employee.deductions for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,24,round(sum(employee.net_pay for employee in model_payroll_detail),2),styleColumns1)
            int_rowindex +=2

            sheet.write(int_rowindex,15,round(total_gross_check,2),styleColumns1)
            int_rowindex +=1
            sheet.write(int_rowindex,15,round(total_gross_debit,2),styleColumns1)

            int_rowindex +=2
            sheet.write(int_rowindex,15,round(total_gross_check + total_gross_debit,2),styleColumns1)


        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.payroll_file = byte_arr

    @api.one
    def generateExcelFile2(self):
        # Getting all The Rate of Work Type
        work_hour_type = self.env['hr.workhourtype']

        regular_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('DRATE')
        regular_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('ROT')
        regular_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('NDIFF')
        restday_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTDRATE')
        restday_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTOT')
        restday_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('RESTNDIFF')
        spec_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHDRATE')
        spec_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHOT')
        restday_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('SPEHNDIFF')
        hol_daily_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHDRATE')
        hol_ot_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHOT')
        hol_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('REGHNDIFF')
        straigthduty_nightdiff_rate_decimal = work_hour_type.getWorkHourRateinDecimal('STRDUTY')

        str_dir = constants.GenXUtils.get_data_dir_excel_template
        model_payroll_details = self.env['hr.payroll.detail'].search([('payroll_detail_id','=',self.id)])
        model_payroll_detail = model_payroll_details.sorted(key=lambda r: r.employee_id.last_name)
        workbook_xlrd = xlrd.open_workbook(str_dir + 'Payroll - New.xls', formatting_info=True)
        #workbook_xlrd = xl.open_workbook(str_dir + 'Payroll - New.xls', formatting_info=True)

        #x = xlwt.Worksheet.set_po
        workbook = copy(workbook_xlrd)
        if len(model_payroll_detail) > 0:

            styleColumns =xlwt.XFStyle()
            styleColumns1 =xlwt.XFStyle()
            styleColumnsString =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border
            styleColumnsString.borders = border
            styleColumns.num_format_str ="#,##0.00"
            styleColumns1.num_format_str ="#,##0.00"
            sheet_xlrd = workbook_xlrd.sheet_by_index(0)

            #curr_allowance_amount = .employee_id.contract_id.amount_allowance

            sheet = workbook.get_sheet(0)
            int_rowindex = 8
            sheet.set_portrait(False)
            sheet.paper_size_code = 5
            #Title
            sheet.write(1,5,self.payroll_attendance.company_assign.name)
            sheet.write(2,5,str(self.payroll_attendance.schedule_datefrom) + ' - ' + str(self.payroll_attendance.schedule_dateto))
            #sheet.write(4,4,self.payroll_releasedate)
            #employee.cola_rate_perday
            for employee in model_payroll_detail:
                if len(employee.employee_id.bank_account_id) > 0:
                    for intColumn in range(1,20):
                        sheet.write(int_rowindex, intColumn,"")
                    curr_employee_daily_rate = round(employee.employee_id.contract_id.daily_rate,2)

                    sheet.write(int_rowindex,1,"",styleColumns )
                    sheet.write_merge(int_rowindex,int_rowindex,2,3,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumnsString)
                    sheet.write(int_rowindex,4,employee.basic_pay_perday,styleColumns )
                    sheet.write(int_rowindex,5,employee.basic_pay_perday_rate,styleColumns )
                    sheet.write(int_rowindex,6,employee.basic_pay_amount,styleColumns )

                    #Rest Day
                    sheet.write(int_rowindex,7,employee.basic_pay_restday_perhour,styleColumns)
                    sheet.write(int_rowindex,8,round(round(curr_employee_daily_rate/8,2) * restday_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,9,employee.basic_pay_restday_amount ,styleColumns)

                    sheet.write(int_rowindex,10,employee.basic_pay_restday_ot_perhour,styleColumns)
                    sheet.write(int_rowindex,11,round(round(curr_employee_daily_rate/8,2) * restday_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,12,employee.basic_pay_restday_ot_amount,styleColumns)

                    #Regular Holiday
                    sheet.write(int_rowindex,13,employee.reg_hol_pay_perday,styleColumns)
                    sheet.write(int_rowindex,14,employee.reg_hol_pay_amount,styleColumns)
                    employee_daily_rate_in_reg_hol = ((curr_employee_daily_rate + employee.cola_rate_perday)/8.00)

                    sheet.write(int_rowindex,15,employee.reg_hol_work_pay_perhour,styleColumns)
                    sheet.write(int_rowindex,16,round(employee_daily_rate_in_reg_hol * hol_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,17,employee.reg_hol_work_pay_amount ,styleColumns)

                    sheet.write(int_rowindex,18,employee.reg_hol_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,19,round(round(curr_employee_daily_rate/8,2) * hol_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,20,employee.reg_hol_otpay_amount,styleColumns)

                    #Special
                    sheet.write(int_rowindex,21,employee.reg_spechol_perhour,styleColumns)
                    sheet.write(int_rowindex,22,round(round(curr_employee_daily_rate/8,2) * spec_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,23,employee.reg_spechol_amount ,styleColumns)

                    sheet.write(int_rowindex,24,employee.reg_spechol_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,25,round(round(curr_employee_daily_rate/8,2) * spec_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,26,employee.reg_spechol_otpay_amount,styleColumns)


                    #Tardiness SDS
                    sheet.write(int_rowindex,27,employee.tardiness + employee.undertime,styleColumns)
                    sheet.write(int_rowindex,28,employee.tardiness_pay_permin_rate ,styleColumns)
                    sheet.write(int_rowindex,29,employee.undertime_amount + employee.tardiness_amount ,styleColumns)

                    sheet.write(int_rowindex,30,employee.reg_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,31,round(round(curr_employee_daily_rate/8,2) * regular_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,32,employee.reg_otpay_amount,styleColumns)

                    #Night Differential
                    sheet.write(int_rowindex,33,employee.reg_nightdiff_perhour,styleColumns)
                    sheet.write(int_rowindex,34,round(round(curr_employee_daily_rate/8,2) * regular_nightdiff_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,35,employee.reg_nightdiffy_amount,styleColumns)

                    #Straigth Duty
                    employee_daily_rate_in_straight_duty = ((curr_employee_daily_rate + employee.cola_rate_perday)/8.00)
                    sheet.write(int_rowindex,36,employee.reg_straightduty_perhour,styleColumns)
                    sheet.write(int_rowindex,37,round(employee_daily_rate_in_straight_duty * straigthduty_nightdiff_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,38,employee.reg_straightduty_amount,styleColumns)


                    sheet.write(int_rowindex,39,employee.cola_rate_perday,styleColumns)
                    sheet.write(int_rowindex,40,employee.cola_amount,styleColumns)

                    sheet.write(int_rowindex,41,employee.allowance_rate_perday,styleColumns)
                    sheet.write(int_rowindex,42,employee.allowance_amount,styleColumns)

                    sheet.write(int_rowindex,43,employee.basic_pay_leaves_perday,styleColumns)
                    sheet.write(int_rowindex,44,employee.basic_pay_leaves_amount,styleColumns)

                    sheet.write(int_rowindex,45,employee.other_incentive,styleColumns)
                    sheet.write(int_rowindex,46,employee.gross_salary,styleColumns)

                    sheet.write(int_rowindex,47,employee.sss_premium,styleColumns)
                    sheet.write(int_rowindex,48,employee.sss_loan,styleColumns)

                    sheet.write(int_rowindex,49,employee.hdmf_premium,styleColumns)
                    sheet.write(int_rowindex,50,employee.hdmf_salary_loan,styleColumns)
                    sheet.write(int_rowindex,51,employee.hdmf_calamity_loan,styleColumns)

                    sheet.write(int_rowindex,52,employee.hmo_premium,styleColumns)
                    sheet.write(int_rowindex,53,employee.computed_tax,styleColumns)

                    sheet.write(int_rowindex,54,employee.other_deductions ,styleColumns)
                    sheet.write(int_rowindex,55,employee.deductions,styleColumns)
                    sheet.write(int_rowindex,56,employee.net_pay,styleColumns)
                    int_rowindex +=1

            #Summary Debit
            curr_basic_pay_amount = 0

            curr_restday = 0.00
            curr_restday_ot = 0.00

            curr_reg_hol = 0.00
            curr_reg_hol_work = 0.00
            curr_reg_hol_ot = 0.00

            curr_spec_hol_work = 0.00
            curr_spec_hol_ot = 0.00

            curr_ot_amount = 0

            curr_night_diff = 0.00
            curr_straight = 0.00

            curr_other = 0.00

            curr_gross_salary = 0
            curr_sss_premium =0
            curr_sss_loan =0
            curr_net = 0
            curr_under_time = 0
            curr_cola = 0
            curr_deduction = 0
            total_gross_debit = 0
            total_gross_check =0

            curr_hdmf_premium = 0
            curr_hdmf_salary_loan = 0
            curr_hdmf_calamity_loan = 0
            curr_hmo_premium = 0
            curr_other_deductions = 0
            curr_allowance = 0
            curr_leaves_amount = 0
            curr_witholding_tax =0
            for employee in model_payroll_detail:
                for intColumn in range(1,20):
                    sheet.write(int_rowindex, intColumn,"")
                if len(employee.employee_id.bank_account_id) > 0:
                    curr_basic_pay_amount += employee.basic_pay_amount

                    curr_restday += employee.basic_pay_restday_amount
                    curr_restday_ot  += employee.basic_pay_restday_ot_amount

                    curr_reg_hol += employee.reg_hol_pay_amount
                    curr_reg_hol_work += employee.reg_hol_work_pay_amount
                    curr_reg_hol_ot += employee.reg_hol_otpay_amount

                    curr_spec_hol_work += employee.reg_spechol_amount
                    curr_spec_hol_ot += employee.reg_spechol_otpay_amount

                    curr_night_diff += employee.reg_nightdiffy_amount
                    curr_straight += employee.reg_straightduty_amount

                    curr_other += employee.other_incentive


                    curr_under_time += employee.undertime_amount + employee.tardiness_amount
                    curr_ot_amount += employee.reg_otpay_amount
                    curr_gross_salary +=employee.gross_salary
                    curr_sss_premium += employee.sss_premium
                    curr_sss_loan += employee.sss_loan
                    curr_cola +=employee.cola_amount
                    curr_hdmf_premium += employee.hdmf_premium
                    curr_hdmf_salary_loan += employee.hdmf_salary_loan
                    curr_hdmf_calamity_loan += employee.hdmf_calamity_loan
                    curr_hmo_premium += employee.hmo_premium
                    curr_other_deductions += employee.other_deductions
                    curr_deduction += employee.deductions
                    curr_net += employee.net_pay
                    curr_allowance += employee.allowance_amount
                    curr_leaves_amount += employee.basic_pay_leaves_amount
                    curr_witholding_tax += employee.computed_tax

                sheet.write_merge(int_rowindex,int_rowindex,2,3, "Subtotal ( Debit Card)")
                sheet.write(int_rowindex,6,curr_basic_pay_amount,styleColumns1)

                sheet.write(int_rowindex,9,curr_restday,styleColumns1)
                sheet.write(int_rowindex,12,curr_restday_ot,styleColumns1)

                sheet.write(int_rowindex,14,curr_reg_hol,styleColumns1)
                sheet.write(int_rowindex,17,curr_reg_hol_work,styleColumns1)
                sheet.write(int_rowindex,20,curr_reg_hol_ot,styleColumns1)

                sheet.write(int_rowindex,23,curr_spec_hol_work,styleColumns1)
                sheet.write(int_rowindex,26,curr_spec_hol_ot,styleColumns1)

                sheet.write(int_rowindex,29,curr_under_time,styleColumns1)

                sheet.write(int_rowindex,32,curr_ot_amount,styleColumns1)

                sheet.write(int_rowindex,35,curr_night_diff,styleColumns1)
                sheet.write(int_rowindex,38,curr_straight,styleColumns1)

                sheet.write(int_rowindex,40,curr_cola,styleColumns1)
                sheet.write(int_rowindex,42,curr_allowance,styleColumns1)

                sheet.write(int_rowindex,44,curr_leaves_amount,styleColumns1)

                sheet.write(int_rowindex,45,curr_other,styleColumns1)
                sheet.write(int_rowindex,46,curr_gross_salary,styleColumns1)

                sheet.write(int_rowindex,47,curr_sss_premium,styleColumns1)
                sheet.write(int_rowindex,48,curr_sss_loan,styleColumns1)

                sheet.write(int_rowindex,49,curr_hdmf_premium,styleColumns1)
                sheet.write(int_rowindex,50,curr_hdmf_salary_loan,styleColumns1)
                sheet.write(int_rowindex,51,curr_hdmf_calamity_loan,styleColumns1)
                sheet.write(int_rowindex,52,curr_hmo_premium,styleColumns1)
                sheet.write(int_rowindex,53,curr_witholding_tax,styleColumns1)

                sheet.write(int_rowindex,54,curr_other_deductions,styleColumns1)
                sheet.write(int_rowindex,55,curr_deduction,styleColumns1)
                sheet.write(int_rowindex,56,curr_net,styleColumns1)

            int_rowindex +=2
            total_gross_debit = curr_gross_salary
            total_net_debit = curr_net

            #FOR CHECK
            for employee in model_payroll_detail:
                if len(employee.employee_id.bank_account_id) == 0:
                    for intColumn in range(1,20):
                        sheet.write(int_rowindex, intColumn,"")

                    curr_employee_daily_rate = round(employee.employee_id.contract_id.daily_rate,2)

                    sheet.write(int_rowindex,1,"",styleColumns )
                    sheet.write_merge(int_rowindex,int_rowindex,2,3,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumnsString)
                    sheet.write(int_rowindex,4,employee.basic_pay_perday,styleColumns )
                    sheet.write(int_rowindex,5,employee.basic_pay_perday_rate,styleColumns )
                    sheet.write(int_rowindex,6,employee.basic_pay_amount,styleColumns )

                    #Rest Day
                    sheet.write(int_rowindex,7,employee.basic_pay_restday_perhour,styleColumns)
                    sheet.write(int_rowindex,8,round(round(curr_employee_daily_rate/8,2) * restday_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,9,employee.basic_pay_restday_amount ,styleColumns)

                    sheet.write(int_rowindex,10,employee.basic_pay_restday_ot_perhour,styleColumns)
                    sheet.write(int_rowindex,11,round(round(curr_employee_daily_rate/8,2) * restday_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,12,employee.basic_pay_restday_ot_amount,styleColumns)

                    #Regular Holiday
                    sheet.write(int_rowindex,13,employee.reg_hol_pay_perday,styleColumns)
                    sheet.write(int_rowindex,14,employee.reg_hol_pay_amount,styleColumns)

                    employee_daily_rate_in_reg_hol = ((curr_employee_daily_rate + employee.cola_rate_perday)/8.00)
                    sheet.write(int_rowindex,15,employee.reg_hol_work_pay_perhour,styleColumns)
                    sheet.write(int_rowindex,16,round(employee_daily_rate_in_reg_hol * hol_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,17,employee.reg_hol_work_pay_amount ,styleColumns)

                    sheet.write(int_rowindex,18,employee.reg_hol_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,19,round(round(curr_employee_daily_rate/8,2) * hol_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,20,employee.reg_hol_otpay_amount,styleColumns)

                    #Special
                    sheet.write(int_rowindex,21,employee.reg_spechol_perhour,styleColumns)
                    sheet.write(int_rowindex,22,round(round(curr_employee_daily_rate/8,2) * spec_daily_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,23,employee.reg_spechol_amount ,styleColumns)

                    sheet.write(int_rowindex,24,employee.reg_spechol_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,25,round(round(curr_employee_daily_rate/8,2) * spec_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,26,employee.reg_spechol_otpay_amount,styleColumns)



                    sheet.write(int_rowindex,27,employee.tardiness + employee.undertime,styleColumns)
                    sheet.write(int_rowindex,28,employee.tardiness_pay_permin_rate ,styleColumns)
                    sheet.write(int_rowindex,29,employee.undertime_amount + employee.tardiness_amount ,styleColumns)

                    sheet.write(int_rowindex,30,employee.reg_otpay_perhour,styleColumns)
                    sheet.write(int_rowindex,31,round(round(curr_employee_daily_rate/8,2) * regular_ot_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,32,employee.reg_otpay_amount,styleColumns)

                    #Night Differential
                    sheet.write(int_rowindex,33,employee.reg_nightdiff_perhour,styleColumns)
                    sheet.write(int_rowindex,34,round(round(curr_employee_daily_rate/8,2) * regular_nightdiff_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,35,employee.reg_nightdiffy_amount,styleColumns)

                    #Straigth Duty
                    employee_daily_rate_in_straight_duty = ((curr_employee_daily_rate + employee.cola_rate_perday)/8.00)
                    sheet.write(int_rowindex,36,employee.reg_straightduty_perhour,styleColumns)
                    sheet.write(int_rowindex,37,round(employee_daily_rate_in_straight_duty * straigthduty_nightdiff_rate_decimal,2),styleColumns)
                    #sheet.write(int_rowindex,37,round(round(curr_employee_daily_rate/8,2) * straigthduty_nightdiff_rate_decimal,2),styleColumns)
                    sheet.write(int_rowindex,38,employee.reg_straightduty_amount,styleColumns)


                    sheet.write(int_rowindex,39,employee.cola_rate_perday,styleColumns)
                    sheet.write(int_rowindex,40,employee.cola_amount,styleColumns)

                    sheet.write(int_rowindex,41,employee.allowance_rate_perday,styleColumns)
                    sheet.write(int_rowindex,42,employee.allowance_amount,styleColumns)

                    sheet.write(int_rowindex,43,employee.basic_pay_leaves_perday,styleColumns)
                    sheet.write(int_rowindex,44,employee.basic_pay_leaves_amount,styleColumns)

                    sheet.write(int_rowindex,45,employee.other_incentive,styleColumns)
                    sheet.write(int_rowindex,46,employee.gross_salary,styleColumns)

                    sheet.write(int_rowindex,47,employee.sss_premium,styleColumns)
                    sheet.write(int_rowindex,48,employee.sss_loan,styleColumns)

                    sheet.write(int_rowindex,49,employee.hdmf_premium,styleColumns)
                    sheet.write(int_rowindex,50,employee.hdmf_salary_loan,styleColumns)
                    sheet.write(int_rowindex,51,employee.hdmf_calamity_loan,styleColumns)

                    sheet.write(int_rowindex,52,employee.hmo_premium,styleColumns)
                    sheet.write(int_rowindex,53,employee.computed_tax,styleColumns)

                    sheet.write(int_rowindex,54,employee.other_deductions ,styleColumns)
                    sheet.write(int_rowindex,55,employee.deductions,styleColumns)
                    sheet.write(int_rowindex,56,employee.net_pay,styleColumns)
                    int_rowindex +=1

            #Summary Check
            curr_basic_pay_amount = 0

            curr_restday = 0.00
            curr_restday_ot = 0.00

            curr_reg_hol = 0.00
            curr_reg_hol_work = 0.00
            curr_reg_hol_ot = 0.00

            curr_spec_hol_work = 0.00
            curr_spec_hol_ot = 0.00

            curr_ot_amount = 0

            curr_night_diff = 0.00
            curr_straight = 0.00

            curr_other = 0.00

            curr_gross_salary = 0
            curr_sss_premium =0
            curr_sss_loan =0
            curr_net = 0
            curr_under_time = 0
            curr_cola = 0
            curr_deduction = 0
            total_gross_check =0

            curr_hdmf_premium = 0
            curr_hdmf_salary_loan = 0
            curr_hdmf_calamity_loan = 0
            curr_hmo_premium = 0
            curr_other_deductions = 0
            curr_allowance = 0
            curr_leaves_amount = 0
            curr_witholding_tax = 0
            for employee in model_payroll_detail:
                for intColumn in range(1,20):
                    sheet.write(int_rowindex, intColumn,"")
                if len(employee.employee_id.bank_account_id) == 0:
                    curr_basic_pay_amount += employee.basic_pay_amount

                    curr_restday += employee.basic_pay_restday_amount
                    curr_restday_ot  += employee.basic_pay_restday_ot_amount

                    curr_reg_hol += employee.reg_hol_pay_amount
                    curr_reg_hol_work += employee.reg_hol_work_pay_amount
                    curr_reg_hol_ot += employee.reg_hol_otpay_amount

                    curr_spec_hol_work += employee.reg_spechol_amount
                    curr_spec_hol_ot += employee.reg_spechol_otpay_amount

                    curr_night_diff += employee.reg_nightdiffy_amount
                    curr_straight += employee.reg_straightduty_amount

                    curr_other += employee.other_incentive


                    curr_under_time += employee.undertime_amount + employee.tardiness_amount
                    curr_ot_amount += employee.reg_otpay_amount
                    curr_gross_salary +=employee.gross_salary
                    curr_sss_premium += employee.sss_premium
                    curr_sss_loan += employee.sss_loan
                    curr_cola +=employee.cola_amount
                    curr_hdmf_premium += employee.hdmf_premium
                    curr_hdmf_salary_loan += employee.hdmf_salary_loan
                    curr_hdmf_calamity_loan += employee.hdmf_calamity_loan
                    curr_hmo_premium += employee.hmo_premium
                    curr_other_deductions += employee.other_deductions
                    curr_deduction += employee.deductions
                    curr_net += employee.net_pay
                    curr_allowance += employee.allowance_amount
                    curr_leaves_amount += employee.basic_pay_leaves_amount
                    curr_witholding_tax += employee.computed_tax
                sheet.write_merge(int_rowindex,int_rowindex,2,3, "Subtotal ( Reliever - Check )")
                sheet.write(int_rowindex,6,curr_basic_pay_amount,styleColumns1)

                sheet.write(int_rowindex,9,curr_restday,styleColumns1)
                sheet.write(int_rowindex,12,curr_restday_ot,styleColumns1)

                sheet.write(int_rowindex,14,curr_reg_hol,styleColumns1)
                sheet.write(int_rowindex,17,curr_reg_hol_work,styleColumns1)
                sheet.write(int_rowindex,20,curr_reg_hol_ot,styleColumns1)

                sheet.write(int_rowindex,23,curr_spec_hol_work,styleColumns1)
                sheet.write(int_rowindex,26,curr_spec_hol_ot,styleColumns1)

                sheet.write(int_rowindex,29,curr_under_time,styleColumns1)

                sheet.write(int_rowindex,32,curr_ot_amount,styleColumns1)

                sheet.write(int_rowindex,35,curr_night_diff,styleColumns1)
                sheet.write(int_rowindex,38,curr_straight,styleColumns1)


                sheet.write(int_rowindex,40,curr_cola,styleColumns1)
                sheet.write(int_rowindex,42,curr_allowance,styleColumns1)
                sheet.write(int_rowindex,44,curr_leaves_amount,styleColumns1)

                sheet.write(int_rowindex,45,curr_other,styleColumns1)
                sheet.write(int_rowindex,46,curr_gross_salary,styleColumns1)

                sheet.write(int_rowindex,47,curr_sss_premium,styleColumns1)
                sheet.write(int_rowindex,48,curr_sss_loan,styleColumns1)

                sheet.write(int_rowindex,49,curr_hdmf_premium,styleColumns1)
                sheet.write(int_rowindex,50,curr_hdmf_salary_loan,styleColumns1)
                sheet.write(int_rowindex,51,curr_hdmf_calamity_loan,styleColumns1)
                sheet.write(int_rowindex,52,curr_hmo_premium,styleColumns1)
                sheet.write(int_rowindex,53,curr_witholding_tax,styleColumns1)
                sheet.write(int_rowindex,54,curr_other_deductions,styleColumns1)
                sheet.write(int_rowindex,55,curr_deduction,styleColumns1)
                sheet.write(int_rowindex,56,curr_net,styleColumns1)


            int_rowindex +=3
            total_gross_check = round(curr_gross_salary,2)
            tota_net_check = round(curr_net,2)

            #Totals
            sheet.write_merge(int_rowindex,int_rowindex,2,3,"TOTALS")
            sheet.write(int_rowindex,6, round(sum(employee.basic_pay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,9,round(sum(employee.basic_pay_restday_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,12,round(sum(employee.basic_pay_restday_ot_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,14,round(sum(employee.reg_hol_pay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,17,round(sum(employee.reg_hol_work_pay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,20,round(sum(employee.reg_hol_otpay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,23,round(sum(employee.reg_spechol_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,26,round(sum(employee.reg_spechol_otpay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,29,round(sum(employee.undertime_amount + employee.tardiness_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,32,round(sum(employee.reg_otpay_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,35,round(sum(employee.reg_nightdiffy_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,38,round(sum(employee.reg_straightduty_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,40,round(sum(employee.cola_amount for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,42,round(sum(employee.allowance_amount for employee in model_payroll_detail),2),styleColumns1)

            sheet.write(int_rowindex,44,round(sum(employee.basic_pay_leaves_amount for employee in model_payroll_detail),2),styleColumns1)

            sheet.write(int_rowindex,45,round(sum(employee.other_incentive for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,46,round(sum(employee.gross_salary for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,47,round(sum(employee.sss_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,48,round(sum(employee.sss_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,49,round(sum(employee.hdmf_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,50,round(sum(employee.hdmf_salary_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,51,round(sum(employee.hdmf_calamity_loan for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,52,round(sum(employee.hmo_premium for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,53,round(sum(employee.computed_tax for employee in model_payroll_detail),2),styleColumns1)

            sheet.write(int_rowindex,54,round(sum(employee.other_deductions for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,55,round(sum(employee.deductions for employee in model_payroll_detail),2),styleColumns1)
            sheet.write(int_rowindex,56,round(sum(employee.net_pay for employee in model_payroll_detail),2),styleColumns1)



            int_rowindex +=2
            sheet.write(int_rowindex,55,"ATM",styleColumns1)
            sheet.write(int_rowindex,56,round(total_net_debit,2),styleColumns1)

            int_rowindex +=1
            sheet.write(int_rowindex,55,"CHECK",styleColumns1)
            sheet.write(int_rowindex,56,round(tota_net_check,2),styleColumns1)

            int_rowindex +=1
            sheet.write(int_rowindex,55,"TOTAL",styleColumns1)
            sheet.write(int_rowindex,56,round(tota_net_check + total_net_debit,2),styleColumns1)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.payroll_file = byte_arr


class payrollDetailInformation(models.Model):
    _name = 'hr.payroll.detail'
    _description = 'Detailed Payroll Listing per Employee'
    _order = 'employee_id'
    payroll_detail_id = fields.Many2one('hr.payroll.main', ondelete = 'cascade')

    name = fields.Char('Payroll Detail Name')
    employee_id = fields.Many2one('hr.employee', 'Employee Name')
    employee_project_assign = fields.Many2one('res.partner', 'Project Assigned')
    is_reliever = fields.Boolean('Reliever?')
    is_additional_employee = fields.Boolean('Additional Employee?')

    # Gross Pay
    basic_pay_perday = fields.Float('Basic Pay (day)', default=0, digits=(18,2))
    basic_pay_perday_rate = fields.Float('Basic Pay (day)', default=0, digits=(18,2))
    basic_pay_amount = fields.Float('Amount', default=0, digits=(18,2))

    # Incentive Leaves
    basic_pay_leaves_perhour = fields.Float('Incentive Leave (hour)', default=0, digits=(18,2))
    basic_pay_leaves_perday = fields.Integer('Incentive Leave (day)', default=0)
    basic_pay_leaves_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_otpay_perhour = fields.Float('Regular Overtime (hr)', default=0, digits=(18,2))
    reg_otpay_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_nightdiff_perhour = fields.Float('Night Differential (hr)', default=0, digits=(18,2))
    reg_nightdiffy_amount = fields.Float('Amount', default=0, digits=(18,2))

    #Restday
    basic_pay_restday_perhour = fields.Float('Rest Day worked (hr)', default=0, digits=(18,2))
    basic_pay_restday_amount = fields.Float('Amount', default=0, digits=(18,2))

    #Restday OT
    basic_pay_restday_ot_perhour = fields.Float('Restday worked Overtime (hr)', default=0, digits=(18,2))
    basic_pay_restday_ot_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_straightduty_perhour = fields.Float('Straight Duty (hr)', default=0, digits=(18,2))
    reg_straightduty_amount = fields.Float('Amount', default=0, digits=(18,2))

    cola_rate_perday = fields.Float('COLA (day)', default=0, digits=(18,2))
    cola_amount = fields.Float('Amount', default=0, digits=(18,2))

    allowance_rate_perday = fields.Float('Allowance (day)', default=0, digits=(18,2))
    allowance_amount = fields.Float('Amount', default=0, digits=(18,2))



    reg_hol_pay_perday = fields.Float('Legal Holiday (day)', default=0, digits=(18,2))
    reg_hol_pay_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_hol_work_pay_perhour = fields.Float('Legal Holiday worked (hr)', default=0, digits=(18,2))
    reg_hol_work_pay_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_hol_otpay_perhour = fields.Float('Legal Holiday overtime (hr)', default=0, digits=(18,2))
    reg_hol_otpay_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_spechol_perhour = fields.Float('Special Holiday worked (hr)', default=0, digits=(18,2))
    reg_spechol_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_spechol_otpay_perhour = fields.Float('Special Holiday overtime (hr)', default=0, digits=(18,2))
    reg_spechol_otpay_amount = fields.Float('Amount', default=0, digits=(18,2))
    other_incentive = fields.Float('Others', default=0, digits=(18,2))

    # Deduction for Gross Pay
    tardiness = fields.Float('Tardiness (Min)', digits=(18,2))
    tardiness_permin_rate = fields.Float('Rate (min)', default=0, digits=(18,2))
    tardiness_amount = fields.Float('Amount', default=0, digits=(18,2))

    undertime = fields.Float('Undertime (Min)', digits=(18,2))
    tardiness_pay_permin_rate = fields.Float('Rate (min)', default=0, digits=(18,2))
    undertime_amount = fields.Float('Amount', default=0, digits=(18,2))

    gross_salary = fields.Float('Gross Salary', default=0, digits=(18,2))

    # End Gross Pay

    # Deductions
    # SSS Deduction
    sss_premium = fields.Float('SSS Premium', default=0, digits=(18,2))
    sss_loan = fields.Float('SSS Loans', default=0, digits=(18,2))

    # Pagibig Deduction
    hdmf_premium = fields.Float('Pagibig Premium', default=0, digits=(18,2))
    hdmf_salary_loan = fields.Float('Pagibig Salary Loan', default=0, digits=(18,2))
    hdmf_calamity_loan = fields.Float('Pagibig Calamity Loan', default=0, digits=(18,2))

    # Philhealth Deduction
    hmo_premium = fields.Float('Philhealth', default=0, digits=(18,2))
    other_deductions = fields.Float('Others', default=0, digits=(18,2))

    deductions = fields.Float('Total Deduction', default=0, digits=(18,2))
    # End Deductions

    # Net Pay
    net_pay = fields.Float('Net Pay', default=0, digits=(18,2))
    # End Net Pay

    #Tax
    computed_tax = fields.Float('Withholding Tax', default=0)

    #Other Information
    month_half_period = fields.Integer('Month Quarter')
    month_name_period = fields.Selection(constants.MONTH_SELECTION,'Month Name')
    year_payroll_period = fields.Integer('Year')
    payroll_detail_date = fields.Date('Payroll Date')

    #Override Functions
    @api.multi
    def unlink(self):
        for perSelf in self:
            model_attendance = perSelf.payroll_detail_id.payroll_attendance.employee_ids.search([('employee_reliever','=', perSelf.employee_id.id)])
            #If Employee Payroll is Deleted then tagging of Computed payroll must be False
            if len(model_attendance) > 0:
                for employee_attendance in model_attendance:
                    employee_attendance.computed_payroll = False

            model_attendance = perSelf.payroll_detail_id.payroll_attendance.employee_ids.search([('employee_reliever','=', perSelf.employee_id.id)])
            if len(model_attendance) > 0:
                for employee_attendance in model_attendance:
                    employee_attendance.computed_payroll = False

            model_incentive = self.env['payroll.detail.deduction'].search([('payroll_detail_id', '=', perSelf.id)])
            model_incentive.unlink()
            model_incentive = self.env['payroll.detail.incentives'].search([('payroll_detail_id', '=', perSelf.id)])
            model_incentive.unlink()

        super(payrollDetailInformation, self).unlink()
        return True

    #For Report Generation
    @api.one
    def getCompanyName(self):
        #Get Company Information
        company = self.env['res.company'].search([('id', '=', 1)])
        self.company_name = company.name.upper()

        return company.name

    @api.one
    def getCompanyAddress(self):
        #Get Company Information
        company = self.env['res.company'].search([('id', '=', 1)])
        self.company_address = company.street + ' ' + company.street2 + ' ' + company.city + ' City'

    @api.one
    def getCompanyContact(self):
        #Get Company Information
        company = self.env['res.company'].search([('id', '=', 1)])

        self.company_contact = 'Tel Nos.' + str(company.phone) + ' : Telefax No.' + str(company.fax)

    @api.one
    def getIdentification(self):
        self.my_id = self.id

    company_name = fields.Char('Company Name', store=False, compute ='getCompanyName', default = getCompanyName)
    company_address = fields.Char('Company Address', store=False, compute ='getCompanyAddress', default = getCompanyAddress)
    company_contact = fields.Char('Company Contact', store=False, compute ='getCompanyContact', default = getCompanyContact)

    incentive_id = fields.One2many('payroll.detail.incentives', 'payroll_detail_id','incentive breakdown ID')
    deduction_id = fields.One2many('payroll.detail.deduction', 'payroll_detail_id','Deduction breakdown ID')
    my_id = fields.Integer('My ID', compute ='getIdentification')

    def getDeductionBreakdown(self, cr, uid, ids, context=None):
        context = {}

        if context is None:  context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
            context.update(default_attendance_detail_id=ids)
        employee = self.pool.get("hr.payroll.detail").browse(cr,uid,ids,context=None)
        int_state  = 0
        if employee.payroll_detail_id.state == 'draft':
            int_state  = 1

        partial_id = self.pool.get("payroll.incentive.main.wiz").create(
            cr, uid, {'payroll_detail_id': ids[0], 'other_type':2, 'name': employee.employee_id.name,
                      'state':int_state }, context=context)

        return {
            'name': "Deduction Breakdown",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'payroll.incentive.main.wiz',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }

    def getIncentiveBreakdown(self, cr, uid, ids, context=None):
        context = {}
        #default_employee=self.employee_id.id,
        if context is None:  context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model=self._name)
            context.update(default_attendance_detail_id=ids)
        employee = self.pool.get("hr.payroll.detail").browse(cr,uid,ids,context=None)

        int_state  = 0
        if employee.payroll_detail_id.state == 'draft':
            int_state  = 1

        partial_id = self.pool.get("payroll.incentive.main.wiz").create(
            cr, uid, {'payroll_detail_id': ids[0], 'other_type':1, 'name': employee.employee_id.name,
                      'state':int_state}, context=context)

        return {
            'name': "Incentive Breakdown",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'payroll.incentive.main.wiz',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }


class payrollIncentiveMain(models.Model):
    _name = 'payroll.incentive.main'
    _description = 'Payroll Incentive Deduction Main'

    payroll_detail_id = fields.Many2one('hr.payroll.detail', 'Payroll Detail')
    name = fields.Char('Name')
    incentive_ids = fields.One2many('payroll.incen.breakdown', 'main_id', readonly=False, copy=False)

    @api.onchange('payroll_detail_id')
    def getInfos(self):
        incentive_main = self.env['payroll.incentive.main'].search([('payroll_detail_id', '=', self.payroll_detail_id.id)])
        if len(incentive_main) > 0:
            self.name = incentive_main.name
            self.incentive_ids = incentive_main.incentive_ids

    @api.one
    def getTotal(self):
        total_amount = 0
        incentive = self.env['payroll.incen.breakdown'].search([('main_id', '=', self.id)])
        total_amount = sum(incent.amount for incent in incentive)
        return total_amount
    @api.one
    def updateReliever(self):
        for incentive in self.incentive_ids:
            model_incentive = self.env['payroll.incen.breakdown']
            model_incentive.write({
                'main_id' : incentive.main_id,
                'name': incentive.name,
                'amount': incentive.amount
            })
        #raise Warning(self.payroll_detail_id)


class payrollIncentiveBreakdown(models.Model):
    _name = 'payroll.incen.breakdown'
    _description = 'Payroll Incentive breakdown'

    main_id = fields.Many2one('payroll.inctv.dedct.main', 'Incentive Main ID')
    name = fields.Many2one('hr.incentives', 'Incentive Name')
    amount = fields.Float('Amount', digits=(18,2), default =0)


class payrollIncentiveBreakdown(models.Model):
    _name = 'payroll.detail.incentives'
    _description = 'Payroll Detail Incentive Breakdown'

    payroll_detail_id = fields.Many2one('hr.payroll.detail', 'Payroll Detail')
    name = fields.Many2one('hr.incentives', 'Incentive Name')
    amount = fields.Float('Amount', digits=(18,2), default =0)

    @api.model
    def getTotal(self, pint_payroll_detail = 0):
        model_IncentiveBreakdown = self.env[self._name].search([('payroll_detail_id', '=', pint_payroll_detail)])
        curr_total = sum(round(curr.amount,2) for curr in model_IncentiveBreakdown)
        return curr_total


class payrollDeductionBreakdown(models.Model):
    _name = 'payroll.detail.deduction'
    _description = 'Payroll Detail Deduction Breakdown'

    payroll_detail_id = fields.Many2one('hr.payroll.detail', 'Payroll Detail')
    name = fields.Many2one('hr.deductions', 'Deduction')
    amount = fields.Float('Amount', digits=(18,2), default =0)

    @api.model
    def getTotal(self, pint_payroll_detail = 0):
        model_IncentiveBreakdown = self.env[self._name].search([('payroll_detail_id', '=', pint_payroll_detail)])
        curr_total = sum(round(curr.amount,2) for curr in model_IncentiveBreakdown)
        return curr_total

    #@api.one
    #def saveIncentive(self):


    #---------------- Functions/Methods
    # Overrides
    #@api.multi
    #def write(self, vals):
#        super(payrollIncentiveBreakdown, self).write(vals)
#        return True
    # End Override Functions

#    @api.model
#    def create(self, vals):
        #Update first the Sequence
        #sequences = self.env['ir.sequence']
        #employeeSequences = sequences.search([('code','=','hr.employee.sequence')])

        #new_record = super(hrExtendedEmployee, self).create(vals)
        #return new_record
 #       return []


class paymentType(models.Model):
    _name = 'hr.payroll.paymenttype'

    # Payment Type
    # Type of Payment for the Employee during Salary Release
    # CHK CHECK
    # DEB DEBIT CARD
    # CSH CASH
    code = fields.Char('Code')
    name = fields.Char('Name')
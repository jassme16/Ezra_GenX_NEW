from openerp import models, fields,api
#from openerp.osv import fields, osv

from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from openerp.addons.hr_payroll_ezra.parameters import constants as genx

MONTH_QUARTER_SELECTION = [
    (1, '1st Half'),
    (2, '2nd Half')
]


class payroll_temp_detail(models.Model):
    _name = 'hr.payroll.detail.temp'
    _description = 'Temp Payroll detail'
    _order = 'employee_id,payroll_detail_date'

    #payroll_main_temp_id = fields.Many2one('hr.payroll.main.temp', ondelete = 'cascade')
    payroll_detail_id = fields.Many2one('hr.payroll.main', ondelete = 'cascade')

    name = fields.Char('Payroll Detail Name')
    employee_id = fields.Many2one('hr.employee', 'Employee Name')
    employee_project_assign = fields.Many2one('res.partner', 'Project Assigned')
    is_reliever = fields.Boolean('Reliever?')

    # Gross Pay
    basic_pay_perday = fields.Float('Basic Pay (day)', default=0, digits=(18,2))
    basic_pay_perday_rate = fields.Float('Basic Pay (day)', default=0, digits=(18,2))
    basic_pay_amount = fields.Float('Amount', default=0, digits=(18,2))

    # Incentive Leaves
    basic_pay_leaves_perhour = fields.Float('Incentive Leave (hour)', default=0, digits=(18,2))
    basic_pay_leaves_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_otpay_perhour = fields.Float('Regular Overtime (hr)', default=0, digits=(18,2))
    reg_otpay_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_nightdiff_perhour = fields.Float('Night Differential (hr)', default=0, digits=(18,2))
    reg_nightdiffy_amount = fields.Float('Amount', default=0, digits=(18,2))

    # Restday
    basic_pay_restday_perhour = fields.Float('Rest Day worked (hr)', default=0, digits=(18,2))
    basic_pay_restday_amount = fields.Float('Amount', default=0, digits=(18,2))

    #Restday OT
    basic_pay_restday_ot_perhour = fields.Float('Restday worked Overtime (hr)', default=0, digits=(18,2))
    basic_pay_restday_ot_amount = fields.Float('Amount', default=0, digits=(18,2))

    reg_straightduty_perhour = fields.Float('Straight Duty (hr)', default=0, digits=(18,2))
    reg_straightduty_amount = fields.Float('Amount', default=0, digits=(18,2))

    cola_rate_perday = fields.Float('COLA (day)', default=0, digits=(18,2))
    cola_amount = fields.Float('Amount', default=0, digits=(18,2))

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
    month_name_period = fields.Selection(genx.MONTH_SELECTION,'Month Name')
    year_payroll_period = fields.Integer('Year')
    payroll_detail_date = fields.Date('Payroll Date')

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


class payslip_per_Employee(models.TransientModel):
    _name = 'payroll.payslip.employee'

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    month_of_from = fields.Selection(genx.MONTH_SELECTION, 'From the Month of', required=True, default = 1)
    month_quarter_from = fields.Selection(MONTH_QUARTER_SELECTION, 'Month Quarter', required=True, default = 1)
    month_year_from = fields.Integer('Year', required=True, default = genx.YEAR_NOW)


    month_of_to = fields.Selection(genx.MONTH_SELECTION, 'To the Month of', required=True, default = 12)
    month_quarter_to = fields.Selection(MONTH_QUARTER_SELECTION, 'Month Quarter', required=True, default = 2)
    month_year_to = fields.Integer('Year', required=True, default = genx.YEAR_NOW)



    def print_report(self, cr, uid, ids, context=None):

        model_payroll_detail_temp_create = self.pool.get("hr.payroll.detail.temp")

        model_payroll_detail_temp= self.pool.get("hr.payroll.detail.temp").browse(cr,uid,ids,context=None)

        model_payroll_detail_temp_create.search(cr,uid,[('create_uid', '=',uid)],context=context)


        unlink_ids= []

        #unlink_ids = [pay_detail.id for pay_detail in model_payroll_detail_temp_create.browse(cr,uid,ids,context=None)]
        for pay_detail in model_payroll_detail_temp_create.browse(cr,uid,ids,context=None):
            #print(pay_detail.create_uid)
            #raise Warning(pay_detail.id)
            unlink_ids.append(pay_detail.id)

        #raise Warning(unlink_ids)

        model_payroll_detail_temp_create.unlink(cr, uid, unlink_ids, context=context)


        model_payroll_detail= self.pool.get("hr.payroll.detail")
        pay_ids = model_payroll_detail.search(cr,uid,[('create_uid', '=',uid)],context=context)


        for payroll_detail in model_payroll_detail.browse(cr,uid,pay_ids,context=None):
            dict_save = {
                'payroll_detail_id':payroll_detail.payroll_detail_id.id,
                'name':payroll_detail.name,
                'employee_id':payroll_detail.employee_id.id,
                'employee_project_assign':payroll_detail.employee_project_assign.id,
                'is_reliever':payroll_detail.is_reliever,
                'basic_pay_perday':payroll_detail.basic_pay_perday,
                'basic_pay_perday_rate':payroll_detail.basic_pay_perday_rate,
                'basic_pay_amount':payroll_detail.basic_pay_amount,
                'basic_pay_leaves_perhour':payroll_detail.basic_pay_leaves_perhour,
                'basic_pay_leaves_amount':payroll_detail.basic_pay_leaves_amount,
                'reg_otpay_perhour':payroll_detail.reg_otpay_perhour,
                'reg_otpay_amount':payroll_detail.reg_otpay_amount,
                'reg_nightdiff_perhour':payroll_detail.reg_nightdiff_perhour,
                'reg_nightdiffy_amount':payroll_detail.reg_nightdiffy_amount,
                'basic_pay_restday_perhour':payroll_detail.basic_pay_restday_perhour,
                'basic_pay_restday_amount':payroll_detail.basic_pay_restday_amount,
                'basic_pay_restday_ot_perhour':payroll_detail.basic_pay_restday_ot_perhour,
                'basic_pay_restday_ot_amount':payroll_detail.basic_pay_restday_ot_amount,
                'reg_straightduty_perhour':payroll_detail.reg_straightduty_perhour,
                'reg_straightduty_amount':payroll_detail.reg_straightduty_amount,
                'cola_rate_perday':payroll_detail.cola_rate_perday,
                'cola_amount':payroll_detail.cola_amount,
                'reg_hol_pay_perday':payroll_detail.reg_hol_pay_perday,
                'reg_hol_pay_amount':payroll_detail.reg_hol_pay_amount,
                'reg_hol_work_pay_perhour':payroll_detail.reg_hol_work_pay_perhour,
                'reg_hol_work_pay_amount':payroll_detail.reg_hol_work_pay_amount,
                'reg_hol_otpay_perhour':payroll_detail.reg_hol_otpay_perhour,
                'reg_hol_otpay_amount':payroll_detail.reg_hol_otpay_amount,
                'reg_spechol_perhour':payroll_detail.reg_spechol_perhour,
                'reg_spechol_amount':payroll_detail.reg_spechol_amount,
                'reg_spechol_otpay_perhour':payroll_detail.reg_spechol_otpay_perhour,
                'reg_spechol_otpay_amount':payroll_detail.reg_spechol_otpay_amount,
                'other_incentive':payroll_detail.other_incentive,
                'tardiness':payroll_detail.tardiness,
                'tardiness_permin_rate':payroll_detail.tardiness_permin_rate,
                'tardiness_amount':payroll_detail.tardiness_amount,
                'undertime':payroll_detail.undertime,
                'tardiness_pay_permin_rate':payroll_detail.tardiness_pay_permin_rate,
                'undertime_amount':payroll_detail.undertime_amount,
                'gross_salary':payroll_detail.gross_salary,
                'sss_premium':payroll_detail.sss_premium,
                'sss_loan':payroll_detail.sss_loan,
                'hdmf_premium':payroll_detail.hdmf_premium,
                'hdmf_salary_loan':payroll_detail.hdmf_salary_loan,
                'hdmf_calamity_loan':payroll_detail.hdmf_calamity_loan,
                'hmo_premium':payroll_detail.hmo_premium,
                'other_deductions':payroll_detail.other_deductions,
                'deductions':payroll_detail.deductions,
                'net_pay':payroll_detail.net_pay,
                'computed_tax':payroll_detail.computed_tax,
                'month_half_period':payroll_detail.month_half_period,
                'month_name_period':payroll_detail.month_name_period,
                'year_payroll_period':payroll_detail.year_payroll_period,
                'payroll_detail_date':payroll_detail.payroll_detail_date,
                'incentive_id':payroll_detail.incentive_id,
                'deduction_id':payroll_detail.deduction_id,}

            model_payroll_detail_temp_create.create(cr, uid, dict_save)

        if context is None:
            context = {}

        data = self.read(cr, uid, ids, ['employee_id'], context=context)[0]
        #data= self.pool.get("hr.payroll.detail").browse(cr,uid,ids,context=None)
        #raise Warning(ids)
        #x_data = {'employee_id': self.employee_id}

        #raise Warning(data)
        obj = self.pool.get('hr.payroll.detail.temp')
        ids = obj.search(cr, uid, [('employee_id','=',9729)])

        #raise Warning(ids)
        #x_data = {'employee_id':9729}
        datas = {
             'ids': ids,
             'model': 'hr.payroll.detail.temp',
             'form': data
            }
        #return self.pool['report'].get_action(
                    #cr, uid, [], 'hr_payroll_ezra.report_payslip_employee', data=datas, context=context )

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hr_payroll_ezra.report_payslip_employee',
            'datas': datas,
            }
        #pass



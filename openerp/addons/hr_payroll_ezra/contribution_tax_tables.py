# -*- coding: utf-8 -*-
import datetime
from openerp import models, fields,api
import calendar
from parameters import constants as genx
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
INCENTIVE_DEDUCTION_TYPE = [
    ('rate_hr','Rate per Hour'),
    ('fixed_amount_hr','Fixed Amount per Hour'),
    ('rate_day','Rate per Day'),
    ('fixed_amount_day','Fixed Amount per Day'),
    ('fixed_amount','Fixed Amount')
]

TAX_LINE_NUMBER = [
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4'),
    ('5', '5'),
    ('6', '6'),
    ('7', '7'),
    ('8', '8')
]

TAX_EXEMPTIOM_STATUS = [
    ('zero', 'Zero'),
    ('withdependents', 'With Dependents'),
    ('withnodependents', 'With No Dependents')
]

PAYMENT_SCHEDULE =[
    ('daily', 'DAILY'),
    ('weekly', 'WEEKLY'),
    ('semimonthly', 'SEMI-MONTHLY'),
    ('monthly', 'MONTHLY')
]


DEPENDENTS =[
    ('0', '0'),
    ('1', '1'),
    ('2', '2'),
    ('3', '3'),
    ('4', '4')
]


ONE_HUNDRED_PERCENT = 100
MONTHS_IN_YEAR = 12
WORK_HOURS = 8
class TaxTable(models.Model):
    _name = 'hr.payroll.taxtable'

    name = fields.Char('Name')
    code = fields.Char('Code')
    line_number = fields.Selection(TAX_LINE_NUMBER,'Line Number', required = True)
    exemption_status = fields.Selection(TAX_EXEMPTIOM_STATUS,'Exemption Status', required = True)
    payment_schedule = fields.Selection(PAYMENT_SCHEDULE,'Schedule', required = True)
    dependents = fields.Selection(DEPENDENTS,'No. of Dependents', required = True)
    exemption_amount = fields.Float('Exemption Amount', required= True)
    salary_range_from = fields.Float('Salary Range From', required= True)
    salary_range_to = fields.Float('Salary Range To', required= True)
    tax = fields.Float('Tax', required= True)
    rate_in_excess = fields.Float('Rate in Excess(%)', required= True)

    @api.model
    def getTaxRates(self, amount = 0.00, employee_status ='', dependents = 0, payment_schedule = ''):

        CONDITION = " %(amount).2f BETWEEN SALARY_RANGE_FROM AND SALARY_RANGE_TO" % {'amount':amount}
        CONDITION = CONDITION  + " AND exemption_status = '%(status)s' AND (DEPENDENTS::INTEGER) = %(dependents)d " \
                                 " AND PAYMENT_SCHEDULE = '%(schedule)s' " %{'status':employee_status, 'dependents':dependents, 'schedule': payment_schedule}


        TAX_QUERY = genx.CreateSQLQuery(self._table, ['tax', 'rate_in_excess', 'salary_range_from'],CONDITION).returnQuery()

        flt_tax = 0.00
        flt_rate_in_excess = 0.00
        flt_salary_range_from = 0.00

        self.env.cr.execute(TAX_QUERY)
        for fetch in self.env.cr.fetchall():
            flt_tax = fetch[0]
            flt_rate_in_excess = fetch[1] /100
            flt_salary_range_from = fetch[2]
        return {'TAX': flt_tax, 'RATE_EXCESS': flt_rate_in_excess, 'EXEMPTION_AMOUNT': flt_salary_range_from}

    @api.model
    def getTaxInformation(self, employee_status = '', dependents = 0, payment_schedule=''):
        tax_infos = self.env['hr.payroll.taxtable'].search([])
        for tax_info in tax_infos:
            if tax_info.exemption_status == employee_status \
                and int(tax_info.dependents) == dependents \
                and tax_info.payment_schedule == payment_schedule:
                return {'CODE': tax_info.code, 'EXEMPTION_AMOUNT': tax_info.exemption_amount}
        return {'CODE': '', 'EXEMPTION_AMOUNT': 0.00}

class sssContributionTable(models.Model):

    _name = 'hr.payroll.ssscontrib'

    def computeSssTotal(self):
        self.total_contribution = self.employers_contribution + self.employee_compensation + self.employee_compensation

    bracket = fields.Integer('Bracket No.')
    name = fields.Char('SSS Contribution name')
    range_from = fields.Float('Range from',digits=(18,2))
    range_to = fields.Float('Range to' ,digits=(18,2))
    employers_contribution = fields.Float('ER',digits=(18,2))
    employee_contribution = fields.Float('EE',digits=(18,2))
    employee_compensation = fields.Float('EC',digits=(18,2))
    total_contribution = fields.Float('Total', compute = computeSssTotal, store = True,digits=(18,2))


    @api.model
    def getEmployeeContribution(self, amount = 0):


        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        SSS_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution', 'employee_compensation'],CONDITION).returnQuery()

        employee_contribution = 0.00
        employee_compensation = 0.00
        self.env.cr.execute(SSS_QUERY)

        for fetch in self.env.cr.fetchall():

            employee_contribution = fetch[0]
            employee_compensation = fetch[1]
        return employee_contribution + employee_compensation

    @api.model
    def getEmployeeTotalContribution(self, amount = 0):

        CONDITION = " %(amount).2f >= RANGE_FROM and %(amount).2f <= RANGE_TO" % {'amount':amount}
        SSS_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution', 'employee_compensation', 'employers_contribution'],CONDITION).returnQuery()

        employee_contribution = 0.00
        employee_compensation = 0.00
        employer_contribution = 0.00
        self.env.cr.execute(SSS_QUERY)
        for fetch in self.env.cr.fetchall():
            employee_contribution = fetch[0]
            employee_compensation = fetch[1]
            employer_contribution = fetch[2]
        return employee_contribution + employee_compensation + employer_contribution

    @api.model
    def getEmployerContribution(self, amount = 0):
        CONDITION = " %(amount).2f >= RANGE_FROM and %(amount).2f <= RANGE_TO" % {'amount':amount}
        SSS_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution', 'employee_compensation', 'employers_contribution'],CONDITION).returnQuery()

        employer_contribution = 0.00
        self.env.cr.execute(SSS_QUERY)
        for fetch in self.env.cr.fetchall():
            employer_contribution = fetch[2]
        return employer_contribution

    @api.model
    def getEmployeeCompensation(self,amount = 0):
        CONDITION = " %(amount).2f >= RANGE_FROM and %(amount).2f <= RANGE_TO" % {'amount':amount}
        SSS_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution', 'employee_compensation', 'employers_contribution'],CONDITION).returnQuery()

        employee_compensation = 0.00
        self.env.cr.execute(SSS_QUERY)
        for fetch in self.env.cr.fetchall():
            employee_compensation = fetch[1]
        return employee_compensation

class ContributionDeductions(models.Model):

    _name = 'payroll.sss.deductions'

    code = fields.Char('Code', required =True)
    name = fields.Char('Name')

    main_customer_id = fields.Many2one('res.customers.main','Customer' , required =True)
    region_id = fields.Many2one('hr.regions', 'Region Assigned', required=True)
    branches_id = fields.Many2one('res.customer.branches', 'Branch')
    number_of_days = fields.Selection(genx.WORKING_DAYS, 'Working Days', default=5)
    position_id = fields.Many2one('hr.job','Position')

    sss_ee = fields.Float('SSS Employee Contribution', required=True, default=0, digits=(18, 2))
    sss_er = fields.Float('SSS Employer Contribution', required=True, default=0, digits=(18, 2))
    sss_ec = fields.Float('SSS Employee Compensation', required=True, default=0, digits=(18, 2))
    phic_ee = fields.Float('PHIC Employee Contribution', required=True, default=0, digits=(18, 2))
    phic_er = fields.Float('PHIC Employer Contribution', required=True, default=0, digits=(18, 2))
    phic_employee_monthly_salary = fields.Float('Monthly Salary', required=True, default=0, digits=(18, 2))
    pagibig_ee = fields.Float('Pag-ibig Employee Contribution', required=True, default=0, digits=(18, 2))
    pagibig_er = fields.Float('Pag-ibig Employer Contribution', required=True, default=0, digits=(18, 2))

    #@api.one
    def getDeductionInformation(self, employee_id):
        employee = self.env['hr.employee'].search([('id','=', employee_id)])
        if len(employee) > 0:
            region_id = employee.assignto_region.id
            branch_id = employee.assignto_branch_2.id
            working_days = employee.assignto_workingdays
            customer = employee.assignto.id
            job_id = employee.job_id.id

            deduction = self.env['payroll.sss.deductions'].search([('main_customer_id','=',customer),
                                                                   ('region_id','=',region_id),
                                                                   ('branches_id','=',branch_id),
                                                                   ('number_of_days','=',working_days),
                                                                   ('position_id','=',job_id)])
            if len(deduction) == 0:
                deduction = self.env['payroll.sss.deductions'].search([('main_customer_id','=',customer),
                                                                       ('region_id','=',region_id),
                                                                       ('number_of_days','=',working_days),
                                                                       ('position_id','=',job_id),
                                                                       ('branches_id','=',False)])


            if len(deduction) > 0:
                return deduction
                #return {'EE': deduction.sss_ee, 'ER': deduction.sss_er}
        return []

    @api.model
    def getEmployeeCompensation(self, employee_id):
        employee = self.env['hr.employee'].search([('id','=', employee_id)])
        if len(employee) > 0:
            region_id = employee.assignto_region.id
            branch_id = employee.assignto_branch_2.id
            working_days = employee.assignto_workingdays
            customer = employee.assignto.id
            job_id = employee.job_id.id

            deduction = self.env['payroll.sss.deductions'].search([('main_customer_id','=',customer),
                                                                   ('region_id','=',region_id),
                                                                   ('branches_id','=',branch_id),
                                                                   ('number_of_days','=',working_days),
                                                                   ('position_id','=',job_id)])
            if len(deduction) == 0:
                deduction = self.env['payroll.sss.deductions'].search([('main_customer_id','=',customer),
                                                                       ('region_id','=',region_id),
                                                                       ('number_of_days','=',working_days),
                                                                       ('position_id','=',job_id),
                                                                       ('branches_id','=',False)])
            if len(deduction) > 0:
                return deduction.sss_ec

    #@api.one
    def getSSSDeductions(self,employee_id):
        deduction = self.getDeductionInformation(employee_id)
        if len(deduction) > 0:
            #print('1111')
            return {'EE': deduction.sss_ee, 'ER': deduction.sss_er}
        return {'EE': 0, 'ER': 0}

    #@api.one
    def getPHICDeductions(self,employee_id):
        deduction = self.getDeductionInformation(employee_id)
        if len(deduction) > 0:
            return {'EE': deduction.phic_ee, 'ER': deduction.phic_er, 'MONTHLY_SALARY': deduction.phic_employee_monthly_salary}
        return {'EE': 0, 'ER': 0, 'MONTHLY_SALARY': 0}

    #@api.one
    def getPagibig(self,employee_id):
        deduction = self.getDeductionInformation(employee_id)
        if len(deduction) > 0:
            return {'EE': deduction.pagibig_ee, 'ER': deduction.pagibig_er, 'MONTHLY_SALARY': deduction.phic_employee_monthly_salary}
        return {'EE': 0, 'ER': 0, 'MONTHLY_SALARY': 0}



class philHealthTable(models.Model):
    _name = 'hr.payroll.hmo'

    @api.one
    def computeHmoTotal(self):
        self.total_contribution = self.employers_contribution + self.employee_compensation

    bracket = fields.Integer('Bracket No.')
    name = fields.Char('PHIC name')
    range_from = fields.Float('Range from',digits=(18,2))
    range_to = fields.Float('Range to',digits=(18,2))
    employers_contribution = fields.Float('Employer Share',digits=(18,2))
    employee_contribution = fields.Float('Employee Share',digits=(18,2))
    total_contribution = fields.Float('Total', compute = computeHmoTotal, store = True,digits=(18,2))

    @api.model
    def getEmployeeContribution(self, amount = 0):

        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        PHIL_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution'],CONDITION).returnQuery()

        contribution = 0.00
        self.env.cr.execute(PHIL_QUERY)
        for fetch in self.env.cr.fetchall():
            contribution = fetch[0]
        return contribution

    @api.model
    def getEmployerContribution(self, amount = 0):

        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        PHIL_QUERY = genx.CreateSQLQuery(self._table, ['employers_contribution'],CONDITION).returnQuery()

        contribution = 0.00
        self.env.cr.execute(PHIL_QUERY)
        for fetch in self.env.cr.fetchall():
            contribution = fetch[0]
        return contribution

    @api.model
    def getEmployeeMonthlySalaryBracket(self, amount = 0):
        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        PHIL_QUERY = genx.CreateSQLQuery(self._table, ['bracket'],CONDITION).returnQuery()

        contribution = 0.00
        self.env.cr.execute(PHIL_QUERY)
        for fetch in self.env.cr.fetchall():
            contribution = fetch[0]
        return contribution


class hdmfTable(models.Model):
    _name = 'hr.payroll.hdmf'
    bracket = fields.Integer('Bracket No.')
    name = fields.Char('Pagibig Contribution name')
    monthly_compensation = fields.Float('Monthly Compensation',digits=(18,2))
    range_from = fields.Float('Range from',digits=(18,2))
    range_to = fields.Float('Range to',digits=(18,2))
    employers_contribution = fields.Float('Employer (%)',digits=(18,2))
    employee_contribution = fields.Float('Employee (%)',digits=(18,2))

    @api.model
    def getEmployeeContribution(self, amount = 0):

        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        HDMF_QUERY = genx.CreateSQLQuery(self._table, ['employee_contribution,monthly_compensation'],CONDITION).returnQuery()

        contribution = 0.00
        monthly_comp = 0.00
        self.env.cr.execute(HDMF_QUERY)
        for fetch in self.env.cr.fetchall():
            contribution = fetch[0]
            monthly_comp = fetch[1]
        return monthly_comp * (contribution/ ONE_HUNDRED_PERCENT)

    @api.model
    def getEmployerContribution(self, amount = 0):

        CONDITION = " %(amount).2f BETWEEN RANGE_FROM AND RANGE_TO" % {'amount':amount}
        HDMF_QUERY = genx.CreateSQLQuery(self._table, ['employers_contribution,monthly_compensation'],CONDITION).returnQuery()

        contribution = 0.00
        monthly_comp = 0.00
        self.env.cr.execute(HDMF_QUERY)
        for fetch in self.env.cr.fetchall():
            contribution = fetch[0]
            monthly_comp = fetch[1]

        return monthly_comp * (contribution/ ONE_HUNDRED_PERCENT)


class LeaveTypes(models.Model):
    _name = 'hr.leavetypes'
    code = fields.Char('Code')
    name = fields.Char('Name')
    rate = fields.Float('Hourly Rate(%)',digits=(18,2))

    @api.model
    def getLeaveType(self, code =''):
        obj_name = self.search([('code', '=', code)])
        return obj_name.name


class WorkDaysType(models.Model):
    _name = 'hr.workdaystype'
    code = fields.Char('Code')
    name = fields.Char('Name')

    @api.model
    def getWorkDaysType(self, code =''):
        obj_name = self.search([('code', '=', code)])
        return obj_name.name


class WorkHourType(models.Model):
    _name = 'hr.workhourtype'
    code = fields.Char('Code')
    work_daytype_id = fields.Many2one('hr.workdaystype', 'Type')
    name = fields.Char('Name')
    rate = fields.Float('Hourly Rate(%)', default =0)
    rate_in_decimal = fields.Float('Rate in decimal', default =0)
    is_taxable = fields.Boolean('Taxable?', default = True)

    @api.one
    @api.onchange('rate')
    def convertRatetoDecimal(self):
        self.rate_in_decimal = self.rate / ONE_HUNDRED_PERCENT

    @api.model
    def getWorkHourRateinDecimal(self, work_hour_code =''):
        work_hour_type = self.search([('code', '=', work_hour_code)])
        return work_hour_type.rate_in_decimal

    @api.model
    def getAmountRateAmount(self,work_hour_code= '', amount = 0):
        work_hour_type = self.search([('code', '=', work_hour_code)])
        rate_amount = amount * work_hour_type.rate_in_decimal
        return rate_amount


class Incentives(models.Model):
    _name = 'hr.incentives'
    code = fields.Char('Code', required = True)
    name = fields.Char('Name', required = True)
    type = fields.Selection(INCENTIVE_DEDUCTION_TYPE, 'Incentive Type', required = True, default = "fixed_amount")
    amount = fields.Float('Amount', default=0)
    rate= fields.Float('Rate(%)', default=0)
    is_taxable = fields.Boolean('Taxable?', default = True)


class Deductions(models.Model):
    _name = 'hr.deductions'
    code = fields.Char('Code', required= True)
    name = fields.Char('Name', required= True)
    type = fields.Selection(INCENTIVE_DEDUCTION_TYPE, 'Deduction Type', required = True, default ='fixed_amount')
    amount = fields.Float('Amount', default =0)
    rate= fields.Float('Rate(%)', default =0)


class Region(models.Model):
    _name = 'hr.regions'
    _description = 'Philippine Region Groups'

    code = fields.Char('Code', required=True)
    name = fields.Char('Region', required=True)
    island_group = fields.Selection(genx.ISLAND_GROUP, required=True, default =1)
    regional_centers = fields.Char('Regional Centers', required=True)
    cola_amount = fields.Float('COLA', digits=(18,2),default=0)

    @api.model
    def get_COLA_amount(self, region_id):
        if region_id !=False:
            model_region = self.env['hr.regions'].search([('id','=', region_id)])
            if len(model_region) > 0:
                return model_region.cola_amount
            else:
                return 0
        else:
            return 0

class Holidays(models.Model):
    _name = 'hr.holiday'
    _description = 'Holiday Table'
    _order = 'holiday_month, holiday_day'
    name = fields.Char('Name', required=True)
    holiday_month = fields.Selection(genx.MONTH_SELECTION,'Month', required=True)
    holiday_day = fields.Integer('Day', required=True, default = 1)

    holiday_date = fields.Date('Date', compute = "getDate")
    holiday_year = fields.Integer('Year')
    is_only_for_this_year = fields.Boolean('For this Year', default = False)

    @api.one
    def getDate(self):

        if self.is_only_for_this_year == True:
            if self.is_only_for_this_year == 0:
                raise Warning('Year must must not equal to zero.')
            else:
               str_date = str(self.holiday_year) + '-'
        else:
            str_date = str(genx.YEAR_NOW) + '-'

        if self.is_only_for_this_year == 0:
            str_date = str(genx.YEAR_NOW) + '-'
        if self.holiday_year ==0:
            str_date = str(genx.YEAR_NOW) + '-'

        str_date += str(self.holiday_month) + '-' + str(self.holiday_day)

        new_date = datetime.datetime.strptime(str_date, '%Y-%m-%d')
        self.holiday_date = new_date
        return  new_date



    @api.model
    def create(self, vals):
        if not 'holiday_date' in vals.keys():
            if self.is_only_for_this_year == True:
                if self.is_only_for_this_year == 0:
                    raise Warning('Year must must not equal to zero.')
                else:

                   str_date = str(vals['holiday_year']) + '-'
            else:
                str_date = str(genx.YEAR_NOW) + '-'

            str_date += str(vals['holiday_month']) + '-' + str(vals['holiday_day'])
            #raise Warning(str_date)
            new_date = datetime.datetime.strptime(str_date, '%Y-%m-%d')
            vals['holiday_date'] = new_date
            create_date = vals['holiday_date']
            #raise Warning(new_date)
        else:
            create_date = datetime.datetime.strptime(vals['holiday_date'], '%Y-%m-%d')
        #raise Warning(create_date)
        model_holiday = self.env['hr.holiday'].search([])
        #Use Loop due to Error in Search ORM for 11 Jan 2016
        for holiday in model_holiday:
            if holiday.holiday_date == create_date:
                raise ValidationError('Date has already define as Holiday.')
        #if len(model_holiday) > 0:
        #    raise ValidationError('Date has already define as Holiday.')


        new_record = super(Holidays, self).create(vals)

        #employeeSequences.write({'number_next': int(self.employee_number)})
        return new_record


    @api.constrains('holiday_day')
    def checkHolidayDate(self):


        if self.is_only_for_this_year == True:
            if self.is_only_for_this_year == 0:
                raise Warning('Year must must not equal to zero.')
            else:
               is_leapYear = calendar.isleap(self.holiday_year)
        else:
            is_leapYear = calendar.isleap(genx.YEAR_NOW)

        if self.holiday_month == 2:
            int_feb_day = 28
            if is_leapYear == True:
               int_feb_day +=1
            if self.holiday_day <= 0:
                raise ValidationError('Days must not be equal to zero.')
            if self.holiday_day > int_feb_day:
                raise ValidationError('Days exceeded.')
        elif self.holiday_month in(1,3,5,7,8,10,12):
            if self.holiday_day <= 0:
                raise ValidationError('Days must not be equal to zero.')
            if self.holiday_day > 31:
                raise ValidationError('Days exceeded.')
        elif self.holiday_month in(4,6,9,11):
            if self.holiday_day <= 0:
                raise ValidationError('Days must not be equal to zero.')
            if self.holiday_day > 30:
                raise ValidationError('Days exceeded.')


    @api.model
    def checkHolidays_in_DateRange(self, pDateFrom, pDateTo):
        #model_holiday = self.env['hr.holiday'].search([('holiday_date', '>=', pDateFrom),
        #                                                ('holiday_date', '<=', pDateTo)])
        model_holiday = self.env['hr.holiday'].search([])
        holiday_count = 0
        #raise Warning(model_holiday)
        for holiday in model_holiday:
            if holiday.is_only_for_this_year == True:
                if (holiday.holiday_year == genx.YEAR_NOW):
                    dt_holiday = datetime.date(genx.YEAR_NOW, holiday.holiday_month,holiday.holiday_day )
                    dt_from = datetime.date(int(pDateFrom[0:4]), int(pDateFrom[5:7]),int(pDateFrom[8:10]))
                    dt_to = datetime.date(int(pDateTo[0:4]), int(pDateTo[5:7]),int(pDateTo[8:10]))
                    if dt_from <= dt_holiday  <= dt_to :
                        holiday_count += 1
            else:
                dt_holiday = datetime.date(int(pDateTo[0:4]), holiday.holiday_month,holiday.holiday_day )
                dt_from = datetime.date(int(pDateFrom[0:4]), int(pDateFrom[5:7]),int(pDateFrom[8:10]))
                dt_to = datetime.date(int(pDateTo[0:4]), int(pDateTo[5:7]),int(pDateTo[8:10]))
                if dt_from <= dt_holiday  <= dt_to :
                    holiday_count += 1

        return holiday_count


class SalaryPerProvince(models.Model):
    _name = 'hr.regions.salary'
    _description = 'Salary based on Region and Province'

    name = fields.Char('Name', required=True)
    regions = fields.Many2one('hr.regions', 'Regions', required=True)
    province = fields.Char('City/Province', required=True)
    daily_rate_amount = fields.Float('Daily Rate', required=True, default=0)
    cola_amount = fields.Float('COLA', required=True, default=0)

    @api.onchange('regions', 'province', 'cola_amount')
    def rename(self):
        str_region = ''
        str_province = ''
        str_description = ''
        if isinstance(self.regions, bool):
            str_region = ''
        elif len(self.regions) == 0:
            str_region = ''
        else:
            str_region = self.regions.name

        if isinstance(self.province, bool):
            str_province = ''
        elif len(self.province) == 0:
            str_province = ''
        else:
            str_province = self.province

        if isinstance(self.cola_amount, bool):
            str_description =' No COLA'
        elif self.cola_amount == 0:
            str_description =' No COLA'
        else:
            str_description =' with COLA'

        self.name = str_region + '/' + str_province + str_description


    @api.multi
    def write(self, vals):

        #Check if Records has been selected in the Employee Contract and then Update the Amount
        super(SalaryPerProvince, self).write(vals)
        model_hr_contract = self.env['hr.contract'].search([('regions', '=', self.id)])
        if len(model_hr_contract) > 0:
            for employee_contract in model_hr_contract:
                employee_contract.write({
                    'daily_rate': self.daily_rate_amount,
                    'cola_amount': self.cola_amount,
                    'wage': (self.daily_rate_amount * (employee_contract.weeks_in_years * employee_contract.workdays_in_weeks)) / MONTHS_IN_YEAR,
                    'hourly_rate': self.daily_rate_amount / WORK_HOURS
                })
        return True

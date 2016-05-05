from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp import models, fields, api
import datetime
from cStringIO import StringIO
import xlwt
import base64


class BonusPayMain(models.Model):
    _name = 'payroll.incentive.13thmonth'
    _description = '13 Month Pay'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = self.name + '.xls'

    name = fields.Char('Name', required=True)

    month_range_from = fields.Selection(constants.MONTH_SELECTION, 'Month Range from', required=True)
    year_from = fields.Integer('Year from', default = constants.YEAR_NOW, required=True)

    month_range_to = fields.Selection(constants.MONTH_SELECTION, 'Month Range to', required=True)
    year_to = fields.Integer('Year to', default = constants.YEAR_NOW, required=True)
    release_date = fields.Date('Release Date', required= True, default = constants.DATE_NOW)


    total_amount = fields.Float('Total Amount')

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    payroll_file = fields.Binary('Excel File')

    state = fields.Selection(constants.STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')
    incentive_detail_id = fields.One2many('payroll.incentive.13thmonth.detail', 'incentive_main_id', readonly=False, copy=False)
    bonus_summary_id = fields.One2many('payroll.bonus.month.summary', 'incentive_main_id', readonly=False, copy=False)

    resigned_employee_id = fields.Many2one('hr.employee', 'Employee')


    #For Report 13th Month Summary
    total_computed_amount = fields.Float('Total Computed Amount')
    total_amount_paid = fields.Float('Total Amount Paid')
    total_net_amount = fields.Float('Total 13th Month')


    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generate13thMonth(self):
        self.total_amount = 0
        str_datefrom = str(self.year_from) + '-' +  str(self.month_range_from) + '-01'
        str_dateto = str(self.year_to) + '-' + str(self.month_range_to)+ '-16'
        dt_datefrom = datetime.datetime.strptime(str_datefrom, '%Y-%m-%d')
        dt_dateto = datetime.datetime.strptime(str_dateto, '%Y-%m-%d')
        intSequence = 1

        filter = [('payroll_detail_date', '>=', dt_datefrom),('payroll_detail_date', '<=', dt_dateto)]

        if len(self.resigned_employee_id) > 0:
            filter.append(('employee_id', '=', self.resigned_employee_id.id))



        payroll_details = self.env['hr.payroll.detail'].search(filter)
        incentive_detail = self.env['payroll.incentive.13thmonth.detail']
        incentive_det = incentive_detail.search([('incentive_main_id', '=', self.id)])
        incentive_det.unlink()
        #raise Warning(payroll_details)
        if len(payroll_details) > 0:
            intSequence = 1
            for period in payroll_details:
                if period.employee_id.assignto_workingdays !=8:
                    incentive_number_exists = incentive_detail.search([('employee_id', '=', period.employee_id.id),
                                                                       ('incentive_main_id', '=', self.id)])
                    net_pay = (period.basic_pay_amount + period.basic_pay_leaves_amount) - (period.tardiness_amount + period.undertime_amount)
                    if len(incentive_number_exists) > 0:
                        total_amount = round(incentive_number_exists.total_amount,2)
                        total_amount += round(net_pay,2)
                        incentive_number_exists.write({'total_amount': total_amount})
                    else:
                        incentive_detail.create(
                            {
                                'incentive_main_id': self.id,
                                'employee_id': period.employee_id.id,
                                'name': period.employee_id.name,
                                'employee_number': period.employee_id.employee_number,
                                'total_amount': round(net_pay,2),
                                'amount': 0
                            })
                    intSequence +=1

        employees_incentive = self.env['payroll.incentive.13thmonth.detail'].search([('incentive_main_id', '=', self.id)])

        for employee in employees_incentive:
            if employee.employee_id.active == True:
                employee.write({'amount': round(employee.total_amount/12,2)})
                self.total_amount += round(employee.total_amount/12,2)
            else:

                if employee.employee_id.thirteenth_month_amount > 0:
                    if datetime.datetime.strptime(employee.employee_id.thirteenth_month_date_paid ,'%Y-%m-%d').year \
                            == datetime.datetime.strptime(self.release_date,'%Y-%m-%d').year:
                        employee.write({'amount': round(employee.employee_id.thirteenth_month_amount, 2),
                                        'is_paid': True})
                        self.total_amount += round(employee.employee_id.thirteenth_month_amount, 2)
                else:
                    employee.write({'amount': round(employee.total_amount/12,2)})
                    self.total_amount += round(employee.total_amount/12,2)

        #Removing the Detail after Generation
        incentive_det = incentive_detail.search([('incentive_main_id', '=', False)])
        incentive_det.unlink()

        #Report Creation Detail per Month
        details = self.env['payroll.bonus.month.detail']

        for employee in employees_incentive:
            detail = details.search([('name', '=', employee.employee_id.id)])
            detail.unlink()
            payroll_details = self.env['hr.payroll.detail'].search([('payroll_detail_date', '>=', dt_datefrom),
                                                                   ('payroll_detail_date', '<=', dt_dateto),
                                                                   ('employee_id', '=', employee.employee_id.id)])
            for payroll_detail in payroll_details:
                #raise Warning('dadsasad')
                #Check if Employee for Month-Year already Exists
                model_if_exist = detail.search([('incemtive_detail_id', '=', employee.id),
                                                ('month', '=', payroll_detail.month_name_period),
                                                ('year', '=', payroll_detail.year_payroll_period)])

                net_pay = 0
                basic_amount = 0
                leaveamount = 0
                tardiness  =  0
                basic_amount = payroll_detail.basic_pay_amount
                leaveamount = payroll_detail.basic_pay_leaves_amount
                tardiness = payroll_detail.tardiness_amount
                net_pay = (basic_amount + leaveamount) - tardiness
                if len(model_if_exist) == 0:
                    details.create({
                        'incemtive_detail_id': employee.id,
                        'month':  payroll_detail.month_name_period,
                        'year': payroll_detail.year_payroll_period,
                        'amount': net_pay,
                        'name': employee.employee_id.id
                    })
                else:
                    model_payroll_bonus_month_detail = details.search([('incemtive_detail_id', '=', employee.id),
                                                                        ('month', '=', payroll_detail.month_name_period),
                                                                        ('year', '=', payroll_detail.year_payroll_period)])

                    net_pay += model_payroll_bonus_month_detail.amount

                    model_payroll_bonus_month_detail.write({
                        'amount': net_pay,
                        'name': employee.employee_id.id
                    })
        if len(self.incentive_detail_id) > 0:
            self.generateExcelFileBankPayroll()

    @api.one
    def generate13thMonthSummary(self):
        str_datefrom = str(self.year_from) + '-' +  str(self.month_range_from) + '-01'
        str_dateto = str(self.year_to) + '-' + str(self.month_range_to)+ '-16'
        dt_datefrom = datetime.datetime.strptime(str_datefrom, '%Y-%m-%d')
        dt_dateto = datetime.datetime.strptime(str_dateto, '%Y-%m-%d')
        intSequence = 1

        filter = [('payroll_detail_date', '>=', dt_datefrom),('payroll_detail_date', '<=', dt_dateto)]

        payroll_details = self.env['hr.payroll.detail'].search(filter)
        incentive_detail_summary = self.env['payroll.bonus.month.summary']
        incentive_det_summary = incentive_detail_summary.search([('incentive_main_id', '=', self.id)])
        incentive_det_summary.unlink()

        if len(payroll_details) > 0:
            intSequence = 1
            for period in payroll_details:
                if period.employee_id.assignto_workingdays !=8:
                    incentive_number_exists = incentive_detail_summary.search([('name', '=', period.employee_id.id),
                                                                               ('incentive_main_id', '=', self.id)])
                    net_pay = (period.basic_pay_amount + period.basic_pay_leaves_amount) - (period.tardiness_amount + period.undertime_amount)
                    if len(incentive_number_exists) > 0:
                        total_amount = round(incentive_number_exists.total_yearly_salary,2)
                        total_amount += round(net_pay,2)
                        incentive_number_exists.write({'total_yearly_salary': total_amount})
                    else:
                        incentive_detail_summary.create(
                            {
                                'incentive_main_id': self.id,
                                'name': period.employee_id.id,
                                'total_yearly_salary': round(net_pay,2),
                                'bonus_amount_paid':0,
                                'amount_paid': 0,
                                'total_amount_paid': 0
                            })
                    intSequence +=1

        employees_incentive = self.env['payroll.bonus.month.summary'].search([('incentive_main_id', '=', self.id)])

        # Compute the Net Bonus Amount based on
        # Summary of Salary in on Year / 12 months
        self.total_computed_amount = 0
        self.total_amount_paid = 0
        self.total_net_amount = 0

        for employee in employees_incentive:
            if employee.name.active == True:
                employee.write({'amount_paid': round(employee.total_yearly_salary/12,2),
                                'total_amount_paid': round(employee.total_yearly_salary/12,2)})

                self.total_computed_amount += round(employee.total_yearly_salary/12,2)
                self.total_net_amount += round(employee.total_yearly_salary/12,2)
            else:
                if employee.name.thirteenth_month_amount > 0:
                    if datetime.datetime.strptime(employee.name.thirteenth_month_date_paid ,'%Y-%m-%d').year \
                            == datetime.datetime.strptime(self.release_date,'%Y-%m-%d').year:

                        employee.write({'amount': round(employee.total_yearly_salary/12,2),
                                        'amount_paid': round(employee.total_yearly_salary/12,2),
                                        'release_date':  employee.name.thirteenth_month_date_paid,
                                        'bonus_amount_paid': employee.name.thirteenth_month_amount,
                                        'total_amount_paid': round(employee.total_yearly_salary/12,2)
                                                             - round(employee.name.thirteenth_month_amount, 2)})

                    self.total_computed_amount += round(employee.total_yearly_salary/12,2)
                    self.total_amount_paid += employee.name.thirteenth_month_amount
                    self.total_net_amount += round(employee.total_yearly_salary/12,2) - round(employee.name.thirteenth_month_amount, 2)
                else:
                    employee.write({'amount': round(employee.total_yearly_salary/12,2),
                                    'amount_paid': employee.name.thirteenth_month_amount,
                                    'total_amount_paid': round(employee.total_yearly_salary/12,2)
                                                         - round(employee.name.thirteenth_month_amount, 2)})

                    self.total_computed_amount += round(employee.total_yearly_salary/12,2)
                    self.total_amount_paid += employee.name.thirteenth_month_amount
                    self.total_net_amount += round(employee.total_yearly_salary/12,2) - round(employee.name.thirteenth_month_amount, 2)

    @api.one
    def generateExcelFileBankPayroll(self):

        self.payroll_file = None

        #Creation of Excel File
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Bank Payroll Template",True)

        bankpayroll_detail = self.env['payroll.incentive.13thmonth.detail']
        bank_det =  bankpayroll_detail.search([('incentive_main_id', '=', self.id)])

        # Create Title
        sheet.write(0, 0, "Account Number")
        sheet.write(0, 1, "Name")
        sheet.write(0, 2, "Amount")



        sheet.col(0).width = 8000 # around 220 pixels
        sheet.col(1).width = 8000 # around 220 pixels
        sheet.col(2).width = 8000 # around 220 pixels
        i =1
        for employee in bank_det:
            if not  isinstance(employee.employee_id.bank_account_id.acc_number, bool):
                #raise Warning(i)
                #sheet.col(i).width = 8000 # around 220 pixels
                if isinstance(employee.employee_id.bank_account_id.acc_number, bool):
                    account_number  =""
                else:
                    account_number =  employee.employee_id.bank_account_id.acc_number.replace("-","")
                sheet.write(i, 0, account_number)
                sheet.write(i, 1, employee.employee_id.name)

                sheet.write(i, 2, employee.amount)
                i +=1
                #self.total_amount += employee.amount


        sheet = workbook.add_sheet("Bank Payroll Template Check")

        sheet.write(0, 0, "Name")
        sheet.write(0, 1, "Amount")



        sheet.col(0).width = 8000 # around 220 pixels
        sheet.col(1).width = 8000 # around 220 pixels
        i =1
        for employee in bank_det:
            if isinstance(employee.employee_id.bank_account_id.acc_number, bool):
                sheet.col(i).width = 8000 # around 220 pixels
                if isinstance(employee.employee_id.bank_account_id.acc_number, bool):
                    account_number  =""
                else:
                    account_number =  employee.employee_id.bank_account_id.acc_number.replace("-","")
                sheet.write(i, 0, employee.employee_id.name)

                sheet.write(i, 1, employee.amount)
                i +=1
                #self.total_amount += employee.amount



        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.payroll_file = byte_arr

        #else:
        #    raise Warning('Select a payroll period before generating.')

    @api.one
    def generateExcelFile(self):

        self.total_amount = 0
        self.payroll_file = None

        if self.year_from != self.year_to:
            intSequence = 1
            payroll_details = self.env['hr.payroll.detail'].search([('year_payroll_period', '=', self.year_from),
                                                                   ('month_name_period', '>=', self.month_range_from),
                                                                   ('month_name_period', '<=', 12)])
            incentive_detail = self.env['payroll.incentive.13thmonth.detail']
            incentive_det = incentive_detail.search([('incentive_main_id', '=', self.id)])
            incentive_det.unlink()

            if len(payroll_details) > 0:
                intSequence = 1
                #for period in self.payroll_period.payroll_main_id:
                for period in payroll_details:

                    incentive_number_exists = incentive_detail.search([('employee_id', '=', period.employee_id.id)])
                    net_pay = (period.basic_pay_amount + period.basic_pay_leaves_amount) - (period.tardiness_amount + period.undertime_amount)
                    if len(incentive_number_exists) > 0:
                        total_amount = round(incentive_number_exists.total_amountm,2)
                        total_amount += round(net_pay,2)
                        incentive_number_exists.write({'total_amount': total_amount})
                    else:

                        incentive_detail.create(
                            {
                                'incentive_main_id': self.id,
                                'employee_id': period.employee_id.id,
                                'name': period.employee_id.name,
                                'employee_number': period.employee_id.employee_number,
                                'total_amount': round(net_pay,2),
                                'amount': 0
                            })
                    intSequence +=1

            payroll_details = self.env['hr.payroll.detail'].search([('year_payroll_period', '=', self.year_to),
                                                   ('month_name_period', '>=',1 ),
                                                   ('month_name_period', '<=', self.month_range_to)])
            if len(payroll_details) > 0:
                #for period in self.payroll_period.payroll_main_id:
                for period in payroll_details:
                    incentive_number_exists = incentive_detail.search([('employee_id', '=', period.employee_id.id)])
                    net_pay = (period.basic_pay_amount + period.basic_pay_leaves_amount) - (period.tardiness_amount + period.undertime_amount)
                    if len(incentive_number_exists) > 0:
                        total_amount = round(incentive_number_exists.total_amount,2)
                        total_amount += net_pay
                        incentive_number_exists.write({'total_amount': total_amount})
                    else:

                        incentive_detail.create(
                            {
                                'incentive_main_id': self.id,
                                'employee_id': period.employee_id.id,
                                'name': period.employee_id.name,
                                'employee_number': period.employee_id.employee_number,
                                'total_amount': round(net_pay,2),
                                'amount': 0
                            })
                    intSequence +=1
        else:
            # Get Additional Information
            payroll_detail = self.env['hr.payroll.detail'].search([('year_payroll_period', '>=', self.year_from),
                                                                   ('year_payroll_period', '<=', self.year_to)])
            payroll_details = payroll_detail.search([('month_name_period', '>=', int(self.month_range_from)),
                                                    ('month_name_period', '<=', int(self.month_range_to))])

            incentive_detail = self.env['payroll.incentive.13thmonth.detail']
            incentive_det = incentive_detail.search([('incentive_main_id', '=', self.id)])
            incentive_det.unlink()
            if len(payroll_details) > 0:

                intSequence = 1

                payroll_detail = self.env['hr.payroll.detail'].search([('year_payroll_period', '>=', self.year_from),
                                                                       ('year_payroll_period', '<=', self.year_to)])
                payroll_details = payroll_detail.search([('month_name_period', '>=', int(self.month_range_from)),
                                                         ('month_name_period', '<=', int(self.month_range_to))])


                #for period in self.payroll_period.payroll_main_id:
                for period in payroll_details:
                    if period.employee_id.assignto_workingdays !=8:
                        incentive_number_exists = incentive_detail.search([('employee_id', '=', period.employee_id.id)])
                        net_pay = (period.basic_pay_amount + period.basic_pay_leaves_amount) - (period.tardiness_amount + period.undertime_amount)
                        if len(incentive_number_exists) > 0:
                            total_amount = round(incentive_number_exists.total_amount,2)
                            total_amount += net_pay
                            incentive_number_exists.write({'total_amount': total_amount})
                        else:

                            incentive_detail.create(
                                {
                                    'incentive_main_id': self.id,
                                    'employee_id': period.employee_id.id,
                                    'name': period.employee_id.name,
                                    'employee_number': period.employee_id.employee_number,
                                    'total_amount': round(net_pay,2),
                                    'amount': 0
                                })
                        intSequence +=1

        employees_incentive = self.env['payroll.incentive.13thmonth.detail'].search([('incentive_main_id', '=', self.id)])

        for employee in employees_incentive:
            employee.write({'amount': round(employee.total_amount/12,2)})
            self.total_amount += round(employee.total_amount/12,2)

        incentive_det = incentive_detail.search([('incentive_main_id', '=', False)])
        incentive_det.unlink()

        #For Report Creation
        for employee in employees_incentive:
            details = self.env['payroll.bonus.month.detail']
            if self.year_from != self.year_to:
                detail = details.search([('incemtive_detail_id', '=', employee.id)])
                detail.unlink()

                for month in range(self.month_range_from, 13):
                    model_if_exist = detail.search([('incemtive_detail_id', '=', employee.id),
                                                    ('month', '=', month),
                                                    ('year', '=', self.year_from)])

                    payroll_details = self.env['hr.payroll.detail'].search([('year_payroll_period', '=', self.year_from),
                                                                           ('month_name_period', '=', month),
                                                                           ('employee_id', '=', employee.employee_id.id)])
                    net_pay = 0
                    basic_amount = 0
                    leaveamount = 0
                    tardiness  =  0
                    basic_amount = sum(pdetail.basic_pay_amount for pdetail in payroll_details)
                    leaveamount = sum(pdetail.basic_pay_leaves_amount for pdetail in payroll_details)
                    tardiness = sum(pdetail.tardiness_amount for pdetail in payroll_details)

                    net_pay = (basic_amount + leaveamount) - (tardiness)

                    if len(model_if_exist) == 0:
                        details.create({
                            'incemtive_detail_id': employee.id,
                            'month': month,
                            'year': self.year_from,
                            'amount': net_pay,
                            'name': employee.employee_id.id
                        })

                for month in range(1, self.month_range_to +1):
                    model_if_exist = detail.search([('incemtive_detail_id', '=', employee.id),
                                                    ('month', '=', month),
                                                    ('year', '=', self.year_to)])

                    payroll_details = self.env['hr.payroll.detail'].search([('year_payroll_period', '=', self.year_to),
                                                                           ('month_name_period', '=', month),
                                                                           ('employee_id', '=', employee.employee_id.id)])
                    net_pay = 0
                    basic_amount = 0
                    leaveamount = 0
                    tardiness  =  0
                    basic_amount = sum(pdetail.basic_pay_amount for pdetail in payroll_details)
                    leaveamount = sum(pdetail.basic_pay_leaves_amount for pdetail in payroll_details)
                    tardiness = sum(pdetail.tardiness_amount for pdetail in payroll_details)

                    net_pay = (basic_amount + leaveamount) - (tardiness)

                    if len(model_if_exist) == 0:
                        details.create({
                            'incemtive_detail_id': employee.id,
                            'month': month,
                            'year': self.year_to,
                            'amount': net_pay,
                            'name': employee.employee_id.id
                        })

    @api.one
    def postDraft(self):
        message ="""<span>13th Month Pay</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of 13th Month Pay</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>13th Month Pay</span>
                    <div><b>Status</b>: Draft->Approved</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approve of 13th Month Pay</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        #This will post the 13th Month Paid in Resigned Employee 201 File:
        if len(self.resigned_employee_id) > 0:

            for employee_13thmonth in self.incentive_detail_id:

                model_hr_employee = self.env['hr.employee'].search([('id', '=', employee_13thmonth.employee_id.id),
                                                                    ('active', '=', 0)])
                #raise Warning(model_hr_employee)
                if len(model_hr_employee) > 0:
                    model_hr_employee.write({'thirteenth_month_amount': employee_13thmonth.amount,
                                             'thirteenth_month_date_paid': self.release_date})

        message ="""<span>13th Month Pay</span>
                    <div><b>Status</b>: Approved->Paid</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid of 13th Month Pay</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[2][0]
        self.posted_by_id = self._uid


class BonusPayDetail(models.Model):
    _name = 'payroll.incentive.13thmonth.detail'
    _description = 'Detailed 13 Month Pay'

    incentive_main_id = fields.Many2one('payroll.incentive.13thmonth')
    employee_id = fields.Many2one('hr.employee','Employee ID')
    name = fields.Char('Employee Name')
    employee_number = fields.Char('Employee Number')
    total_amount = fields.Float('Total Yearly Income', default = 0, digits=(18,2))
    amount = fields.Float('13th Pay Amount', default = 0, digits=(18,2))
    incentive_id = fields.One2many('payroll.bonus.month.detail', 'incemtive_detail_id', readonly=False, copy=False)
    is_paid = fields.Boolean('Paid?', default = False)

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

    company_name = fields.Char('Company Name', store=False, compute ='getCompanyName', default = getCompanyName)
    company_address = fields.Char('Company Address', store=False, compute ='getCompanyAddress', default = getCompanyAddress)
    company_contact = fields.Char('Company Contact', store=False, compute ='getCompanyContact', default = getCompanyContact)


class BonusPayDetailEmployee(models.Model):
    _name = 'payroll.bonus.month.detail'
    _description = 'Employee Month Basic Pay Detail'
    _order = 'name,year, month '
    incemtive_detail_id = fields.Many2one('payroll.incentive.13thmonth.detail', 'Payroll Incentive Detail')
    name = fields.Many2one('hr.employee', 'Employee')
    month = fields.Selection(constants.MONTH_SELECTION, 'Month')
    year = fields.Integer('Year')
    amount = fields.Float('Amount', digits=(18,2))
    is_paid = fields.Boolean('Paid?', default = False)


class BonusSummary(models.Model):
    _name = 'payroll.bonus.month.summary'
    _description = 'Employee 13th Month Summary'
    _order = 'name'
    incentive_main_id = fields.Many2one('payroll.incentive.13thmonth')
    name = fields.Many2one('hr.employee', 'Employee')
    total_yearly_salary = fields.Float('Yearly Salary', digits=(18, 2))
    bonus_amount_paid = fields.Float('Amount', digits=(18, 2))
    amount_paid = fields.Float('Amount Paid', digits=(18, 2))
    release_date = fields.Date('Date Paid')
    total_amount_paid = fields.Float('13th Month', digits=(18, 2))
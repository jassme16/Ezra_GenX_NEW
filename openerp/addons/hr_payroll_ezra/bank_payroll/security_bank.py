import xlwt

import base64
from openerp import models, fields, api
from cStringIO import StringIO
from openerp.addons.hr_payroll_ezra.parameters import constants

PAYROLL_STATE_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid')
]


class BankPayrollMain(models.Model):
    _name = 'payroll.bank.template'
    _description = 'Bank Payroll Template'
    _inherit = 'mail.thread'

    @api.one
    def legacy_doc1_getFilename(self):
        self.filename = self.name + ' Bank Payroll.xls'

    name = fields.Char('Bank Payroll Name', required=True)
    payroll_period = fields.Many2one('hr.payroll.main','Payroll Period')

    payroll_month_of = fields.Selection(constants.MONTH_SELECTION, 'for the Month of', required=True)
    payroll_month_quarter = fields.Selection(constants.MONTH_QUARTER_SELECTION,'Month Quarter', required=True)
    payroll_year = fields.Integer('for the Year', default = constants.YEAR_NOW, required=True)

    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount_debit = fields.Float('Total Debit', readonly = True)
    total_amount_check = fields.Float('Total Check', readonly = True)
    total_amount = fields.Float('Grand Total', readonly = True)
    state = fields.Selection(PAYROLL_STATE_STATUS, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')
    payroll_bank_main_id = fields.One2many('payroll.bank.template.detail', 'bank_payroll_detail_id', readonly=False, copy=False)
    payroll_bank_main_check_id = fields.One2many('payroll.bank.template.detail.check', 'bank_payroll_detail_id', readonly=False, copy=False)


    filename = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    payroll_file = fields.Binary('Generate Bank Payroll')

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateBank(self):
        self.total_amount = 0
        self.payroll_file = None

        bankpayroll_check_detail =self.env['payroll.bank.template.detail.check']
        bank_check_det = bankpayroll_check_detail.search([('bank_payroll_detail_id', '=', self.id)])
        bank_check_det.unlink()

        bankpayroll_detail = self.env['payroll.bank.template.detail']
        bank_det = bankpayroll_detail.search([('bank_payroll_detail_id', '=', self.id)])
        bank_det.unlink()
        # For Per Project Assigned Selection
        if len(self.payroll_period) > 0:
            self.total_amount = 0
            self.total_amount_debit = 0
            self.total_amount_check = 0
            for period in self.payroll_period.payroll_main_id:
                if len(period.employee_id.bank_account_id) > 0:
                    if isinstance(period.employee_id.bank_account_id.acc_number, bool):
                        account_number  =""
                    else:
                        account_number =  period.employee_id.bank_account_id.acc_number.replace("-","")

                    if len(self.employee_name) > 0:
                        if self.employee_name == period.employee_id:
                            bankpayroll_detail.create(
                                {
                                    'bank_payroll_detail_id': self.id,
                                    'name': period.employee_id.last_name + ', ' + period.employee_id.first_name,
                                    'account_number': account_number ,
                                    'amount': round(period.net_pay,2)
                                })
                            self.total_amount += round(period.net_pay,2)
                    else:
                        bankpayroll_detail.create(
                            {
                                'bank_payroll_detail_id': self.id,
                                'name': period.employee_id.last_name + ', ' + period.employee_id.first_name,
                                'account_number': period.employee_id.bank_account_id.acc_number,
                                'amount': round(period.net_pay,2)
                            })
                        self.total_amount += round(period.net_pay,2)
        else:
            self.total_amount = 0
            self.total_amount_debit = 0
            self.total_amount_check = 0
            payroll_detail = self.env['hr.payroll.detail'].search([('month_half_period', '=', self.payroll_month_quarter),
                                                                   ('month_name_period', '=', self.payroll_month_of),
                                                                   ('year_payroll_period', '=', self.payroll_year),
                                                                   ('payroll_detail_id.state', '=', 'approved')])
            if len(payroll_detail) > 0:
                for employee in payroll_detail:
                    if isinstance(employee.employee_id.bank_account_id.acc_number, bool):
                        account_number = ""
                    else:
                        account_number =  employee.employee_id.bank_account_id.acc_number.replace("-","")
                    # Employee Has no Bank Account Number
                    if len(employee.employee_id.bank_account_id) > 0:
                        if len(self.employee_name) > 0:
                            if self.employee_name == employee.employee_id:
                                bankpayroll_detail.create(
                                    {
                                        'bank_payroll_detail_id': self.id,
                                        'name': employee.employee_id.last_name + ', ' + employee.employee_id.first_name,
                                        'account_number': account_number,
                                        'amount': round(employee.net_pay,2)
                                    })
                                self.total_amount_debit += round(employee.net_pay,2)
                        else:
                            bankpayroll_detail.create(
                                {
                                    'bank_payroll_detail_id': self.id,
                                    'name': employee.employee_id.last_name + ', ' + employee.employee_id.first_name,
                                    'account_number': account_number,
                                    'amount': round(employee.net_pay,2)
                                })
                            self.total_amount_debit += round(employee.net_pay,2)
                    else:
                        if len(self.employee_name) > 0:
                            if self.employee_name == employee.employee_id:
                                bank_check_det.create(
                                    {
                                        'bank_payroll_detail_id': self.id,
                                        'name': employee.employee_id.last_name + ', ' + employee.employee_id.first_name,
                                        'account_number': "",
                                        'amount': round(employee.net_pay,2)
                                    })
                                self.total_amount_check += round(employee.net_pay,2)
                        else:
                            bank_check_det.create(
                                {
                                    'bank_payroll_detail_id': self.id,
                                    'name': employee.employee_id.last_name + ', ' + employee.employee_id.first_name,
                                    'account_number': "",
                                    'amount': round(employee.net_pay,2)
                                })
                            self.total_amount_check += round(employee.net_pay,2)
        self.total_amount = self.total_amount_debit + self.total_amount_check
        self.generateExcelFile()

    @api.one
    def generateExcelFile(self):

        #self.total_amount = 0
        self.payroll_file = None

        #Creation of Excel File
        workbook = xlwt.Workbook()

        #With Account Number
        sheet = workbook.add_sheet("Bank Payroll Debit",True)

        bankpayroll_detail = self.env['payroll.bank.template.detail']
        bank_det =  bankpayroll_detail.search([('bank_payroll_detail_id', '=', self.id)])

        # Create Title
        sheet.write(0, 0, "Account Number")
        sheet.write(0, 1, "Name")
        sheet.write(0, 2, "Amount")

        sheet.col(0).width = 8000 # around 220 pixels
        sheet.col(1).width = 8000 # around 220 pixels
        sheet.col(2).width = 8000 # around 220 pixels
        i =1
        for employee in bank_det:
            #sheet.col(i).width = 8000 # around 220 pixels
            sheet.write(i, 0, employee.account_number)
            sheet.write(i, 1, employee.name)
            sheet.write(i, 2, employee.amount)


        # For Employee With no Account Number
        sheet = workbook.add_sheet("Bank Payroll Check",True)

        bankpayroll_detail = self.env['payroll.bank.template.detail.check']
        bank_det =  bankpayroll_detail.search([('bank_payroll_detail_id', '=', self.id)])

        # Create Title
        #sheet.write(0, 0, "Account Number")
        sheet.write(0, 0, "Name")
        sheet.write(0, 1, "Amount")

        sheet.col(0).width = 8000 # around 220 pixels
        sheet.col(1).width = 8000 # around 220 pixels
        sheet.col(2).width = 8000 # around 220 pixels
        i =1
        for employee in bank_det:
            sheet.col(i).width = 8000 # around 220 pixels
            sheet.write(i, 0, employee.name)
            sheet.write(i, 1, employee.amount)
            i +=1

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.payroll_file = byte_arr

    @api.one
    def postDraft(self):
        message ="""<span>Bank Payroll</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of Bank Payroll</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = PAYROLL_STATE_STATUS[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>Bank Payroll</span>
                    <div><b>Status</b>: Draft->Approved</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approve of Bank Payroll</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = PAYROLL_STATE_STATUS[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        message ="""<span>Bank Payroll</span>
                    <div><b>Status</b>: Approved->Paid</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid of Bank Payroll</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = PAYROLL_STATE_STATUS[2][0]
        self.posted_by_id = self._uid

class BankPayrollDetail(models.Model):
    _name = 'payroll.bank.template.detail'
    _description = 'Bank Payroll Template Detail'
    _order = 'account_number,name'

    bank_payroll_detail_id = fields.Many2one('payroll.bank.template')
    name = fields.Char('Name')
    account_number = fields.Char('Account Number')
    amount = fields.Char('Amount')

class BankPayrollDetail(models.Model):
    _name = 'payroll.bank.template.detail.check'
    _description = 'Bank Payroll Template Detail Check'
    _order = 'account_number,name'

    #@api.one
    #def _getTotalAmount(self):
    #    total_amount  = 0
    #    model_payroll_check = self.env['payroll.bank.template.detail.check'].search([('bank_payroll_detail_id', '=', self.bank_payroll_detail_id.id)])
    #    for employee_payroll in model_payroll_check:
    #        curr_amount = 0
    #        if not isinstance(employee_payroll.amount, bool):
    #            curr_amount = employee_payroll.amount
    #            self.total_amount += curr_amount

    bank_payroll_detail_id = fields.Many2one('payroll.bank.template')
    name = fields.Char('Name')
    account_number = fields.Char('Account Number')
    amount = fields.Char('Amount')

    #total_amount = fields.Float('Total', digits=(18,2))
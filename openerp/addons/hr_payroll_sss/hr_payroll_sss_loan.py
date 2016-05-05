# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.addons.hr_payroll_ezra.parameters import constants
import xlwt
from cStringIO import StringIO
import base64


class SSSLoanMain(models.Model):
    _name = 'payroll.sss.loan'
    _description = 'SSS Loan'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = 'Employee SSS Loan' + self.name +  '.xls'

    name = fields.Char('SSS Loan name', required=True)
    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount = fields.Float('Total Amount')
    state = fields.Selection(constants.STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')

    for_the_month_of = fields.Selection(constants.MONTH_SELECTION, 'For the Month of')
    for_the_year= fields.Integer('For the Year', default = constants.YEAR_NOW)

    sss_loan_detail_id = fields.One2many('payroll.sss.loan.detail', 'sss_loan_main_ids', readonly=False, copy=False)
    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    payroll_file = fields.Binary('Excel File')

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateExcelFile(self):
        self.total_amount = 0
        self.payroll_file = None

        sss_detail = self.env['payroll.sss.loan.detail']
        sss_det = sss_detail.search([('sss_loan_main_ids', '=', self.id)])
        sss_det.unlink()
        intSequence = 1

        # Get Additional Information
        if len(self.employee_name) > 0:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),('year_payroll_period','=',self.for_the_year),
                                                                   ('employee_id','=', int(self.employee_name[0])),
                                                                   ('payroll_detail_id.state', '=', 'approved')])
        else:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),('year_payroll_period','=',self.for_the_year),
                                                                   ('payroll_detail_id.state', '=', 'approved')])

        for period in payroll_detail:
            if period.employee_id.assignto_workingdays != 8:
                sss_number_exists = sss_detail.search([('name', '=', period.employee_id.sss_no)])
                if period.sss_loan > 0:
                    if len(period.employee_id.sss_no) > 0 and period.employee_id.sss_no !='0000000000':
                        if len(sss_number_exists) > 0:
                            total_amount = sss_number_exists.sss_amount
                            total_amount += period.sss_loan
                            sss_number_exists.write({'sss_amount': total_amount})
                        else:
                            sss_detail.create(
                                {
                                    'sss_loan_main_ids': self.id,
                                    'name': period.employee_id.sss_no,
                                    'last_name': period.employee_id.last_name,
                                    'first_name': period.employee_id.first_name,
                                    'middle_name': period.employee_id.middle_name,
                                    'sss_amount': period.sss_loan,
                                    'remarks': ''
                                })
                        self.total_amount += period.sss_loan
            intSequence +=1
            self.CreateExcel()

    def CreateExcel(self):
        #Cell Properties Setup

        styleTitleMain =xlwt.XFStyle()
        styleColumns = xlwt.XFStyle()
        styleSpecificRow = xlwt.XFStyle()
        styleSpecificRow.num_format_str = "#,##0.00"
        #font
        font  = xlwt.Font()
        font.name = 'Arial'
        font.height =120
        styleTitleMain.font = font
        styleColumns.font = font


        #Creation of Excel File
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("SSS Loan")

        #Get Company Information
        company = self.env['res.company'].search([('id','=',1)])


        #Title Creation
        sheet.write_merge(1,1, 1,3, company.name)
        sheet.write_merge(2,2, 1,3, "Date: " + constants.DATE_NOW_FORMATTED)


        sss_detail = self.env['payroll.sss.loan.detail']
        sss_det = sss_detail.search([('sss_loan_main_ids', '=', self.id)])

        sheet.col(0).width = 13 * constants.PER_PIXEL

        sheet.write(4, 1, "SSS Number")
        sheet.write(4, 2, "EMPLOYEE NAME")
        sheet.write(4, 3, "TOTAL AMOUNT")
        sheet.write(4, 4, "REMARKS")

        intRow = 6
        employee_number = 0
        for employee in sss_det:
            if employee.sss_amount > 0:
                sheet.write(intRow, 1, employee.name)
                sheet.write(intRow, 2,  employee.last_name + ', ' + employee.first_name + ' ' + employee.middle_name[0] + '.')
                sheet.write(intRow, 3, employee.sss_amount, styleSpecificRow)
                sheet.write(intRow, 4, employee.remarks)
                employee_number += 1
                intRow += 1
        sheet.write_merge(intRow,intRow, 1,2, "Grand Total: ")
        sheet.write(intRow, 3, self.total_amount, styleSpecificRow)

        sheet.write_merge(intRow + 3,intRow + 3, 1,3, "Total Number of Employees: " + str(employee_number))
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.payroll_file = byte_arr

    @api.one
    def postDraft(self):
        message ="""<span>SSS Loan</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of SSS Loan</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>SSS Loan</span>
                    <div><b>Status</b>: Draft->Approved</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approve of SSS Loan</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        message ="""<span>SSS Loan</span>
                    <div><b>Status</b>: Approved->Paid</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid of SSS Loan</div>
                    """ %{'user': self.getUseridName()}

        self.state = constants.STATE[2][0]
        self.posted_by_id = self._uid

class SSSLoanDetail(models.Model):
    _name = 'payroll.sss.loan.detail'
    _description = 'Detailed SSS loan'
    _order = 'name asc'

    sss_loan_main_ids = fields.Many2one('payroll.sss.loan')

    name = fields.Char('SSS Number')
    last_name = fields.Char('Last Name')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    sss_amount = fields.Float('Amount', default = 0)
    remarks = fields.Char('Remarks')


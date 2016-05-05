# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.addons.hr_payroll_ezra.parameters import constants
import xlwt
from cStringIO import StringIO
import base64

SSS_REMARKS = [('N','NORMAL'),
               ('1','New Hire'),
               ('3','No Earnings')]

class SSSContributionMain(models.Model):
    _name = 'payroll.sss.contribution'
    _description = 'SSS Contribution'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = 'Employee SSS Premium' + self.name +  '.xls'

    @api.one
    def _getTotalAmount(self):
        if len(self.sss_cont_detail_id) > 0:
            self.total_amount_ee = sum(employee.sss_employee_contribution  for employee in self.sss_cont_detail_id)
            self.total_amount_er = sum(employee.sss_employer_contribution for employee in self.sss_cont_detail_id)
            self.total_amount_ec = sum(employee.employee_compensation for employee in self.sss_cont_detail_id)
            self.total_amount = sum(employee.sss_contribution for employee in self.sss_cont_detail_id)

    name = fields.Char('SSS Premium name', required=True)
    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount = fields.Float('Grand Total',compute ='_getTotalAmount')
    total_amount_ee = fields.Float('Total Employee Share',compute ='_getTotalAmount')
    total_amount_er = fields.Float('Total Employer Share',compute ='_getTotalAmount')
    total_amount_ec = fields.Float('Total Employee Compensation',compute ='_getTotalAmount')




    state = fields.Selection(constants.STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')

    for_the_month_of = fields.Selection(constants.MONTH_SELECTION, 'For the Month of')
    for_the_year= fields.Integer('For the Year', default = constants.YEAR_NOW)

    sss_cont_detail_id = fields.One2many('payroll.sss.contribution.detail', 'sss_cont_main_ids', readonly=False, copy=False)
    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    payroll_file = fields.Binary('Excel File')

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateExcelFile(self):
        self.total_amount = 0
        self.payroll_file = None

        sss_detail = self.env['payroll.sss.contribution.detail']
        sss_det = sss_detail.search([('sss_cont_main_ids', '=', self.id)])
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

        #model_sss = self.env['hr.payroll.ssscontrib']
        model_sss = self.env['payroll.sss.deductions']
        for period in payroll_detail:
            if period.employee_id.assignto_workingdays != 8:
                if period.sss_premium > 0:
                    if len(period.employee_id.sss_no) > 0 and period.employee_id.sss_no !='0000000000':
                        sss_number_exists = sss_detail.search([('name', '=', period.employee_id.sss_no),
                                                               ('sss_cont_main_ids', '=', self.id)])
                        if len(sss_number_exists) > 0:
                            total_amount = sss_number_exists.sss_contribution + (model_sss.getEmployeeCompensation(period.employee_id.id))
                            total_amount += period.sss_premium
                            sss_number_exists.write({'sss_contribution': total_amount})
                        else:
                            #Check Remarks
                            curr_emp_comp =0
                            if period.sss_premium > 0:
                                curr_emp_comp = model_sss.getEmployeeCompensation(period.employee_id.id)
                                curr_sss_ee = period.sss_premium
                                curr_sss_er = model_sss.getSSSDeductions(period.employee_id.id)['ER']
                                sss_contribution = period.sss_premium +model_sss.getSSSDeductions(period.employee_id.id)['ER']
                            sss_detail.create(
                                {
                                    'sss_cont_main_ids': self.id,
                                    'name': period.employee_id.sss_no,
                                    'last_name': period.employee_id.last_name,
                                    'first_name': period.employee_id.first_name,
                                    'middle_name': period.employee_id.middle_name,
                                    'sss_employee_contribution': curr_sss_ee,
                                    'sss_employer_contribution': curr_sss_er,
                                    'monthly_compensation':period.employee_id.contract_id.wage,
                                    'sss_contribution': sss_contribution , #+ model_sss.getSSSDeductions(period.employee_id.id)['ER']
                                    'employee_compensation': curr_emp_comp,
                                    'remarks': 'N',
                                    'date_hired':0})
                            self.total_amount += period.sss_premium
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
        sheet = workbook.add_sheet("SSS Premium")

        #Get Company Information
        company = self.env['res.company'].search([('id','=',1)])


        #Title Creation
        sheet.write_merge(1,1, 1,3, company.name)
        sheet.write_merge(2,2, 1,3, "Date: " + constants.DATE_NOW_FORMATTED)


        sss_detail = self.env['payroll.sss.contribution.detail']
        sss_det = sss_detail.search([('sss_cont_main_ids', '=', self.id)])

        sheet.col(0).width = 13 * constants.PER_PIXEL

        sheet.write(4, 1, "S.S. NUMBER")
        sheet.write(4, 2, "FAMILY NAME")
        sheet.write(4, 3, "GIVEN NAME")
        sheet.write(4, 4, "MIDDLE NAME")
        sheet.write(4, 5, "EMPLOYEE CONTRIBUTION")
        sheet.write(4, 6, "EMPLOYER CONTRIBUTION")
        sheet.write(4, 7, "EMPLOYEE COMPENSATION")
        sheet.write(4, 8, "S.S. CONTRIBUTION")
        sheet.write(4, 9, "REMARKS")
        sheet.write(4, 10, "DATE HIRED")

        intRow = 6
        employee_number = 0
        for employee in sss_det:
            sheet.write(intRow, 1, employee.name)
            sheet.write(intRow, 2,  employee.last_name)
            sheet.write(intRow, 3, employee.first_name)
            sheet.write(intRow, 4, employee.middle_name[0])
            sheet.write(intRow, 5, employee.sss_employee_contribution, styleSpecificRow )
            sheet.write(intRow, 6, employee.sss_employer_contribution, styleSpecificRow )
            sheet.write(intRow, 7, employee.employee_compensation,styleSpecificRow)
            sheet.write(intRow, 8, employee.sss_contribution, styleSpecificRow )
            sheet.write(intRow, 9, employee.remarks)
            sheet.write(intRow, 10, employee.date_hired)
            employee_number += 1
            intRow += 1
        intRow += 1
        sheet.write(intRow, 5, sum(employee.sss_employee_contribution for employee in sss_det), styleSpecificRow )
        sheet.write(intRow, 6, sum(employee.sss_employer_contribution for employee in sss_det), styleSpecificRow )
        sheet.write(intRow, 7, sum(employee.employee_compensation for employee in sss_det),styleSpecificRow)
        sheet.write(intRow, 8, sum(employee.sss_contribution for employee in sss_det), styleSpecificRow )

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
        message ="""<span>SSS Contributions</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of SSS Contributions</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>SSS Contributions</span>
                    <div><b>Status</b>: Draft->Approved</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approve of SSS Contributions</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        message ="""<span>SSS Contributions</span>
                    <div><b>Status</b>: Approved->Paid</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid of SSS Contributions</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = constants.STATE[2][0]
        self.posted_by_id = self._uid

class SSSContributionDetail(models.Model):
    _name = 'payroll.sss.contribution.detail'
    _description = 'Detailed SSS Premium'

    sss_cont_main_ids = fields.Many2one('payroll.sss.contribution')

    name = fields.Char('SS Number')
    last_name = fields.Char('Last Name')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    monthly_compensation = fields.Float('Monthly Compensation', default = 0)
    sss_employee_contribution = fields.Float('Employee Contribution', default = 0)
    sss_employer_contribution = fields.Float('Employer Contribution', default = 0)
    sss_contribution = fields.Float('S.S. Total Contribution', default = 0)
    employee_compensation= fields.Float('Employee Compensation', default = 0)
    remarks = fields.Selection(SSS_REMARKS,'Remarks')
    date_hired = fields.Integer('Date Hired', default = 0)



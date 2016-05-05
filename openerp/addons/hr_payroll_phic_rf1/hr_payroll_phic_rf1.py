# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.addons.hr_payroll_ezra.parameters import constants
import xlwt
from cStringIO import StringIO
import base64



STATE= [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid')
]

PER_PIXEL = 36


class phicMain(models.Model):
    _name = 'payroll.phic'
    _description = 'Philhealth RF-1'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = 'Employers Remmitance Report' + self.name +  '.xls'

    @api.one
    def empShare_func(self):
        self.total_employer_share = 0
        for detail in self.phic_detail_id:
            self.total_employer_share += detail.employer_share
        self.grandTotal = self.total_amount + self.total_employer_share

    name = fields.Char('PHIC Name', required=True)
    payroll_period = fields.Many2one('hr.payroll.main','Payroll Period')
    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount = fields.Float('Total Employee Share')
    state = fields.Selection(STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')

    for_the_month_of = fields.Selection(constants.MONTH_SELECTION, 'For the Month of',required=True)
    for_the_year= fields.Integer('For the Year', default = constants.YEAR_NOW,required=True)

    phic_ids = fields.Many2many('hr.payroll.main','payroll_phic_period_rel', 'phic_id','payroll_period_id', string ="Payroll Period/s")
    phic_detail_id = fields.One2many('payroll.phic.detail', 'phic_main_ids', readonly=False, copy=False)
    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    payroll_file = fields.Binary('Excel File')

    total_employer_share = fields.Float('Total Employer Share',store = False, compute ='empShare_func')
    grandTotal = fields.Float('Grand Total',store = False, compute ='empShare_func')

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateExcelFile(self):

        self.total_amount = 0
        self.payroll_file = None

        #model_hmo = self.env['hr.payroll.hmo']
        model_hmo = self.env['payroll.sss.deductions']

        # Get Additional Information
        if len(self.employee_name) > 0:
            payroll_details = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year),
                                                                   ('employee_id','=',self.employee_name.id)])
        else:
            payroll_details = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year)])
        payroll_detail = payroll_details.sorted(key=lambda r: r.employee_id.last_name)
        phic_detail = self.env['payroll.phic.detail']
        phic_det = phic_detail.search([('phic_main_ids', '=', self.id)])
        phic_det.unlink()

        if len(payroll_detail) > 0:

            intSequence = 1
            #for period in self.payroll_period.payroll_main_id:
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:
                    phic_number_exists = phic_detail.search([('name', '=', period.employee_id.philhealth_no),
                                                             ('phic_main_ids', '=', self.id)])

                    if len(phic_number_exists) > 0:
                        phic_number_exists.write({'employee_share': phic_number_exists.employee_share + period.hmo_premium})
                    else:
                        phic_detail.create(
                            {
                                'phic_main_ids': self.id,
                                'sequence_number': intSequence,
                                'name': period.employee_id.philhealth_no,
                                'last_name': period.employee_id.last_name,
                                'suffix_name': None,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'date_of_birth': period.employee_id.birthday,
                                'gender': period.employee_id.gender,
                                'monthly_salary': model_hmo.getPHICDeductions(period.employee_id.id)['MONTHLY_SALARY'],
                                'employee_share': period.hmo_premium,
                                'employer_share': model_hmo.getPHICDeductions(period.employee_id.id)['ER'],
                                'employee_monthly_salary_bracket': period.employee_id.contract_id.wage})
                    self.total_amount += period.hmo_premium
                    intSequence +=1




            #Creation of Excel File
            workbook = xlwt.Workbook()
            sheet = workbook.add_sheet("RF-1")

            phic_detail = self.env['payroll.phic.detail']
            phic_det = phic_detail.search([('phic_main_ids', '=', self.id)])


            #sheet.write(0, 0, "Sequence")
            #sheet.col(0).width = 45 * PER_PIXEL

            #sheet.write_merge(0,0,2,2,'PHIC NO')
            #sheet.col(1).width = 100 *  PER_PIXEL

            #sheet.write_merge(0,0, 3,3, "LAST NAME")
            #sheet.write_merge(0,0, 4,4, "SUFFIX")
            #sheet.write_merge(0,0, 5,5, "FIRST NAME")
            #sheet.write_merge(0,0, 6,6, "MIDDLE")
            #sheet.write(0, 7, "DATE BIRTH(mm-dd-yyyy)")
            #sheet.write(0, 8, "SEX(M/F)")
            #sheet.write(0, 9, "MONTHLY SALARY BRACKET(MSB)")
            #sheet.write(0, 10, "PS")
            #sheet.write(0, 11, "ES")
            #sheet.write(0, 12, "Employee Status")
            #sheet.write(0, 13, "Remarks")



            sheet.write(0, 0, "Sequence")
            sheet.col(0).width = 45 * PER_PIXEL

            sheet.write_merge(0,0, 2,2, "LAST NAME")
            sheet.col(1).width = 100 *  PER_PIXEL
            sheet.write_merge(0,0, 3,3, "SUFFIX")

            sheet.write_merge(0,0, 4,4, "FIRST NAME")
            sheet.write_merge(0,0, 5,5, "MIDDLE NAME")

            sheet.write_merge(0,0,6,6,'PHIC NO')

            sheet.write(0, 7, "DATE BIRTH(mm-dd-yyyy)")
            sheet.write(0, 8, "SEX(M/F)")
            sheet.write(0, 9, "MONTHLY SALARY BRACKET(MSB)")
            sheet.write(0, 10, "PS")
            sheet.write(0, 11, "ES")
            #sheet.write(0, 12, "Employee Status")
            sheet.write(0, 12, "Remarks")

            if len(phic_det) > 0:
                #Creation of Sequence and PHIC Number
                intRow = 1
                for employee in phic_det:
                    sheet.write(intRow, 0, employee.sequence_number)
                    sheet.write(intRow, 1,'')
                    sheet.write(intRow, 2,employee.last_name)
                    if employee.suffix_name == False:
                        suffix = ''
                    else:
                        suffix = employee.suffix_name
                    sheet.write(intRow, 3, suffix)

                    #sheet.write(intRow, 2,employee.name)

                    sheet.col(1).width = 5 * PER_PIXEL

                    #sheet.write(intRow, 4,  employee.last_name)
                    sheet.write(intRow, 4, employee.first_name)
                    sheet.write(intRow, 5, employee.middle_name)

                    if employee.date_of_birth == False:
                        date_of_Birth = ''
                    else:
                        date_of_Birth = employee.date_of_birth

                    sheet.write(intRow, 6,employee.name)
                    sheet.write(intRow, 7, date_of_Birth)

                    gender = 'M'
                    if employee.gender == 'female':
                        gender = 'F'
                    elif employee.gender == False:
                        gender = ''

                    sheet.write(intRow, 8, gender)
                    sheet.write(intRow, 9, employee.monthly_salary)
                    sheet.write(intRow, 10, employee.employee_share)
                    sheet.write(intRow, 11, employee.employer_share)
                    #sheet.write(intRow, 12, None)
                    if  employee.employee_share == 0:
                        sheet.write(intRow, 12, 'NE')
                    else:
                        sheet.write(intRow, 12, None)
                    intRow +=1

            fp = StringIO()
            workbook.save(fp)
            fp.seek(0)
            data = fp.read()
            fp.close()
            byte_arr = base64.b64encode(data)
            self.payroll_file = byte_arr

    @api.one
    def postDraft(self):
        message ="""<span>Employee Philhealth Contribution</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of Philhealth Contribution</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>Employee Philhealth Contribution</span>
                    <div><b>Status</b>: Draft->Approved</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approve of Philhealth Contribution</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = STATE[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        message ="""<span>Employee Philhealth Contribution</span>
                    <div><b>Status</b>: Approved->Paid</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid Philhealth Contribution</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        self.state = STATE[2][0]
        self.posted_by_id = self._uid

class phicDetail(models.Model):
    _name = 'payroll.phic.detail'
    _description = 'Detailed Philhealth RF-1'
    _order = 'last_name'
    phic_main_ids = fields.Many2one('payroll.phic')

    sequence_number = fields.Integer('Sequence')
    name = fields.Char('Philhealth Identification Number')
    last_name = fields.Char('Last Name')
    suffix_name = fields.Char('Suffix Name')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Middle Name')
    date_of_birth = fields.Date('Date of Birth')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Sex')
    monthly_salary = fields.Float('Monthly Salary', default = 0)
    employee_share = fields.Float('Employee Share', default = 0)
    employer_share= fields.Float('Employer Share', default = 0)
    employee_monthly_salary_bracket= fields.Float('MSB', default = 0)


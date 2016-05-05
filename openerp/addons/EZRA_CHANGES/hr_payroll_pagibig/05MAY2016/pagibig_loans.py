from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp import models, fields, api
from cStringIO import StringIO
import xlwt
import base64


LOAN_TYPE = [('mp3','MP3'),
             ('cal2','CAL2')
            ]


PAGIBIG_COLUMNS = {
    'MID No': 1,
    'Application No': 2,
    'Last Name': 4,
    'First Name': 5,
    'Middle Name': 6,
    'Mid Name': 7,
    'Loan Type': 8,
    'Amout': 9,
    'Remarks': 10,
}


class PagibigLoanMain(models.Model):
    _name = 'payroll.hdmf.loan'
    _description = 'Pag-ibig Employee Loans'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = 'Short-Term loan Remittance.xls'

    name = fields.Char('HDMF Loan Name', required=True)

    for_the_month_of = fields.Selection(constants.MONTH_SELECTION, 'For the Month of')
    for_the_year= fields.Integer('For the Year', default = constants.YEAR_NOW)

    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount = fields.Float('Total with Pagibig ID')
    total_amount_wo_id = fields.Float('Total without Pagibig ID')
    grand_total_amount = fields.Float('Grand total Amount')

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    hdmf_file = fields.Binary('Excel File')

    state = fields.Selection(constants.STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')
    hdmf_detail_id = fields.One2many('payroll.hdmf.loan.detail', 'hdmf_main_id', readonly=False, copy=False)
    hdmf_detail_id_2 = fields.One2many('payroll.hdmf.loan.detail.2', 'hdmf_main_id', readonly=False, copy=False)

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateExcelFile(self):

        self.total_amount = 0
        self.total_amount_wo_id = 0
        self.grand_total_amount = 0
        self.hdmf_file = None

        # Get Additional Information
        if len(self.employee_name) > 0:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year),
                                                                   ('employee_id','=',self.employee_name.id)])
        else:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year)])


        hdmf_detail = self.env['payroll.hdmf.loan.detail']
        hdmf_detail_2 = self.env['payroll.hdmf.loan.detail.2']

        hdmf_det = hdmf_detail.search([('hdmf_main_id', '=', self.id)])
        hdmf_det.unlink()
        hdmf_det = hdmf_detail_2.search([('hdmf_main_id', '=', self.id)])
        hdmf_det.unlink()

        if len(payroll_detail) > 0:
            #For Salary Loan
            # Get Additional Information
            if len(self.employee_name) > 0:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                       ('year_payroll_period','=',self.for_the_year),
                                                                       ('employee_id','=',self.employee_name.id),
                                                                       ('hdmf_salary_loan', '>', 0),
                                                                       ('payroll_detail_id.state', '=', 'approved')])
            else:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                       ('year_payroll_period','=',self.for_the_year),
                                                                       ('hdmf_salary_loan', '>', 0),
                                                                       ('payroll_detail_id.state', '=', 'approved')])

            intSequence = 1
            #Get Employee with HDMF ID
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:
                    if len(period.employee_id.hdmf_no) > 0 and period.employee_id.hdmf_no !='000000000000':
                        if period.employee_id.hdmf_no == 104001439411:
                            raise Warning(period.employee_id.hdmf_no)
                        hdmf_detail.create(
                            {
                                'hdmf_main_id': self.id,
                                'name': period.employee_id.hdmf_no,
                                'application_agr_no': '',
                                'last_name': period.employee_id.last_name,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'loan_Type': 'mp3',
                                'amount': period.hdmf_salary_loan,
                                'remarks': ''})
                        self.total_amount += period.hdmf_salary_loan
                        intSequence +=1

            #Get Employee without HDMF ID
            intSequence = 1
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:
                    if len(period.employee_id.hdmf_no) < 12 or period.employee_id.hdmf_no == '000000000000':
                        hdmf_detail_2.create(
                            {
                                'hdmf_main_id': self.id,
                                'name': period.employee_id.hdmf_no,
                                'application_agr_no': '',
                                'last_name': period.employee_id.last_name,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'loan_Type': 'mp3',
                                'amount': period.hdmf_salary_loan,
                                'remarks': ''})
                        self.total_amount_wo_id += period.hdmf_salary_loan
                        intSequence +=1

            #For Calamity Loan
            if len(self.employee_name) > 0:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year),
                                                                   ('hdmf_calamity_loan', '>', 0),
                                                                   ('employee_id','=',self.employee_name.id),
                                                                   ('payroll_detail_id.state', '=', 'approved')])
            else:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year),
                                                                   ('hdmf_calamity_loan', '>', 0),
                                                                   ('payroll_detail_id.state', '=', 'approved')])
            raise Warning('Test')
            intSequence = 1
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:
                    if len(period.employee_id.hdmf_no) > 0 and period.employee_id.hdmf_no !='000000000000':
                        hdmf_detail.create(
                            {
                                'hdmf_main_id': self.id,
                                'name': period.employee_id.hdmf_no,
                                'application_agr_no': '',
                                'last_name': period.employee_id.last_name,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'loan_Type': 'cal2',
                                'amount': period.hdmf_calamity_loan,
                                'remarks': ''})
                        self.total_amount += period.hdmf_calamity_loan
                        intSequence +=1

            #Get Employee without HDMF ID
            intSequence = 1
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:
                    if len(period.employee_id.hdmf_no) < 12 or period.employee_id.hdmf_no == '000000000000':
                        hdmf_detail_2.create(
                            {
                                'hdmf_main_id': self.id,
                                'name': period.employee_id.hdmf_no,
                                'application_agr_no': '',
                                'last_name': period.employee_id.last_name,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'loan_Type': 'cal2',
                                'amount': period.hdmf_calamity_loan,
                                'remarks': ''})
                        self.total_amount_wo_id += period.hdmf_calamity_loan
                        intSequence +=1

            self.grand_total_amount = self.total_amount + self.total_amount_wo_id
            self.CreateExcel()

    def CreateExcel(self):
        #Cell Properties Setup
        style = xlwt.XFStyle()
        styleTitleMain = xlwt.XFStyle()
        styleTitle = xlwt.XFStyle()
        styleTitle2 = xlwt.XFStyle()
        styleTitle3 = xlwt.XFStyle()
        styleTitle4 = xlwt.XFStyle()
        styleFont =  xlwt.XFStyle()
        styleBorderLeft=  xlwt.XFStyle()
        styleBorderRight=  xlwt.XFStyle()
        styleBorderTop=  xlwt.XFStyle()
        styleBorderBottom=  xlwt.XFStyle()

        #Get Company Setup
        model_ezra = self.env['res.company.setup'].search([('id', '=',1)])
        strhdmf = model_ezra.hdmf_no[0:4] + '-' + model_ezra.hdmf_no[4:8] + '-' + model_ezra.hdmf_no[8:12]

        #font
        fontMain = xlwt.Font()
        font  = xlwt.Font()
        font.name = 'Arial'
        font.height =120
        styleTitle.font = font
        styleTitle2.font = font
        styleFont.font =  font


        #Wraptext

        #border 1
        border = xlwt.Borders()
        border.bottom = xlwt.Borders.THICK
        border.top = xlwt.Borders.THICK
        border.left = xlwt.Borders.THICK
        border.right = xlwt.Borders.THICK
        style.borders = border
        styleTitle.borders = border


        #border 2
        border.top = xlwt.Borders.THICK
        styleTitle2.borders = border


        #Alignment Center
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        styleTitleMain.alignment = alignment

        #MAIN TITLE
        fontMain.name = 'Arial'
        fontMain.height =320
        fontMain.bold = True
        styleTitleMain.font = fontMain



        #Creation of Excel File
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("MCRF",True)
        #Get Company Information
        company = self.env['res.company'].search([('id','=',1)])


        #Title Creation
        sheet.write_merge(5,6, 3,7, "SHORT TERM LOAN",styleTitleMain)
        sheet.write_merge(7,7, 3,7, "REMITTANCE FORM ( STRLF )",styleTitleMain)

        sheet.write_merge(5,6, 9,10, "Pag-IBIG EMPLOYER'S ID NUMBER")
        sheet.write_merge(7,7, 9,10, strhdmf)


        #Company Info
        border3= xlwt.Borders()
        border3.bottom = xlwt.Borders.NO_LINE
        border3.top = xlwt.Borders.THICK
        border3.left = xlwt.Borders.THICK
        border3.right = xlwt.Borders.THICK
        styleTitle3.borders = border3
        
        border4= xlwt.Borders()
        border4.bottom = xlwt.Borders.THICK
        border4.top = xlwt.Borders.NO_LINE
        border4.left = xlwt.Borders.THICK
        border4.right = xlwt.Borders.THICK
        styleTitle4.borders = border4

        borderThickLeft = xlwt.Borders()
        borderThickLeft.bottom = xlwt.Borders.NO_LINE
        borderThickLeft.top = xlwt.Borders.NO_LINE
        borderThickLeft.left = xlwt.Borders.THICK
        borderThickLeft.right = xlwt.Borders.NO_LINE
        styleBorderLeft.borders = borderThickLeft

        borderThickRight = xlwt.Borders()
        borderThickRight.bottom = xlwt.Borders.NO_LINE
        borderThickRight.top = xlwt.Borders.NO_LINE
        borderThickRight.left = xlwt.Borders.NO_LINE
        borderThickRight.right = xlwt.Borders.THICK
        styleBorderRight.borders = borderThickRight


        styleTitle.alignment = alignment
        styleTitle2.alignment= alignment
        styleFont.alignment= alignment


        sheet.write_merge(10,10, 1,10, "EMPLOYER/BUSINESS NAME",styleTitle3)
        sheet.write_merge(11,11, 1,9, company.name, styleBorderLeft )
        sheet.write(11,10, "", styleBorderRight )

        sheet.write_merge(12,12, 1,8, "EMPLOYER/BUSINESS ADDRESS",styleTitle3)

        sheet.write_merge(13,13, 1,3, "Unit/Room No., Floor", styleBorderLeft)

        sheet.write_merge(14,14, 1,3, "", styleBorderLeft)
        sheet.write(13,10, "", styleBorderRight)
        sheet.write(15,10, "", styleBorderRight)

        sheet.write(13, 4, "Building Name")
        sheet.write(14, 4, company.partner_id.street)
        sheet.write_merge(13,13, 5,6, "Lot No., Block No., Phase No. House No")
        sheet.write_merge(13,13, 7,8, "Street Name",styleBorderRight)
        sheet.write_merge(12,12, 9,10, "PERIOD COVERED",styleTitle3)
        sheet.write(13, 9, constants.MONTH_SELECTION[int(self.for_the_month_of) -1][1], styleTitle3)
        sheet.write(13, 10, self.for_the_year,styleTitle3)


        sheet.write_merge(14,14, 9,9, "",styleBorderLeft)
        sheet.write_merge(14,14, 10,10, "",styleBorderRight)

        sheet.write_merge(15,15, 1,1, "Subdivision", styleBorderLeft)
        sheet.write(16,1, company.partner_id.street2, styleBorderLeft)
        sheet.write(15,2, "Barangay")

        sheet.write(15,4, "Municipality/City")
        sheet.write(16,4, company.partner_id.city)

        sheet.write_merge(15,15, 5,6, "Province/State/Country (if abroad)")

        sheet.write_merge(15,15, 8,8, "Zip code",styleBorderRight)
        sheet.write_merge(16,16, 8,8, company.partner_id.zip, styleBorderRight)

        sheet.write_merge(15,15, 9,10, "TELEPHONE NUMBER", styleTitle3)
        sheet.write_merge(16,16, 10,10, company.phone, styleBorderRight)

        hdmf_detail = self.env['payroll.hdmf.loan.detail']
        hdmf_det = hdmf_detail.search([('hdmf_main_id', '=', self.id)])

        sheet.col(0).width = 13 * constants.PER_PIXEL

        sheet.write_merge(17,19, 1,1, "MID",styleTitle)

        sheet.write_merge(17, 19, 2, 2, "APPLICATION/AGREEMENT No.",styleTitle)
        sheet.write_merge(17, 19, 3, 3, "MEMBERSHIP PROGRAM",styleTitle)

        sheet.write_merge(17, 17, 4, 7, "NAME OF BORROWER",styleTitle2)
        sheet.write_merge(18, 19, 4, 4, "Last Name Ext.(JR,SR,III)",styleFont)
        sheet.write_merge(18, 19, 5, 5, "First Name",styleFont)
        sheet.write_merge(18, 19, 6, 6, "Middle Name",styleFont)

        sheet.write_merge(18, 19, 7, 7, "Mid Name",styleFont)

        sheet.write_merge(17, 19, 8, 8, "LOAN TYPE",styleTitle)

        sheet.write_merge(17, 19, 9, 9, "AMOUNT",styleTitle)

        sheet.write_merge(17, 19, 10, 10, "EMPLOYER REMARKS",styleTitle)

        intIndex = 1
        for column in PAGIBIG_COLUMNS:
            sheet.col(intIndex).width = 200 * constants.PER_PIXEL
            intIndex += 1

        intRow = 20
        for employee in hdmf_det:
            sheet.write(intRow, PAGIBIG_COLUMNS['MID No'],  employee.name, style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Application No'], employee.application_agr_no, style)
            sheet.write(intRow, 3, '', style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Last Name'], employee.last_name, style)
            sheet.write(intRow, PAGIBIG_COLUMNS['First Name'], employee.first_name, style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Middle Name'], employee.middle_name, style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Mid Name'], employee.middle_name[0], style)

            if employee.loan_Type == 'mp3':
                sheet.write(intRow, PAGIBIG_COLUMNS['Loan Type'], 'MP3', style)
            else:
                sheet.write(intRow, PAGIBIG_COLUMNS['Loan Type'], 'CAL2', style)

            sheet.write(intRow, PAGIBIG_COLUMNS['Amout'], employee.amount, style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Remarks'], employee.remarks, style)
            intRow += 1
        #Bottom

        #font
        styleBottom = xlwt.XFStyle()
        font = xlwt.Font()
        font.name = 'Arial'
        font.height =140 # 7 * 20
        styleFont.font =  font

        #Border
        border.bottom = xlwt.Borders.THIN
        border.top = xlwt.Borders.THIN
        border.left = xlwt.Borders.THICK
        border.right = xlwt.Borders.THICK
        styleFont.borders = border

        borderLeftRight = xlwt.Borders
        borderLeftRight.bottom = xlwt.Borders.NO_LINE
        borderLeftRight.top = xlwt.Borders.NO_LINE
        borderLeftRight.left = xlwt.Borders.THICK
        borderLeftRight.right = xlwt.Borders.THICK

        sheet.write_merge(intRow,intRow,1,4, "TOTAL FOR THIS PAGE",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        styleFont.borders = border
        intRow +=1

        sheet.write_merge(intRow,intRow,1,4, "GRAND TOTAL (if last page)",styleBorderLeft)
        sheet.write(intRow,9, self.total_amount)
        sheet.write(intRow,10, "",styleBorderRight)
        intRow +=1

        styleFont.font.bold = True
        sheet.write_merge(intRow,intRow,1,10, "EMPLOYER CERTIFICATION",styleFont)
        styleFont.font.bold = False
        intRow +=1
        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        intRow +=1

        sheet.write_merge(intRow,intRow,1,9, "                    I hereby certify under pain of perjury that the information given and all statements made herein are true and correct to the best of my knowledge and belief. I further",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        intRow +=1

        sheet.write_merge(intRow,intRow,1,9, "      certify that my signature appearing herein is genuine and authentic.",styleBorderLeft )
        sheet.write(intRow,10, "",styleBorderRight )
        intRow +=1
        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        intRow +=1
        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        intRow +=1

        styleBorderLeft.alignment = alignment
        styleBorderRight.alignment = alignment

        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        sheet.write_merge(intRow,intRow,1,4, "EVELYN C. BURAC",styleBorderLeft)
        sheet.write_merge(intRow,intRow,6,6, "HR MANAGER")
        sheet.write_merge(intRow,intRow,9,10, "10/15/2015",styleBorderRight)
        intRow +=1

        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        sheet.write_merge(intRow,intRow,1,4, "HEAD OF OFFICE OR AUTHORIZED REPRESENTATIVE",styleBorderLeft)
        sheet.write_merge(intRow,intRow,6,6, "DESIGNATION/POSITION")
        sheet.write_merge(intRow,intRow,9,10, "DATE",styleBorderRight)
        intRow +=1

        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,10, "",styleBorderRight )
        sheet.write_merge(intRow,intRow,1,4, "(Signature Over Printed Name))",styleBorderLeft)
        sheet.write_merge(intRow,intRow,6,6, "")
        sheet.write_merge(intRow,intRow,9,10, "",styleBorderRight)
        intRow +=1

        sheet.write_merge(intRow,intRow,1,10, "",styleTitle4)
        intRow +=1

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.hdmf_file = byte_arr

    @api.one
    def postDraft(self):
        message ="""<span>Employee Pag-ibig Loan</span>
                    <div><b>Status</b>: Approved->Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Rechecking of Pag-ibig Loans</div>
                    """ %{'user': self.getUseridName()}

        self.message_post(body=message)
        self.state = constants.STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="""<span>Employee Pag-ibig Loan</span>
                    <div><b>Status</b>: Draft-> Approved </div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Approved Pagibig-Loan</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)
        self.state = constants.STATE[1][0]
        self.approved_by_id = self._uid

    @api.one
    def post(self):
        message ="""<span>Employee Pag-ibig Loan</span>
                    <div><b>Status</b>: Approved -> Paid </div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Paid Pagibig-Loan</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)
        self.state = constants.STATE[2][0]
        self.posted_by_id = self._uid

class PagibigLoanDetail(models.Model):
    _name = 'payroll.hdmf.loan.detail'
    _description = 'Pag-ibig loan per Member'

    hdmf_main_id = fields.Many2one('payroll.hdmf.loan')
    name = fields.Char('MID No')
    application_agr_no = fields.Char('APPLICATION/AGREEMENT No.')
    last_name = fields.Char('Last Name')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Midddle Name')
    loan_Type = fields.Selection(LOAN_TYPE, 'Loan Type')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')

class PagibigLoanDetail_without_govid(models.Model):
    _name = 'payroll.hdmf.loan.detail.2'
    _description = 'Pag-ibig loan per Member'

    hdmf_main_id = fields.Many2one('payroll.hdmf.loan')
    name = fields.Char('MID No')
    application_agr_no = fields.Char('APPLICATION/AGREEMENT No.')
    last_name = fields.Char('Last Name')
    first_name = fields.Char('First Name')
    middle_name = fields.Char('Midddle Name')
    loan_Type = fields.Selection(LOAN_TYPE, 'Loan Type')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')
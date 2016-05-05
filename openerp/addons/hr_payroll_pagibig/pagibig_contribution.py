from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp import models, fields, api
from cStringIO import StringIO
import xlwt
import base64


PAGIBIG_COLUMNS = {
    'Number': 1,
    'Account Number': 2,
    'Membership Program': 3,
    'Last Name': 4,
    'First Name': 5,
    'Suffix': 6,
    'Middle Name': 7,
    'Mid Name': 8,
    'Period Covered': 9,
    'Monthly Compensation': 10,
    'EE Share': 11,
    'ER Share': 12,
    'Total': 13,
    'Remarks': 14,

}

class PagibigContributionMain(models.Model):
    _name = 'payroll.hdmf.premium'
    _description = 'Pag-ibig Premium'
    _inherit = 'mail.thread'

    @api.one
    def _getFilename(self):
        self.filename = 'Member Contributions.xls'

    @api.one
    def empShare_func(self):
        self.total_employer_share = 0
        for detail in self.hdmf_detail_id:
            self.total_employer_share += detail.employer_share
        self.grandTotal = self.total_amount + self.total_employer_share

    name = fields.Char('HDMF Contribution Name', required=True)

    for_the_month_of = fields.Selection(constants.MONTH_SELECTION, 'For the Month of')
    for_the_year= fields.Integer('For the Year', default = constants.YEAR_NOW)

    employee_name = fields.Many2one('hr.employee', 'Employee Name')
    total_amount = fields.Float('Total Employee Share')

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    hdmf_file = fields.Binary('Excel File')

    state = fields.Selection(constants.STATE, 'Status', default = 'draft')
    approved_by_id = fields.Many2one('res.users', 'Approver')
    posted_by_id = fields.Many2one('res.users', 'Posted by')
    hdmf_detail_id = fields.One2many('payroll.hdmf.premium.detail', 'hdmf_main_id', readonly=False, copy=False)

    total_employer_share = fields.Float('Total Employer Share',store = False, compute ='empShare_func')
    grandTotal = fields.Float('Grand Total',store = False, compute ='empShare_func')

    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.one
    def generateContribution(self):

        return self.hdmf_file

    @api.one
    def generateExcelFile(self):

        self.total_amount = 0
        self.hdmf_file = None

        # Get Additional Information
        if len(self.employee_name) > 0:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year),
                                                                   ('employee_id','=',self.employee_name.id)])
        else:
            payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                   ('year_payroll_period','=',self.for_the_year)])

        #model_hdmf = self.env['hr.payroll.hdmf']
        model_hdmf = self.env['payroll.sss.deductions']

        hdmf_detail = self.env['payroll.hdmf.premium.detail']
        hdmf_det = hdmf_detail.search([('hdmf_main_id', '=', self.id)])
        hdmf_det.unlink()
        intSequence = 1

        #raise Warning(self.id)
        if len(payroll_detail) > 0:

            if len(self.employee_name) > 0:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                       ('year_payroll_period','=',self.for_the_year),
                                                                       ('employee_id','=',self.employee_name.id),
                                                                       ('payroll_detail_id.state', '=', 'approved')])
            else:
                payroll_detail = self.env['hr.payroll.detail'].search([('month_name_period','=',self.for_the_month_of),
                                                                       ('year_payroll_period','=',self.for_the_year),
                                                                       ('payroll_detail_id.state', '=', 'approved')])

            #for period in self.payroll_period.payroll_main_id:
            for period in payroll_detail:
                if period.employee_id.assignto_workingdays != 8:

                    if period.hdmf_premium > 0:
                    #if len(period.employee_id.hdmf_no) > 0 and period.employee_id.hdmf_no !='000000000000':
                    #hdmf_number_exists = hdmf_detail.search([('name', '=', period.employee_id.hdmf_no),
                    #                                         ('hdmf_main_id', '=', self.id)])
                    #if len(hdmf_number_exists) > 0:
                    #    total_amount = hdmf_number_exists.total_contribution
                    #    total_amount += period.hdmf_premium
                    #    hdmf_number_exists.write({'employee_share': hdmf_number_exists.employee_share + period.hdmf_premium,
                    #                              'total_contribution': total_amount})
                    #else:
                        if period.hdmf_premium > 0:
                            curr_employer_share = model_hdmf.getPagibig(period.employee_id.id)['ER']
                        else:
                            curr_employer_share = 0

                        hdmf_detail.create(
                            {
                                'hdmf_main_id': self.id,
                                'name': period.employee_id.hdmf_no,
                                'last_name': period.employee_id.last_name,
                                'suffix_name': None,
                                'first_name': period.employee_id.first_name,
                                'middle_name': period.employee_id.middle_name,
                                'period_covered': str(self.for_the_month_of) + ' ' + str(self.for_the_year) ,
                                'monthly_compensation': model_hdmf.getPagibig(period.employee_id.id)['MONTHLY_SALARY'] ,
                                'employee_share': period.hdmf_premium,
                                'employer_share': curr_employer_share,
                                'total_contribution': period.hdmf_premium + curr_employer_share,
                                'remarks': ''})
                        self.total_amount += period.hdmf_premium
                        intSequence +=1

                    self.CreateExcel()
        #else:
            #raise Warning('Select a payroll period before generating.')

    def CreateExcel(self):
        #Cell Properties Setup
        styleBusinessNameLabel = xlwt.XFStyle()
        styleBusinessName = xlwt.XFStyle()
        styleMainTitle= xlwt.XFStyle()

        style = xlwt.XFStyle()
        styleTitle = xlwt.XFStyle()
        styleTitle2 = xlwt.XFStyle()
        styleFont =  xlwt.XFStyle()
        styleEmployeeCertificate =xlwt.XFStyle()
        styleBorderLeft = xlwt.XFStyle()
        styleBorderRight = xlwt.XFStyle()
        styleRep = xlwt.XFStyle()
        styleDesignation= xlwt.XFStyle()
        styleDate= xlwt.XFStyle()
        styleTitleFooterBottomLine = xlwt.XFStyle()
        stylePagibig = xlwt.XFStyle()

        #Get Company Setup
        model_ezra = self.env['res.company.setup'].search([('id', '=',1)])
        strhdmf = model_ezra.hdmf_no[0:4] + '-' + model_ezra.hdmf_no[4:8] + '-' + model_ezra.hdmf_no[8:12]
        #font
        font  = xlwt.Font()
        font.name = 'Arial'
        font.height =120
        styleTitle.font = font
        styleTitle2.font = font
        styleFont.font =  font

        #Alignment Center
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER

        styleEmployeeCertificate.alignment = alignment
        styleRep.alignment  = alignment
        styleDesignation.alignment  = alignment
        styleDate.alignment  = alignment
        stylePagibig.alignment  = alignment
        styleMainTitle.alignment  = alignment
        styleBusinessName.alignment = alignment

        #Borders
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

        # For Header
        borderBusinessNameLabel = xlwt.Borders()
        borderBusinessNameLabel.bottom = xlwt.Borders.NO_LINE
        borderBusinessNameLabel.top = xlwt.Borders.THICK
        borderBusinessNameLabel.left = xlwt.Borders.THICK
        borderBusinessNameLabel.right = xlwt.Borders.THICK
        styleBusinessNameLabel.borders = borderBusinessNameLabel

        borderBusinessNameLabel = xlwt.Borders()
        borderBusinessNameLabel.bottom = xlwt.Borders.NO_LINE
        borderBusinessNameLabel.top = xlwt.Borders.NO_LINE
        borderBusinessNameLabel.left = xlwt.Borders.THICK
        borderBusinessNameLabel.right = xlwt.Borders.THICK
        styleBusinessName.borders = borderBusinessNameLabel

        borderHeaderLeft = xlwt.Borders()
        borderHeaderLeft.bottom = xlwt.Borders.NO_LINE
        borderHeaderLeft.top = xlwt.Borders.NO_LINE
        borderHeaderLeft.left = xlwt.Borders.THICK
        borderHeaderLeft.right = xlwt.Borders.NO_LINE

        borderHeaderRight = xlwt.Borders()
        borderHeaderRight.bottom = xlwt.Borders.NO_LINE
        borderHeaderRight.top = xlwt.Borders.NO_LINE
        borderHeaderRight.left = xlwt.Borders.NO_LINE
        borderHeaderRight.right = xlwt.Borders.THICK


        # For Footer
        boderDesignation = xlwt.Borders()
        boderDesignation.bottom = xlwt.Borders.THIN
        boderDesignation.top = xlwt.Borders.NO_LINE
        boderDesignation.left = xlwt.Borders.NO_LINE
        boderDesignation.right = xlwt.Borders.NO_LINE
        styleDesignation.borders = boderDesignation


        boderRepresentative = xlwt.Borders()
        boderRepresentative.bottom = xlwt.Borders.THIN
        boderRepresentative.top = xlwt.Borders.NO_LINE
        boderRepresentative.left = xlwt.Borders.THICK
        boderRepresentative.right = xlwt.Borders.NO_LINE
        styleRep.borders = boderRepresentative

        boderDate = xlwt.Borders()
        boderDate.bottom = xlwt.Borders.THIN
        boderDate.top = xlwt.Borders.NO_LINE
        boderDate.left = xlwt.Borders.NO_LINE
        boderDate.right = xlwt.Borders.NO_LINE
        styleDate.borders = boderDate

        borderFooterBottom = xlwt.Borders()
        borderFooterBottom.bottom = xlwt.Borders.THICK
        borderFooterBottom.top = xlwt.Borders.NO_LINE
        borderFooterBottom.left = xlwt.Borders.THICK
        borderFooterBottom.right = xlwt.Borders.THICK
        styleTitleFooterBottomLine.borders = borderFooterBottom




        #Wraptext
        #wraptext = xlwt.Alignment.wrap

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
        stylePagibig.borders = border


        #Alignment
        alignment = xlwt.Alignment
        alignment.HORZ_CENTER


        #Creation of Excel File
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("MCRF")

        #Get Company Information
        company = self.env['res.company'].search([('id','=',1)])


        #Title Creation
        sheet.write_merge(5,6, 3,7, "MEMBER'S CONTRIBUTION",styleMainTitle)
        sheet.write_merge(7,7, 3,7, "REMITTANCE FORM ( MCRF )",styleMainTitle)

        sheet.write_merge(5,6, 9,14, "Pag-IBIG EMPLOYER'S ID NUMBER",stylePagibig)
        sheet.write_merge(7,7, 9,14, strhdmf,stylePagibig)


        #Company Info
        sheet.write_merge(10,10, 1,14, "EMPLOYER/BUSINESS NAME",styleBusinessNameLabel)
        sheet.write_merge(11,11, 1,14, company.name,styleBusinessName)

        sheet.write_merge(12,12, 1,14, "EMPLOYER/BUSINESS ADDRESS",styleBusinessNameLabel)

        sheet.write_merge(13,13, 1,4, "Unit/Room No., Floor",styleBorderLeft)

        sheet.write(13, 5, "Building Name")
        sheet.write(14, 5, company.partner_id.street,styleBorderRight)
        sheet.write_merge(13,13, 7,10, "Lot No., Block No., Phase No. House No")
        sheet.write_merge(13,13, 12,14, "Street Name",styleBorderRight)


        sheet.write(14,1, "",styleBorderLeft)
        sheet.write(14,14, "",styleBorderRight)
        sheet.write_merge(15,15, 1,2, "Subdivision", styleBorderLeft)
        sheet.write(16,1, company.partner_id.street2,styleBorderLeft)
        sheet.write(15,3, "Barangay")
        sheet.write(15,14, "",styleBorderRight)

        sheet.write(15,5, "Municipality/City")
        sheet.write(16,5, company.partner_id.city)
        sheet.write_merge(15,15, 7,10, "Province/State/Country (if abroad)")
        sheet.write_merge(15,15, 12,13, "Zip code")

        sheet.write_merge(16,16, 12,13, company.partner_id.zip)
        sheet.write(16,14, company.partner_id.zip,styleBorderRight)



        hdmf_detail = self.env['payroll.hdmf.premium.detail']
        hdmf_det = hdmf_detail.search([('hdmf_main_id', '=', self.id)])

        sheet.col(0).width = 13 * constants.PER_PIXEL
        sheet.col(8).width = 0


        sheet.write_merge(17,19, 1,1, "Pag-IBIG MID NO./RTN",styleTitle)

        sheet.write_merge(17,19,2, 2, "ACCOUNT NO,",styleTitle)
        sheet.write_merge(17,19,3, 3, "MEMBERSHIP PROGRAM",styleTitle)

        sheet.write_merge(17,17, 4,7, "NAME OF EMPLOYEES",styleTitle2)
        sheet.write_merge(18,19, 4,4, "Last Name",styleFont)
        sheet.write_merge(18,19, 5,5, "First Name",styleFont)
        sheet.write(18, 6, "NAME EXT.",styleFont)
        sheet.write(19, 6, "(JR., III, ETC)",styleFont)
        sheet.write_merge(18,19, 7,7, "Middle Name",styleFont)

        sheet.write_merge(18,19,8, 8, "Mid Name",styleFont)

        sheet.write_merge(17,19, 9,9, "Period Covered",styleTitle)

        sheet.write_merge(17,19,10, 10, "MONTHLY COMPENSATION",styleTitle)

        sheet.write_merge(17,17,11,13, "MEMBERSHIP CONTRIBUTIONS",styleTitle)
        sheet.write(18, 11, "EE",styleTitle)
        sheet.write(19, 11, "SHARE",styleTitle)
        sheet.write(18, 12, "ER",styleTitle)
        sheet.write(19, 12, "SHARE",styleTitle)
        sheet.write_merge(18,19,13,13, "TOTAL",styleTitle)

        sheet.write_merge(17,19,14,14, "REMARKS",styleTitle)


        intRow = 20
        for employee in hdmf_det:
            if isinstance(employee.suffix_name, bool):
                suffix = ""
            else:
                suffix = employee.suffix_name
            sheet.write(intRow, PAGIBIG_COLUMNS['Number'],  employee.name,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Account Number'], employee.name,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Membership Program'], '',style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Last Name'], employee.last_name,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['First Name'], employee.first_name,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Suffix'], suffix,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Middle Name'], employee.middle_name,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Mid Name'], employee.middle_name[0],style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Period Covered'], employee.period_covered,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Monthly Compensation'], employee.monthly_compensation,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['EE Share'], employee.employee_share,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['ER Share'], employee.employer_share,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Total'], employee.total_contribution,style)
            sheet.write(intRow, PAGIBIG_COLUMNS['Remarks'], employee.remarks,style)
            intRow += 1

        #Bottom
        #font
        styleBottom = xlwt.XFStyle()
        font  = xlwt.Font()
        font.name = 'Arial'
        font.height =140 # 7 * 20
        styleFont.font =  font
        styleEmployeeCertificate.font= font


        #Border
        border.bottom = xlwt.Borders.THIN
        border.top = xlwt.Borders.THIN
        border.left = xlwt.Borders.THICK
        border.right = xlwt.Borders.THICK
        styleFont.borders = border
        styleEmployeeCertificate.borders = border

        borderLeftRight = xlwt.Borders
        borderLeftRight.bottom = xlwt.Borders.NO_LINE
        borderLeftRight.top = xlwt.Borders.NO_LINE
        borderLeftRight.left = xlwt.Borders.THICK
        borderLeftRight.right = xlwt.Borders.THICK

        sheet.write_merge(intRow,intRow,1,4, "TOTAL FOR THIS PAGE",styleFont)
        sheet.write(intRow,11, "",styleFont)
        sheet.write(intRow,12, "",styleFont)
        sheet.write(intRow,14, "",styleFont)
        styleFont.borders = border
        intRow +=1

        curr_employer_share = sum(employee.employer_share for employee in hdmf_det)
        curr_grand_total = sum(employee.total_contribution for employee in hdmf_det)

        sheet.write_merge(intRow,intRow,1,4, "GRAND TOTAL (if last page)",styleFont)
        sheet.write(intRow,11, self.total_amount,styleFont)
        sheet.write(intRow,12, curr_employer_share,styleFont)
        sheet.write(intRow,13, curr_grand_total,styleFont)
        sheet.write(intRow,14, "",styleFont)
        intRow +=1

        styleEmployeeCertificate.font.bold = True
        sheet.write_merge(intRow,intRow,1,14, "EMPLOYER CERTIFICATION",styleEmployeeCertificate)
        intRow +=1
        sheet.write(intRow,1, "",styleFont)
        sheet.write(intRow,14, "",styleFont)
        intRow +=1

        sheet.write_merge(intRow,intRow,1,14, "                    I hereby certify under pain of perjury that the information given and all statements made herein are true and correct to the best of my knowledge and belief. I further",styleFont)
        intRow +=1

        sheet.write_merge(intRow,intRow,1,14, "      certify that my signature appearing herein is genuine and authentic.",styleFont)
        intRow +=1

        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,14, "",styleBorderRight)
        intRow +=1

        sheet.write(intRow,1, "",styleBorderLeft)
        sheet.write(intRow,14, "",styleBorderRight)
        intRow +=1

        font  = xlwt.Font()
        font.name = 'Arial'
        font.height =160
        styleRep.font= font
        styleDesignation.font= font
        styleDate.font= font
        styleBorderLeft.font= font

        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER


        sheet.write_merge(intRow,intRow,1, 5, "EVELYN C. BURAC",styleRep)
        sheet.write_merge(intRow,intRow,7, 10, "HR MANAGER",styleDesignation)
        sheet.write_merge(intRow,intRow,12, 13, "10/19/2015",styleDate)
        intRow +=1


        styleBorderLeft.alignment = alignment
        styleBorderLeft.font = font

        border = xlwt.Borders()
        border.bottom = xlwt.Borders.NO_LINE
        border.top = xlwt.Borders.NO_LINE
        border.left = xlwt.Borders.NO_LINE
        border.right = xlwt.Borders.NO_LINE
        styleDate.borders = boderDate
        style.borders = border
        style.alignment = alignment
        style.font = font
        sheet.write_merge(intRow,intRow,1, 6, "HEAD OF OFFICE OR AUTHORIZED REPRESENTATIVE",styleBorderLeft)
        sheet.write_merge(intRow,intRow,7, 10, "DESIGNATION/POSITION",style)
        sheet.write_merge(intRow,intRow,12, 13, "DATE",style)
        sheet.write(intRow,14, "",styleBorderRight)
        intRow +=1

        font = xlwt.Font()
        font.name = 'Arial'
        font.height =120
        styleBorderLeft.font= font

        sheet.write_merge(intRow,intRow,1, 6, "(Signature Over Printed Name)",styleBorderLeft)
        sheet.write(intRow,14, "",styleBorderRight)
        intRow +=1
        #sheet.write(intRow,14, "",styleBorderRight)
        sheet.write_merge(intRow,intRow,1, 14, "",styleTitleFooterBottomLine)

        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.hdmf_file = byte_arr

    @api.one
    def postDraft(self):
        message ="<span>Contributions Re-check</span><div><b>Status</b>: Approved->Draft</div><div><b>Re-check by</b>: %(user)s </div><div><b>Type</b>: Rechecking of Pagibig-Contribution</div>" %{'user': self.getUseridName()}
        self.message_post(body=message)
        self.state = constants.STATE[0][0]
        self.approved_by_id = None
        self.posted_by_id = None

    @api.one
    def postApproved(self):
        message ="<span>Contributions Approved</span><div><b>Status</b>: Draft->Approved</div><div><b>Approved by</b>: %(user)s </div><div><b>Type</b>: Approval of Pagibig-Contribution</div>" %{'user': self.getUseridName()}
        self.state = constants.STATE[1][0]
        self.approved_by_id = self._uid
        self.message_post(body=message)

    @api.one
    def post(self):
        message ="<span>Contributions Paid</span> <div><b>Status</b>: Approved->Paid</div><div><b>Confirmed by</b>: %(user)s </div><div><b>Type</b>: Rechecking of Pagibig-Contribution</div>" %{'user': self.getUseridName()}
        self.message_post(body=message)
        self.state = constants.STATE[2][0]
        self.posted_by_id = self._uid

class PagibigContributionDetail(models.Model):
    _name = 'payroll.hdmf.premium.detail'
    _description = 'Pag-ibig Premium per Member'

    hdmf_main_id = fields.Many2one('payroll.hdmf.premium')
    name = fields.Char('MID No/RTN.')
    last_name = fields.Char('Last Name')
    first_name = fields.Char('First Name')
    suffix_name = fields.Char('Suffix')
    middle_name = fields.Char('Middle Name')
    period_covered = fields.Char('Period Covered')
    monthly_compensation = fields.Float('Monthly Compensation')
    employee_share = fields.Float('EE Share')
    employer_share = fields.Float('ER Share')
    total_contribution = fields.Float('Total')
    remarks = fields.Text('Remarks')


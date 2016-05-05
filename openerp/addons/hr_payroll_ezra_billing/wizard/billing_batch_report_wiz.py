# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from cStringIO import StringIO
import xlwt
import xlrd
#import openpyxl
import base64

FORMAT_STR = [(1, 'Format Report 1'),
              (2, 'Format Report 2'),

]


class BillingBatchReport(models.TransientModel):
    _name = 'billing.batch.report.wiz'
    _description = 'Batch Billing Report'

    @api.one
    def _getFilename(self):
        self.filename = 'Client Billing.xls'

    name = fields.Char('Name', default ="Batch Billing Report")
    job_id = fields.Many2one('hr.job', 'Job Title')
    attendance_id = fields.Many2one('hr.attendance.main', 'Attendance', domain = {'attendance_status' : 'approved'})
    report_format = fields.Selection(FORMAT_STR, 'Report Format', default=1)

    billing_month_of = fields.Selection(constants.MONTH_SELECTION, 'for the Month of', reguired = True)
    billing_month_quarter = fields.Selection(constants.MONTH_QUARTER_SELECTION, required = True)

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    billing_file = fields.Binary('Excel File')

    customer_id = fields.Many2one('res.partner', 'Customer')
    customer_branches_id = fields.Many2one('res.customer.branches', 'Branches')


    @api.one
    def generateReport(self):
        if len(self.job_id) > 0 and len(self.customer_branches_id) == 0:
            raise Warning("Select first the Branch before generating the report.")

        styleTitleFrom =xlwt.XFStyle()
        styleTitleTo =xlwt.XFStyle()
        styleTitleRe =xlwt.XFStyle()
        styleTitleDetails =xlwt.XFStyle()
        styleTitleAmount =xlwt.XFStyle()
        styleColumns =xlwt.XFStyle()
        styleData =xlwt.XFStyle()
        styleBottom_in_name = xlwt.XFStyle()
        styleFooter = xlwt.XFStyle()
        styleBottom =xlwt.XFStyle()
        styleLeft=xlwt.XFStyle()
        styleBottomLeft =xlwt.XFStyle()
        styleBottomRight=xlwt.XFStyle()

        #Alignment Center
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        alignment.vert = xlwt.Alignment.VERT_CENTER
        alignment.Wrap = 1
        styleColumns.alignment = alignment
        styleColumns.alignment.wrap = 1

        #border 1
        border = xlwt.Borders()
        border.bottom = xlwt.Borders.THICK
        border.top = xlwt.Borders.THICK
        border.left = xlwt.Borders.THICK
        border.right = xlwt.Borders.THICK
        styleTitleDetails.borders = border
        styleTitleAmount.borders = border
        styleColumns.borders = border

        #border Data
        borderdata = xlwt.Borders()
        borderdata.bottom = xlwt.Borders.NO_LINE
        borderdata.top = xlwt.Borders.NO_LINE
        borderdata.left = xlwt.Borders.THICK
        borderdata.right = xlwt.Borders.THICK

        borderdataBottom = xlwt.Borders()
        borderdataBottom.bottom = xlwt.Borders.THICK
        borderdataBottom.top = xlwt.Borders.NO_LINE
        borderdataBottom.left = xlwt.Borders.THICK
        borderdataBottom.right = xlwt.Borders.THICK

        borderLeft = xlwt.Borders()
        borderLeft.bottom = xlwt.Borders.NO_LINE
        borderLeft.top = xlwt.Borders.NO_LINE
        borderLeft.left = xlwt.Borders.THICK
        borderLeft.right = xlwt.Borders.NO_LINE

        borderdataBottomLeft = xlwt.Borders()
        borderdataBottomLeft.bottom = xlwt.Borders.THICK
        borderdataBottomLeft.top = xlwt.Borders.NO_LINE
        borderdataBottomLeft.left = xlwt.Borders.THICK
        borderdataBottomLeft.right = xlwt.Borders.NO_LINE

        borderBottom_in_name = xlwt.Borders()
        borderBottom_in_name.bottom = xlwt.Borders.THICK
        borderBottom_in_name.top = xlwt.Borders.NO_LINE
        borderBottom_in_name.left = xlwt.Borders.NO_LINE
        borderBottom_in_name.right = xlwt.Borders.NO_LINE

        styleBottomLeft.borders = borderdataBottomLeft
        styleLeft.borders = borderLeft
        styleData.borders = borderdata
        styleBottom.borders = borderdataBottom
        styleBottom_in_name.borders = borderBottom_in_name

        styleData.num_format_str = '#,##0.00'
        styleFooter.num_format_str = '#,##0.00'
        #font
        font = xlwt.Font()
        font.name = 'Arial'
        font.height =120

        model_client_billing_info = self.env['res.customer.setup'].search([('customer_id', '=', self.customer_id.id),
                                                                     ('job_id', '=', self.job_id.id)])

        #Sample Generation

        #workbooks = xlrd.open_workbook('C:\SAMPLE\Book1.xls')
        #sheet1 = workbooks.sheet_by_index(0)

        #Creation of Excel File
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet("Billing - Batch", True)


        #Get Company Information
        company = self.env['res.company'].search([('id','=',1)])

        total_amount = 0
        intRow = 6
        if self.report_format == 1:

            if len(self.customer_branches_id) > 0:
                model_cust_branches = self.env['res.customer.branches'].search([('customer_info','=', self.customer_branches_id.id),
                                                                                ('main_detail_id.customer_info','=', self.customer_id.id)])
            else:
                model_cust_branches = self.env['res.customer.branches'].search([('main_detail_id.customer_info','=', self.customer_id.id)])

            for branch in model_cust_branches:
                billing_details = self.env['billing.detail'].sorted(key = lambda r: r.employee_id.last_name)
                if len(self.job_id) > 0:
                    billing_detail = billing_details.search([('employee_id.job_id', '=', self.job_id.id),
                                                             ('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                             ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])

                else:
                    billing_detail = billing_details.search([('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                             ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])

            # Main Customer
            model_customers = self.env['res.customers.main'].search([('customer_info','=', self.customer_id.id)])

            #Per Branch
            if len(self.customer_branches_id) > 0:
                model_branch = model_customers.search([('main_cust_id.customer_info', '=', self.customer_branches_id.id)])
            else:
                model_branch = model_customers.search([])

            model_bran = model_branch.main_cust_id

            #Per Jobs
            lst_ids = []
            for customer in model_bran:
                lst_ids.append(customer.customer_info.id)

            if len(self.job_id) > 0:
                model_cust_project = self.env['res.customer.setup'].search([('job_id','=', self.job_id),('customer_id.id', 'in', lst_ids)])
            else:
                model_cust_project = self.env['res.customer.setup'].search([('customer_id.id', 'in', lst_ids)])
            intRow = 1
            for projects in model_cust_project.sorted(key = lambda r: r.job_id.name):

                billing_details = self.env['billing.detail'].sorted(key = lambda r: r.employee_id.last_name)
                billing_detail = billing_details.search([('billing_main_id.job_id', '=', projects.job_id.id),
                                                         ('billing_main_id.customer_id', '=', projects.customer_id.id),
                                                         ('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                         ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])
                billing_main = self.env['billing.main'].search([('customer_id', '=',projects.customer_id.id),
                                                                ('attendance_id.month_of', '=',self.billing_month_of),
                                                                ('attendance_id.month_quarter', '=',self.billing_month_quarter),
                                                                ('job_id', '=', projects.job_id.id)])

                if len(billing_detail) > 0:
                    style0 = xlwt.easyxf('font: name Arial, color-index red, bold on')
                    sheet.write(intRow,1,"FR :",styleTitleFrom)

                    sheet.write(intRow,2,company.name,styleTitleFrom)
                    intRow+=1
                    sheet.write(intRow,1,"TO :",styleTitleTo)
                    sheet.write(intRow,2,billing_main.customer_id.name,styleTitleRe)
                    intRow+=1

                    sheet.write(intRow,1,"RE :",styleTitleRe)
                    sheet.write(intRow,2,"BILLING - " + str(billing_main.attendance_id.schedule_datefrom) + ' - ' \
                                + str(billing_main.attendance_id.schedule_dateto),styleTitleRe)
                    intRow +=1
                    sheet.write_merge(intRow,intRow,6,13,projects.job_id.name  ,style0)
                    intRow +=3
                    sheet.write_merge(intRow,intRow, 1,15, "DETAILS", styleColumns)
                    sheet.write_merge(intRow,intRow, 16,33, "AMOUNT", styleColumns)

                    intRow +=1
                    sheet.write_merge(intRow ,intRow  + 6, 1,4, "Name of Employee", styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5, 5,5, "Add'l/Less Days", styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,6,6,"Late/UT",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,7,7,"Straight Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,8,8,"Night Diff.",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,9,9,"OT - Regular",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,10,10,"OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,11,11,"Excess OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,12,12,"Special Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,13,13,"OT - Special Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,14,14,"Legal Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,15,15,"OT - Legal Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,16,16,"Contract Amount",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,17,17,"Add'l Less Days",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,18,18,"Late/UT",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,19,19,"Straight Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,20,20,"Night Diff.",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,21,21,"OT - Regular",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,22,22,"OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,23,23,"Excess OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,24,24,"Special Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,25,25,"OT - Special Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,26,26,"Legal Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,27,27,"OT - Legal Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,28,28,"13th Month Pay",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,29,29,"5 Days Incentive Leave",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,30,30,"Allowance",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,31,31,"Overhead Cost",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,32,32,"Govt Inc.",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 6,33,33,"Total",styleColumns)

                    intRow +=6
                    sheet.write(intRow,5,"(days)",styleColumns)
                    sheet.write(intRow,6,"(mins)",styleColumns)
                    sheet.write(intRow,7,"(hrs)",styleColumns)
                    sheet.write(intRow,8,"(hrs)",styleColumns)
                    sheet.write(intRow,9,"(hrs)",styleColumns)
                    sheet.write(intRow,10,"(hrs)",styleColumns)
                    sheet.write(intRow,11,"(hrs)",styleColumns)
                    sheet.write(intRow,12,"(hrs)",styleColumns)
                    sheet.write(intRow,13,"(hrs)",styleColumns)
                    sheet.write(intRow,14,"(hrs)",styleColumns)
                    sheet.write(intRow,15,"(hrs)",styleColumns)
                    sheet.write(intRow,16,"(per mo.)",styleColumns)
                    sheet.write(intRow,17,"(per day)",styleColumns)
                    sheet.write(intRow,18,"(per min)",styleColumns)
                    sheet.write(intRow,19,"(per hr)",styleColumns)
                    sheet.write(intRow,20,"(per hr)",styleColumns)
                    sheet.write(intRow,21,"(per hr)",styleColumns)
                    sheet.write(intRow,22,"(per hr)",styleColumns)
                    sheet.write(intRow,23,"(per hr)",styleColumns)
                    sheet.write(intRow,24,"(per hr)",styleColumns)
                    sheet.write(intRow,25,"(per hr)",styleColumns)
                    sheet.write(intRow,26,"(per hr)",styleColumns)
                    sheet.write(intRow,27,"(per hr)",styleColumns)
                    sheet.write(intRow,28,"(pesos)",styleColumns)
                    sheet.write(intRow,29,"(pesos)",styleColumns)
                    sheet.write(intRow,30,"(pesos)",styleColumns)
                    sheet.write(intRow,31,"(pesos)",styleColumns)
                    sheet.write(intRow,32,"(pesos)",styleColumns)


                    #Amount Details Columns
                    model_workhourtype = self.env['hr.workhourtype']
                    model_client_billing_info = self.env['res.customer.setup'].search([('customer_id', '=', self.customer_id.id),
                                                                                 ('job_id', '=', self.job_id.id)
                                                                                 ])
                    daily_rate  = (model_client_billing_info.total_labor_cost * constants.MONTHS_IN_YEAR) / (constants.WEEKS_IN_YEAR * constants.WORK_IN_WEEK)
                    hourly_rate = daily_rate / constants.HOURS_PER_DAY

                    intRow -=1

                    sheet.write(intRow,16,model_client_billing_info.total_labor_cost/2, styleColumns)
                    sheet.write(intRow,17,daily_rate ,styleColumns)
                    sheet.write(intRow,18,hourly_rate/constants.MINUTES,styleColumns)
                    sheet.write(intRow,19,model_workhourtype.getAmountRateAmount('NDIFF',hourly_rate),styleColumns)
                    sheet.write(intRow,20,model_workhourtype.getAmountRateAmount('STRDUTY',hourly_rate),styleColumns)
                    sheet.write(intRow,21,model_workhourtype.getAmountRateAmount('ROT',hourly_rate),styleColumns)
                    sheet.write(intRow,22,model_workhourtype.getAmountRateAmount('RESTDRATE',hourly_rate),styleColumns)
                    sheet.write(intRow,23,model_workhourtype.getAmountRateAmount('RESTOT',hourly_rate),styleColumns)
                    sheet.write(intRow,24,model_workhourtype.getAmountRateAmount('SPEHDRATE',hourly_rate),styleColumns)
                    sheet.write(intRow,25,model_workhourtype.getAmountRateAmount('SPEHOT',hourly_rate),styleColumns)
                    sheet.write(intRow,26,model_workhourtype.getAmountRateAmount('REGHDRATE',hourly_rate),styleColumns)
                    sheet.write(intRow,27,model_workhourtype.getAmountRateAmount('REGHOT',hourly_rate),styleColumns)
                    sheet.write(intRow,28,model_client_billing_info.thirteenth_month,styleColumns)
                    sheet.write(intRow,29,model_client_billing_info.total_labor_cost/2,styleColumns)
                    sheet.write(intRow,30,model_client_billing_info.allowance/2,styleColumns)
                    sheet.write(intRow,31,model_client_billing_info.overhead_cost,styleColumns)
                    sheet.write(intRow,32,model_client_billing_info.due_to_government,styleColumns)

                    intRow +=2

                    sheet.write(intRow,1,"",styleLeft)

                    for i in range(5,34):
                        sheet.write(intRow,i,"",styleData)

                    intRow +=1
                    for employee in billing_detail:
                        fontData = xlwt.Font()
                        styleEmployeeName = xlwt.XFStyle()
                        #To Check if Employee has a reliever or not
                        if employee.has_a_reliever == True:
                            fontData.colour_index = 0x0A
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, employee.sequence, styleLeft)
                            sheet.write(intRow, 2, employee.parent_employee_id.name,styleEmployeeName)

                        elif employee.is_reliever == True:
                            fontData.colour_index = 0x0C
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, "", styleLeft)
                            sheet.write(intRow, 2, "**",styleEmployeeName)
                            sheet.write(intRow, 3, employee.employee_reliever_id.name,styleEmployeeName)
                        else:
                            fontData.colour_index = 0x08
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, employee.sequence, styleLeft)
                            sheet.write(intRow, 2, employee.employee_id.name,styleEmployeeName)

                        sheet.write(intRow,5,employee.details_less_day,styleData)
                        sheet.write(intRow,6,employee.details_tardiness_ut,styleData)
                        sheet.write(intRow,7,employee.details_straight_duty,styleData)
                        sheet.write(intRow,8,employee.details_night_diff,styleData)
                        sheet.write(intRow,9,employee.details_overtime_reqular,styleData)
                        sheet.write(intRow,10,employee.details_restday,styleData)
                        sheet.write(intRow,11,employee.details_overtime_restday,styleData)
                        sheet.write(intRow,12,employee.details_special_holiday,styleData)
                        sheet.write(intRow,13,employee.details_overtime_special_holiday,styleData)
                        sheet.write(intRow,14,employee.details_legal_holiday,styleData)
                        sheet.write(intRow,15,employee.details_overtime_legal_holiday,styleData)
                        sheet.write(intRow,16,employee.amount_contract,styleData)
                        sheet.write(intRow,17,employee.amount_less_day,styleData)
                        sheet.write(intRow,18,employee.amount_tardiness_ut,styleData)
                        sheet.write(intRow,19,employee.amount_straight_duty,styleData)
                        sheet.write(intRow,20,employee.amount_night_diff,styleData)
                        sheet.write(intRow,21,employee.amount_overtime_reqular,styleData)
                        sheet.write(intRow,22,employee.amount_restday,styleData)
                        sheet.write(intRow,23,employee.amount_overtime_restday,styleData)
                        sheet.write(intRow,24,employee.amount_special_holiday,styleData)
                        sheet.write(intRow,25,employee.amount_overtime_special_holiday,styleData)
                        sheet.write(intRow,26,employee.amount_legal_holiday,styleData)
                        sheet.write(intRow,27,employee.amount_legal_holiday,styleData)
                        sheet.write(intRow,28,employee.amount_thirteenth_month,styleData)
                        sheet.write(intRow,29,employee.amount_incentive_leaves,styleData)
                        sheet.write(intRow,30,employee.amount_allowance,styleData)
                        sheet.write(intRow,31,employee.amount_overheadcost,styleData)
                        sheet.write(intRow,32,employee.amount_govt_inc,styleData)
                        sheet.write(intRow,33,employee.amount_total,styleData)
                        total_amount +=employee.amount_total
                        intRow +=1

                sheet.write(intRow,1,"",styleBottomLeft)
                sheet.write(intRow,2,"",styleBottom_in_name)
                sheet.write(intRow,3,"",styleBottom_in_name)
                sheet.write(intRow,4,"",styleBottom_in_name)


                for intRowBottom in range(5,34):
                    sheet.write(intRow,intRowBottom,"",styleBottom)
                intRow +=1

                #Footer and Data
                sheet.write(intRow,29,"Subtotal ")
                sheet.write_merge(intRow,intRow,31,33,total_amount,styleFooter)
                intRow +=1

                sheet.write_merge(intRow,intRow,29,30,"Add : Supplies ")
                sheet.write_merge(intRow,intRow,31,33,projects.supplies,styleFooter)
                intRow +=1

                subtotal_amount2 = total_amount + projects.supplies
                sheet.write(intRow,29,"Subtotal ")
                sheet.write_merge(intRow,intRow,31,33,subtotal_amount2,styleFooter)
                intRow +=1
                if projects.is_project_vatable == True:
                    vat = 0
                else:
                    vat = subtotal_amount2 * .012
                sheet.write_merge(intRow,intRow,29,30,"Add : 12% VAT ")
                sheet.write_merge(intRow,intRow,31,33,vat,styleFooter)
                intRow +=2
                grandtotal_amount = subtotal_amount2 + vat

                sheet.write_merge(intRow,intRow,29,30,"GRAND TOTAL ")
                sheet.write_merge(intRow,intRow,31,33,grandtotal_amount,styleFooter)
                intRow +=10
        else:
            #raise Warning(111)
            if len(self.customer_branches_id) > 0:
                model_cust_branches = self.env['res.customer.branches'].search([('customer_info','=', self.customer_branches_id.id),
                                                                                ('main_detail_id.customer_info','=', self.customer_id.id)])
            else:
                model_cust_branches = self.env['res.customer.branches'].search([('main_detail_id.customer_info','=', self.customer_id.id)])




            for branch in model_cust_branches:
                billing_details = self.env['billing.detail'].sorted(key = lambda r: r.employee_id.last_name)
                if len(self.job_id) > 0:
                    billing_detail = billing_details.search([('employee_id.job_id', '=', self.job_id.id),
                                                             ('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                             ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])

                else:
                    billing_detail = billing_details.search([('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                             ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])

            # Main Customer
            model_customers = self.env['res.customers.main'].search([('customer_info','=', self.customer_id.id)])

            #Per Branch
            if len(self.customer_branches_id) > 0:
                model_branch = model_customers.search([('main_cust_id.customer_info', '=', self.customer_branches_id.id)])
            else:
                model_branch = model_customers.search([])

            model_bran = model_branch.main_cust_id
            #Per Jobs
            lst_ids = []
            for customer in model_bran:
                lst_ids.append(customer.customer_info.id)

            if len(self.job_id) > 0:
                model_cust_project = self.env['res.customer.setup'].search([('job_id','=', self.job_id),
                                                                            ('customer_id.id', 'in', lst_ids)])
            else:
                model_cust_project = self.env['res.customer.setup'].search([('customer_id.id', 'in', lst_ids)])

            intRow = 1
            for projects in model_cust_project.sorted(key = lambda r: r.job_id.name):

                billing_details = self.env['billing.detail'].sorted(key = lambda r: r.employee_id.last_name)
                billing_detail = billing_details.search([('billing_main_id.job_id', '=', projects.job_id.id),
                                                         ('billing_main_id.customer_id', '=', projects.customer_id.id),
                                                         ('billing_main_id.attendance_id.month_of', '=', self.billing_month_of),
                                                         ('billing_main_id.attendance_id.month_quarter', '=', self.billing_month_quarter)])
                billing_main = self.env['billing.main'].search([('customer_id', '=',projects.customer_id.id),
                                                                ('attendance_id.month_of', '=',self.billing_month_of),
                                                                ('attendance_id.month_quarter', '=',self.billing_month_quarter),
                                                                ('job_id', '=', projects.job_id.id)])

                if len(billing_detail) > 0:
                    style0 = xlwt.easyxf('font: name Arial, color-index red, bold on')
                    sheet.write(intRow,1,"FR :",styleTitleFrom)

                    sheet.write(intRow,2,company.name,styleTitleFrom)
                    intRow+=1
                    sheet.write(intRow,1,"TO :",styleTitleTo)
                    sheet.write(intRow,2,billing_main.customer_id.name,styleTitleRe)
                    intRow+=1

                    sheet.write(intRow,1,"RE :",styleTitleRe)
                    sheet.write(intRow,2,"BILLING - " + str(billing_main.attendance_id.schedule_datefrom) + ' - ' \
                                + str(billing_main.attendance_id.schedule_dateto),styleTitleRe)
                    intRow +=1
                    sheet.write_merge(intRow,intRow,6,13,projects.job_id.name  ,style0)
                    intRow +=3
                    sheet.write_merge(intRow,intRow, 1,15, "DETAILS", styleColumns)
                    sheet.write_merge(intRow,intRow, 16,19, "AMOUNT", styleColumns)

                    intRow +=1
                    sheet.write_merge(intRow ,intRow  + 6, 1,4, "Name of Employee", styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5, 5,5, "Add'l/Less Days", styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,6,6,"Late/UT",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,7,7,"Straight Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,8,8,"Night Diff.",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,9,9,"OT - Regular",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,10,10,"OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,11,11,"Excess OT - Rest Day",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,12,12,"Special Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,13,13,"OT - Special Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,14,14,"Legal Holiday w/ Duty",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 5,15,15,"OT - Legal Holiday",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,16,16,"Contract Amount",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,17,17,"Add'l Less Days",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 4,18,18,"Late/UT",styleColumns)
                    sheet.write_merge(intRow ,intRow  + 6,19,19,"Total",styleColumns)

                    intRow +=6
                    sheet.write(intRow,5,"(days)",styleColumns)
                    sheet.write(intRow,6,"(mins)",styleColumns)
                    sheet.write(intRow,7,"(hrs)",styleColumns)
                    sheet.write(intRow,8,"(hrs)",styleColumns)
                    sheet.write(intRow,9,"(hrs)",styleColumns)
                    sheet.write(intRow,10,"(hrs)",styleColumns)
                    sheet.write(intRow,11,"(hrs)",styleColumns)
                    sheet.write(intRow,12,"(hrs)",styleColumns)
                    sheet.write(intRow,13,"(hrs)",styleColumns)
                    sheet.write(intRow,14,"(hrs)",styleColumns)
                    sheet.write(intRow,15,"(hrs)",styleColumns)
                    sheet.write(intRow,16,"(per mo.)",styleColumns)
                    sheet.write(intRow,17,"(per day)",styleColumns)
                    sheet.write(intRow,18,"(per min)",styleColumns)


                    #Amount Details Columns
                    model_workhourtype = self.env['hr.workhourtype']
                    model_client_billing_info = self.env['res.customer.setup'].search([('customer_id', '=', self.customer_id.id),
                                                                                 ('job_id', '=', self.job_id.id)
                                                                                 ])
                    daily_rate  = (model_client_billing_info.total_labor_cost * constants.MONTHS_IN_YEAR) / (constants.WEEKS_IN_YEAR * constants.WORK_IN_WEEK)
                    hourly_rate = daily_rate / constants.HOURS_PER_DAY

                    intRow -=1

                    sheet.write(intRow,16,model_client_billing_info.total_labor_cost/2, styleColumns)
                    sheet.write(intRow,17,daily_rate ,styleColumns)
                    sheet.write(intRow,18,hourly_rate/constants.MINUTES,styleColumns)
                    intRow +=2

                    sheet.write(intRow,1,"",styleLeft)

                    for i in range(5,20):
                        sheet.write(intRow,i,"",styleData)

                    intRow +=1
                    for employee in billing_detail:
                        fontData = xlwt.Font()
                        styleEmployeeName = xlwt.XFStyle()
                        #To Check if Employee has a reliever or not
                        if employee.has_a_reliever == True:
                            fontData.colour_index = 0x0A
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, employee.sequence, styleLeft)
                            sheet.write(intRow, 2, employee.parent_employee_id.name,styleEmployeeName)

                        elif employee.is_reliever == True:
                            fontData.colour_index = 0x0C
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, "", styleLeft)
                            sheet.write(intRow, 2, "**",styleEmployeeName)
                            sheet.write(intRow, 3, employee.employee_reliever_id.name,styleEmployeeName)
                        else:
                            fontData.colour_index = 0x08
                            styleData.font = fontData
                            styleLeft.font = fontData
                            styleEmployeeName.font =fontData
                            sheet.write(intRow, 1, employee.sequence, styleLeft)
                            sheet.write(intRow, 2, employee.employee_id.name,styleEmployeeName)

                        sheet.write(intRow,5,employee.details_less_day,styleData)
                        sheet.write(intRow,6,employee.details_tardiness_ut,styleData)
                        sheet.write(intRow,7,employee.details_straight_duty,styleData)
                        sheet.write(intRow,8,employee.details_night_diff,styleData)
                        sheet.write(intRow,9,employee.details_overtime_reqular,styleData)
                        sheet.write(intRow,10,employee.details_restday,styleData)
                        sheet.write(intRow,11,employee.details_overtime_restday,styleData)
                        sheet.write(intRow,12,employee.details_special_holiday,styleData)
                        sheet.write(intRow,13,employee.details_overtime_special_holiday,styleData)
                        sheet.write(intRow,14,employee.details_legal_holiday,styleData)
                        sheet.write(intRow,15,employee.details_overtime_legal_holiday,styleData)
                        sheet.write(intRow,16,employee.amount_contract,styleData)
                        sheet.write(intRow,17,employee.amount_less_day,styleData)
                        sheet.write(intRow,18,employee.amount_tardiness_ut,styleData)
                        sheet.write(intRow,19,employee.amount_total,styleData)
                        total_amount +=employee.amount_total
                        intRow +=1

                sheet.write(intRow,1,"",styleBottomLeft)
                sheet.write(intRow,2,"",styleBottom_in_name)
                sheet.write(intRow,3,"",styleBottom_in_name)
                sheet.write(intRow,4,"",styleBottom_in_name)

                for intRowBottom in range(5,20):
                    sheet.write(intRow,intRowBottom,"",styleBottom)
                intRow +=1

                #Footer and Data
                sheet.write(intRow,15,"Subtotal ")
                sheet.write_merge(intRow,intRow,17,19,total_amount,styleFooter)
                intRow +=1

                sheet.write_merge(intRow,intRow,15,16,"Add : Supplies ")
                sheet.write_merge(intRow,intRow,17,19,projects.supplies,styleFooter)
                intRow +=1

                subtotal_amount2 = total_amount + projects.supplies
                sheet.write(intRow,15,"Subtotal ")
                sheet.write_merge(intRow,intRow,17,19,subtotal_amount2,styleFooter)
                intRow +=1
                if projects.is_project_vatable == True:
                    vat = 0
                else:
                    vat = subtotal_amount2 * .012
                sheet.write_merge(intRow,intRow,15,16,"Add : 12% VAT ")
                sheet.write_merge(intRow,intRow,17,19,vat,styleFooter)
                intRow +=2
                grandtotal_amount = subtotal_amount2 + vat

                sheet.write_merge(intRow,intRow,15,16,"GRAND TOTAL ")
                sheet.write_merge(intRow,intRow,18,19,grandtotal_amount,styleFooter)
                intRow +=10
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data)
        self.billing_file = byte_arr
        return self.billing_file

class RelieverEmployee(models.TransientModel):
    _name = 'billing.reliever'
    _description = 'Wizard Form Reliever'
    report_format = fields.Selection(FORMAT_STR, 'Report Format')
    billing_detail_id = fields.Many2one('billing.detail', 'Billing Detail')
    employee =fields.Many2one('hr.employee', 'Absent Employee')
    name = fields.Many2one('hr.employee','Reliever')
    absent = fields.Integer('Days')


    @api.one
    def createReliever(self):
        payroll_detail = self.env['billing.detail']
        #raise Warning(self.billing_detail_id.id)

        payroll_detail.create({
            'billing_main_id': self.billing_detail_id.billing_main_id.id,
            'name': self.name.name,
            'sequence': 0 ,
            'employee_sequence': 0 ,
            'employee_id': self.employee.id,
            'is_reliever': True,
            'employee_reliever_id': self.name.id,
            'details_less_day': self.absent * -1,
            'record_status': 1
        })

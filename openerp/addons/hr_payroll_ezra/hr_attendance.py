# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from parameters import constants

import datetime
import xlwt
import xlrd
from xlutils.copy import copy
from xlutils.styles import Styles
from cStringIO import StringIO
import base64

import logging
_logger = logging.getLogger(__name__)

YEAR = 365
MONTH = 30

DATE_NOW = datetime.datetime.now()
MWE = constants.MINIMUM_WAGE_AMOUNT
EXEMPTION = constants.ComputeTaxExemption()


MONTH_SELECTION = [
    ('1', 'January'),
    ('2', 'February'),
    ('3', 'March'),
    ('4', 'April'),
    ('5', 'May'),
    ('6', 'June'),
    ('7', 'July'),
    ('8', 'August'),
    ('9', 'September'),
    ('10', 'October'),
    ('11', 'November'),
    ('12', 'December')]

MONTH_QUARTER_SELECTION = [
    (1, '1st Half'),
    (2, '2nd Half')
]

ATTENDANCE_RIGHTS_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Post to Payroll')
]


PAYROLL_STATE_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid to Employees')
]

MARITAL_STATUS = [
    'single',
    'married',
    'widower',
    'divorced'
]


SCHEDULE_PAY=[
    'quarterly',
    'monthly',
    'semi-annually'
    'weekly',
    'bi-weekly',
    'bi-monthly',
    'annually'
]

class payrollEmployeeMainAttendance(models.Model):
    _name = 'hr.attendance.main'
    _description = 'Attendance'
    _inherit = 'mail.thread'
    _order = 'write_date desc'

    @api.one
    def _getFilename(self):
        self.filename = '%s.xls' % self.name

    name = fields.Char('Cut-off Period', required = True)
    company_assign = fields.Many2one('res.customers.main', 'Company')
    assign_projects = fields.Many2one('res.partner', 'Per Project')
    schedule_datefrom = fields.Date('Date from', required=True)
    schedule_dateto = fields.Date('Date to', required=True)
    month_of = fields.Selection(constants.MONTH_SELECTION, 'for the Month of', reguired = True)
    month_quarter = fields.Selection(MONTH_QUARTER_SELECTION, required = True)
    attendance_status = fields.Selection(ATTENDANCE_RIGHTS_STATUS, required = True,
                                         help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Employee Attendance.\n"
                                                     " * The 'Approved' when the encoded Employee Attendance is been approved by the Timekeeper and ready to be computed for Payroll.\n"
                                                     " * The 'Post to Payroll' status is when the Employee Attendance is ready to used in Payroll Computation.\n",
                                         default = 'draft')
    employee_ids = fields.One2many('hr.payroll.attendance','employee_attendance_child_id', readonly=False,copy=False)

    filename = fields.Char('file name', readonly = True,store = False,compute ='_getFilename')
    attendance_file = fields.Binary('Excel File')



    def getUseridName(self):
        return self.env['res.users'].search([('id','=', self._uid)]).name

    @api.constrains('schedule_datefrom','schedule_dateto')
    def checkConstrainDate(self):
        if self.schedule_dateto < self.schedule_datefrom:
            raise ValidationError('Date to is less than the Date from.')

    #--- Overriding Methods

    @api.model
    def create(self, vals):

        for perSelf in self:
            #raise Warning(perSelf._description)
            perSelf.employee_ids.checkleaves()

        new_record = super(payrollEmployeeMainAttendance, self).create(vals)

        return new_record

    @api.multi
    def unlink(self):
        #raise Warning(self.employee_ids.search([('employee_attendance_child_id','=',self.id)]))
        for perSelf in self:
            print 'Start' + perSelf.name
            if perSelf.attendance_status == ATTENDANCE_RIGHTS_STATUS[1][0] or \
               perSelf.attendance_status == ATTENDANCE_RIGHTS_STATUS[2][0]:
                raise Warning("The attendance you've trying to delete is already Posted.")
            # Change the status and related field
            # before removing the Main Attendance Information

            employee_attendance = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',perSelf.id)])
            #Unlink all Relievers and Added Employee
            employee_attendance_reliever = employee_attendance .search(['|',('is_reliever', '=', True),
                                                                            ('is_additional_employee', '=', True)])


            employee_attendance.write({'employee_attendance_child_id': 0, 'attendance_status': 0})
            print 'End' + perSelf.name
        super(payrollEmployeeMainAttendance, self).unlink()
        return True


    @api.multi
    def write(self, vals):
        super(payrollEmployeeMainAttendance, self).write(vals)

        for perSelf in self:
            if self.attendance_status !='post':
                if not vals.has_key('attendance_status'):
                    perSelf.employee_ids.checkleaves()

            for employee in perSelf.employee_ids:
                if len(employee.parent_employee_id) == 0:

                    #Check if this employee has a reliever
                    int_total_reliever = self.env['hr.payroll.attendance'].search_count([('employee_attendance_child_id', '=',perSelf.id),
                                                                                         ('parent_employee_id', '=',employee.employee_id.id)])
                    if int_total_reliever  == 0:
                        model_attendance =self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=',perSelf.id),
                                                                                    ('employee_id', '=',employee.employee_id.id)])
                        model_attendance.write({'has_a_reliever':0})

        return True
    #--- End Overriding Methods

    @api.one
    def postapproved(self):
        # ('assign_projects','=', self.assign_projects.id), Change from Company Assign
        YEAR = datetime.datetime.strptime(self.schedule_dateto,'%Y-%m-%d').year
        payroll = self.env['hr.attendance.main'].search([('month_of','=', self.month_of),
                                                      ('month_quarter','=', self.month_quarter),
                                                      ('company_assign','=', self.company_assign.id),
                                                      ('attendance_status', '=','post')   ])

        for payroll_main in payroll:
            #if datetime.datetime.strptime(payroll_main.create_date[0:10],'%Y-%m-%d').year \
            if datetime.datetime.strptime(payroll_main.schedule_dateto,'%Y-%m-%d').year \
                    == YEAR:
                raise Warning('Attendance period for  %(month_of)s  of  %(month_quarter)s for project %(assign_projects)s\n' \
                              ' already been posted.'
                              %{'month_quarter':constants.MONTH_SELECTION[self.month_of-1][1],
                                'month_of': MONTH_QUARTER_SELECTION[self.month_quarter-1][1],
                                'company_assign': self.company_assign.name,})


        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance Approval',
                                     'Attendance Approval for ' + self.name,
                                     self._uid,
                                     'Attendance',
                                     self.name,
                                     'User Approve the Attendance',
                                     'Draft','Approve',
                                     self.id)

        self.attendance_status = ATTENDANCE_RIGHTS_STATUS[1][0]
        employee_attendance = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendance.write({'attendance_status': ATTENDANCE_RIGHTS_STATUS[1][0]})

        message ="""<span>Employee Attendance</span>
                    <div><b>Status</b>: Draft&rarr;Approved</div>
                    <div><b>Approved by</b>: %(user)s </div>
                    <div><b>Type</b>: Approved Employee Attendance</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

    @api.one
    def posttoPayroll(self):

        self.attendance_status = ATTENDANCE_RIGHTS_STATUS[2][0]
        employee_attendance = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendance.write({'attendance_status': ATTENDANCE_RIGHTS_STATUS[2][0]})

        #Updating the Leave
        if len(self.employee_ids) > 0:
            for employee in self.employee_ids:
                if employee.leaves > 0:
                    intRemainingLeaves = employee.employee_id.remaining_leave
                    intRemainingLeaves -= employee.leaves
                    employee.employee_id.write({'remaining_leave':intRemainingLeaves})

        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance Posting to Payroll',
                                     'Attendance Posting to Payroll for ' + self.name,
                                     self._uid,
                                     'Attendance',
                                     self.name,
                                     'User Recheck the Attendance',
                                     'Approve','Post',
                                     self.id)


        message ="""<span>Employee Attendance</span>
                    <div><b>Status</b>: Approved&rarr;Post</div>
                    <div><b>Confirm by</b>: %(user)s </div>
                    <div><b>Type</b>: Posting of Employee Attendance</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

    @api.one
    def reCheck(self):
        self.attendance_status = ATTENDANCE_RIGHTS_STATUS[0][0]
        employee_attendance = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendance.write({'attendance_status': ATTENDANCE_RIGHTS_STATUS[0][0]})

        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance Recheck',
                                     'Attendance Recheck for ' + self.name,
                                     self._uid,
                                     'Attendance',
                                     self.name,
                                     'User Recheck the Attendance',
                                     'Approve','Draft',
                                     self.id)

        message ="""<span>Employee Attendance</span>
                    <div><b>Status</b>: Approved&rarr;Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Re-Check of Employee Attendance</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)


    @api.one
    def backtoDraft(self):
        payroll_main = self.env['hr.payroll.main'].search([('payroll_attendance','=', self.id),
                                                           ('state','=', 'approved')])

        if len(payroll_main) > 0:
            raise Warning('Attendance already Posted in Payroll. Rollback first the Payroll\n'
                          'before Rolling back this attendance')

        self.attendance_status = ATTENDANCE_RIGHTS_STATUS[0][0]
        employee_attendance = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendance.write({'attendance_status': ATTENDANCE_RIGHTS_STATUS[0][0]})

        #Updating the Leave
        if len(self.employee_ids) > 0:
            for employee in self.employee_ids:
                if employee.leaves > 0:
                    intRemainingLeaves = employee.employee_id.remaining_leave
                    intRemainingLeaves += employee.leaves
                    employee.employee_id.write({'remaining_leave':intRemainingLeaves})

        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance Recheck',
                                     'Attendance Recheck for ' + self.name,
                                     self._uid,
                                     'Attendance',
                                     self.name,
                                     'User Recheck the Attendance',
                                     'Approve','Draft',
                                     self.id)

        message ="""<span>Employee Attendance</span>
                    <div><b>Status</b>: Post&rarr;Draft</div>
                    <div><b>Re-check by</b>: %(user)s </div>
                    <div><b>Type</b>: Re-Checking of Employee Attendance</div>
                    """ %{'user': self.getUseridName()}
        self.message_post(body=message)

        for employee in self.employee_ids:
            employee.computed_payroll = False

    @api.one
    def generateAttendance(self):

        #To Check if Attendance already Posted
        model_attendance_main = self.env['hr.attendance.main'].search([('company_assign','=', self.assign_projects.id),
                                                                       ('month_of','=', self.month_of),
                                                                       ('month_quarter','=', self.month_quarter),
                                                                       ('schedule_datefrom','=', self.schedule_datefrom),
                                                                       ('schedule_dateto','=', self.schedule_dateto),
                                                                       ('attendance_status','=','approved')])

        if len(model_attendance_main) > 0:
            raise Warning('Attendance already Approved.')

        model_attendance_main = self.env['hr.attendance.main'].search([('assign_projects','=', self.assign_projects.id),
                                                                       ('month_of','=', self.month_of),
                                                                       ('month_quarter','=', self.month_quarter),
                                                                       ('schedule_datefrom','=', self.schedule_datefrom),
                                                                       ('schedule_dateto','=', self.schedule_dateto),
                                                                       ('attendance_status','=','post')])

        if len(model_attendance_main) > 0:
            raise Warning('Attendance already Posted.')

        #Model
        model_holiday = self.env['hr.holiday']
        legal_holiday = model_holiday.checkHolidays_in_DateRange(self.schedule_datefrom, self.schedule_dateto)

        #Reset Employee Attendance Relationship
        employee_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendances.write({'employee_attendance_child_id': 0})

        # Check Validation if Qualification of Attendance has been made..
        # If Yes Raise Abomination.. :)) Joke!!! .. Raise an Error..
        if len(self.assign_projects) > 0:
            employees = self.env['hr.employee'].search([('active', '=', 1), ('assignto_branch_2.customer_info', '=', int(self.assign_projects[0]))])
        else:
            employees = self.env['hr.employee'].search([('active', '=', 1)])

        if len(employees) > 0:
            int_employee_sequence = 1
            employee_attendance = self.env['hr.payroll.attendance']
            for employee in employees:
                #To Check if Employee Already had a Summary of Attendance
                employee_att = employee_attendance.search([('employee_id', '=', employee.id), ('schedule_datefrom', '=', self.schedule_datefrom),
                                                           ('schedule_dateto', '=', self.schedule_dateto)])
                if len(employee_att) == 0:
                    if employee.date_hired <= self.schedule_dateto:
                        employee_attendance.create({
                            'name': 'Attendance for ' + self.name,
                            'employee_id': employee.id,
                            'employee_assign': employee.assignto.name,
                            'schedule_datefrom': self.schedule_datefrom,
                            'schedule_dateto': self.schedule_dateto,
                            'attendance_status': self.attendance_status,
                            'employee_attendance_child_id': self.id,
                            'employee_sequence': int_employee_sequence,
                            'assignto_region': employee.assignto_region.id,
                            'assignto_workingdays': employee.assignto_workingdays,
                            'assignto_branch_2': employee.assignto_branch_2.id,
                            'legal_holiday_day':legal_holiday})
                        int_employee_sequence +=1
                else:
                    employee_att.write({'employee_attendance_child_id': self.id,
                                        'attendance_status': self.attendance_status,
                                        'legal_holiday_day':legal_holiday})
            self.Regenerate_Sorting(self.id)
            self.generateExcelFile_New()

            model_audit = self.env['sys.genx.audit']
            model_audit.createAuditTrail('Attendance Generation',
                                         'Attendance Generation for ' + self.name,
                                         self._uid,
                                         'Attendance',
                                         self.name,
                                         'User Generate Attendance',
                                         'Approve','Draft',
                                         self.id)
        else:
            raise Warning('No Employee/s found.')


    @api.model
    def Regenerate_Sorting(self, attendance_main_id = 0):

        model_employee_attendance  = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=', attendance_main_id)])

        # Regenerate First all of the Employee that assigned/added by this cutoff in this branch
        int_sequence = 1
        if len(model_employee_attendance) > 0:
            sorted_model_employee_attendance = model_employee_attendance.sorted(key=lambda r: r.employee_id.name)
            for employee in sorted_model_employee_attendance:
                if employee.employee_id == False:
                    pass
                elif len(employee.employee_id) >0:
                    employee.write({'employee_sequence':int_sequence})
                int_sequence +=1
            #Designate all The Relievers in their new proper Sequence
            for employee in sorted_model_employee_attendance:
                if employee.is_reliever == True:
                    # Get the Sequence of the Main Employee
                    get_employee_sequence = model_employee_attendance.search([('employee_id', '=', employee.parent_employee_id.id),
                                                                              ('employee_attendance_child_id', '=', attendance_main_id)])
                    employee.write({'employee_sequence':get_employee_sequence.employee_sequence})


    @api.one
    def generateAttendance_per_Company(self):

        #To Check if Attendance already Posted
        model_attendance_main = self.env['hr.attendance.main'].search([('company_assign','=', self.company_assign.id),
                                                                       ('month_of','=', self.month_of),
                                                                       ('month_quarter','=', self.month_quarter),
                                                                       ('schedule_datefrom','=', self.schedule_datefrom),
                                                                       ('schedule_dateto','=', self.schedule_dateto),
                                                                       ('attendance_status','=','approved')])

        if len(model_attendance_main) > 0:
            raise Warning('Attendance already Approved.')

        model_attendance_main = self.env['hr.attendance.main'].search([('company_assign','=', self.company_assign.id),
                                                                       ('month_of','=', self.month_of),
                                                                       ('month_quarter','=', self.month_quarter),
                                                                       ('schedule_datefrom','=', self.schedule_datefrom),
                                                                       ('schedule_dateto','=', self.schedule_dateto),
                                                                       ('attendance_status','=','post')])

        if len(model_attendance_main) > 0:
            raise Warning('Attendance already Posted.')

        #Model
        model_holiday = self.env['hr.holiday']
        legal_holiday = model_holiday.checkHolidays_in_DateRange(self.schedule_datefrom, self.schedule_dateto)
        #raise Warning(legal_holiday)
        #Reset Employee Attendance Relationship
        employee_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        employee_attendances.write({'employee_attendance_child_id': 0})


        # Check Validation if Qualification of Attendance has been made..
        # If Yes Raise Abomination.. :)) Joke!!! .. Raise an Error..
        if len(self.company_assign) > 0:
            employees = self.env['hr.employee'].search([('active', '=', 1), ('assignto', '=', self.company_assign.id)])
        else:
            employees = self.env['hr.employee'].search([('active', '=', 1)])

        if len(employees) > 0:
            int_employee_sequence = 1
            employee_attendance = self.env['hr.payroll.attendance']
            for employee in employees:
                #To Check if Employee Already had a Summary of Attendance
                employee_att = employee_attendance.search([('employee_id', '=', employee.id), ('schedule_datefrom', '=', self.schedule_datefrom),
                                                           ('schedule_dateto', '=', self.schedule_dateto)])
                if len(employee_att) == 0:
                    if employee.date_hired <= self.schedule_dateto:
                        employee_attendance.create({
                            'name': 'Attendance for ' + self.name,
                            'employee_id': employee.id,
                            'employee_assign': employee.assignto.name,
                            'employee_branches': employee.assignto_branch_2.customer_info.id,
                            'company_assign': employee.assignto.id,
                            'schedule_datefrom': self.schedule_datefrom,
                            'schedule_dateto': self.schedule_dateto,
                            'attendance_status': self.attendance_status,
                            'employee_attendance_child_id': self.id,
                            'employee_sequence': int_employee_sequence,
                            'assignto_region': employee.assignto_region.id,
                            'assignto_workingdays': employee.assignto_workingdays,
                            'assignto_branch_2': employee.assignto_branch_2.id,
                            'legal_holiday_day':legal_holiday})
                        int_employee_sequence +=1
                else:
                    employee_att.write({'employee_attendance_child_id': self.id,
                                        'attendance_status': self.attendance_status,
                                        'legal_holiday_day':legal_holiday})
            self.generateExcelFile_New()
            model_audit = self.env['sys.genx.audit']
            model_audit.createAuditTrail('Attendance Generation',
                                         'Attendance Generation for ' + self.name,
                                         self._uid,
                                         'Attendance',
                                         self.name,
                                         'User Generate Attendance',
                                         'Approve','Draft',
                                         self.id)


        else:
            raise Warning('No Employee/s found.')

    @api.one
    def recompute(self):
        #Recheck Reliever and Absent
        attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=', self.id),
                                                                ('is_main_employee', '=', True)])
        #Checking of Employee that has been late tag in this project
        if len(attendances) > 0:
            employee_id = []
            for attendance_employee in attendances:
                employee_id.append(attendance_employee.employee_id.id)

            model_employee = self.env['hr.employee'].search([('active', '=', 1),
                                                             ('assignto', '=', self.company_assign.id),
                                                             ('id', 'not in',employee_id)])

            model_holiday = self.env['hr.holiday']
            legal_holiday = model_holiday.checkHolidays_in_DateRange(self.schedule_datefrom, self.schedule_dateto)

            if len(model_employee) > 0:
                int_employee_sequence = 1
                employee_attendance = self.env['hr.payroll.attendance']
                for employee in model_employee:
                    #To Check if Employee Already had a Summary of Attendance
                    employee_att = employee_attendance.search([('employee_id', '=', employee.id), ('schedule_datefrom', '=', self.schedule_datefrom),
                                                               ('schedule_dateto', '=', self.schedule_dateto)])
                    if len(employee_att) == 0:
                        if employee.date_hired <= self.schedule_dateto:
                            employee_attendance.create({
                                'name': 'Attendance for ' + self.name,
                                'employee_id': employee.id,
                                'employee_assign': employee.assignto.name,
                                'employee_branches': employee.assignto_branch_2.customer_info.id,
                                'company_assign': employee.assignto.id,
                                'schedule_datefrom': self.schedule_datefrom,
                                'schedule_dateto': self.schedule_dateto,
                                'attendance_status': self.attendance_status,
                                'employee_attendance_child_id': self.id,
                                'employee_sequence': int_employee_sequence,
                                'assignto_region': employee.assignto_region.id,
                                'assignto_workingdays': employee.assignto_workingdays,
                                'assignto_branch_2': employee.assignto_branch_2.id,
                                'legal_holiday_day':legal_holiday})
                            int_employee_sequence +=1
                    else:
                        employee_att.write({'employee_attendance_child_id': self.id,
                                            'attendance_status': self.attendance_status,
                                            'legal_holiday_day':legal_holiday})
        #END Checking of Employee that has been late tag in this project

        #Case Scenario when deleting the file/record an Error Occured
        #this is to fix it
        model_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=', self.id)])

        if len(model_attendances) > 0:
            for employee in self.employee_ids:
                if len(employee.parent_employee_id)  == 0:

                    #Check if this employee has a reliever
                    int_total_reliever = self.env['hr.payroll.attendance'].search_count([('employee_attendance_child_id', '=',self.id),
                                                                                         ('parent_employee_id', '=',employee.employee_id.id)])
                    if int_total_reliever == 0:
                        model_attendance =self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=',self.id),
                                                                                    ('employee_id', '=',employee.employee_id.id)])

                        model_attendance.write({'has_a_reliever':0})
            self.Regenerate_Sorting(self.id)
        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance Regenerate',
                                     'Attendance Regenerate for ' + self.name,
                                     self._uid,
                                     'Attendance',
                                     self.name,
                                     'User triggered Regenerate button',
                                     'Approve','Draft',
                                     self.id)


    def addEmployee(self, cr, uid, ids, context=None):
        context = {}
        #raise Warning(ids)
        #if context is None:  context = {}
        #if context.get('active_model') != self._name:
        #    context.update(active_ids=ids, active_model='hr.attendance.main')
        #    context.update(default_attendance_detail_id=ids)
        #employee = self.pool.get("hr.payroll.attendance").browse(cr,uid,ids,context=None)
        #raise Warning(ids[0])
        partial_id = self.pool.get("hr.attendance.employee.wiz").create(
            cr, uid, {'attendance_detail_id': ids[0]}, context=context)

        return {
            'name': "Add Employee",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.attendance.employee.wiz',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }

    @api.model
    def reloadForm(self):
        pass

    @api.one
    def generateExcelFile(self):
        str_dir = constants.GenXUtils.get_data_dir_excel_template
        model_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        model_attendance = model_attendances.sorted(key=lambda r: r.employee_id.last_name)
        workbook_xlrd = xlrd.open_workbook(str_dir + 'Attendance.xls', formatting_info=True)
        workbook = copy(workbook_xlrd)
        if len(model_attendance) > 0:
            styleColumns =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border

            sheet_xlrd = workbook_xlrd.sheet_by_index(0)
            sheet = workbook.get_sheet(0)
            int_rowindex = 8
            #Title
            sheet.write(1,3,self.assign_projects.name)
            sheet.write(2,3,str(self.schedule_datefrom) + ' - ' + str(self.schedule_dateto))

            for employee in model_attendance:
                sheet.write_merge(int_rowindex,int_rowindex,1,3,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)
                if isinstance(employee.employee_assign, bool):
                    employee_assign = ""
                else:
                    sheet.write(int_rowindex,4,employee.employee_assign,styleColumns)
                sheet.write(int_rowindex,5,employee.regular_days_work,styleColumns)
                sheet.write(int_rowindex,6,employee.regular_overtime,styleColumns )
                sheet.write(int_rowindex,7,employee.night_differential,styleColumns)
                sheet.write(int_rowindex,8,employee.absent,styleColumns)
                sheet.write(int_rowindex,9,employee.tardiness,styleColumns)
                sheet.write(int_rowindex,10,employee.undertime,styleColumns)
                sheet.write(int_rowindex,11,employee.leaves,styleColumns)
                sheet.write(int_rowindex,12,employee.rest_day_work,styleColumns)
                sheet.write(int_rowindex,13,employee.restday_overtime,styleColumns)
                sheet.write(int_rowindex,14,employee.holiday_day_work,styleColumns)
                sheet.write(int_rowindex,15,employee.holiday_overtime,styleColumns)
                sheet.write(int_rowindex,16,employee.special_day_work,styleColumns)
                sheet.write(int_rowindex,17,employee.special_overtime,styleColumns)
                sheet.write(int_rowindex,18,employee.straight_duty,styleColumns)
                int_rowindex +=1
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.attendance_file = byte_arr

    @api.one
    def generateExcelFile_New(self):
        str_dir = constants.GenXUtils.get_data_dir_excel_template
        model_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id','=',self.id)])
        #, r.employee_id.last_name
        model_attendance = model_attendances.sorted(key=lambda r: r.employee_sequence)
        workbook_xlrd = xlrd.open_workbook(str_dir + 'Attendance 2.xls', formatting_info=True)
        workbook = copy(workbook_xlrd)
        if len(model_attendance) > 0:
            styleColumns =xlwt.XFStyle()
            border = xlwt.Borders()
            border.bottom = xlwt.Borders.THIN
            border.top = xlwt.Borders.THIN
            border.left = xlwt.Borders.THIN
            border.right = xlwt.Borders.THIN
            styleColumns.borders = border

            sheet_xlrd = workbook_xlrd.sheet_by_index(0)
            sheet = workbook.get_sheet(0)
            int_rowindex = 6
            #Title
            sheet.write(1,2,self.company_assign.name)
            sheet.write(2,2,str(self.schedule_datefrom) + ' - ' + str(self.schedule_dateto))

            for employee in model_attendance:
                fontData = xlwt.Font()
                if employee.has_a_reliever == True:
                    fontData.colour_index = 0x0A
                    styleColumns.font =fontData
                    sheet.write_merge(int_rowindex,int_rowindex,0,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)
                elif employee.is_reliever == True:
                    fontData.colour_index = 0x0C
                    styleColumns.font =fontData
                    sheet.write_merge(int_rowindex,int_rowindex,0,2, '**' + employee.employee_reliever.last_name + ',' + employee.employee_reliever.first_name,styleColumns)
                else:
                    fontData.colour_index = 0x08
                    styleColumns.font =fontData
                    sheet.write_merge(int_rowindex,int_rowindex,0,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)

                sheet.write(int_rowindex,3,employee.regular_days_work,styleColumns)
                sheet.write(int_rowindex,4,employee.absent,styleColumns)
                sheet.write(int_rowindex,5,employee.tardiness,styleColumns)
                sheet.write(int_rowindex,6,employee.straight_duty,styleColumns)
                sheet.write(int_rowindex,7,employee.night_differential,styleColumns)
                sheet.write(int_rowindex,8,employee.regular_overtime,styleColumns )
                sheet.write(int_rowindex,9,employee.rest_day_work,styleColumns)
                sheet.write(int_rowindex,10,employee.restday_overtime,styleColumns)
                sheet.write(int_rowindex,11,employee.special_day_work,styleColumns)
                sheet.write(int_rowindex,12,employee.special_overtime,styleColumns)
                sheet.write(int_rowindex,13,employee.legal_holiday_day,styleColumns)
                sheet.write(int_rowindex,14,employee.holiday_day_work,styleColumns)
                sheet.write(int_rowindex,15,employee.holiday_overtime,styleColumns)


                int_rowindex +=1
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.attendance_file = byte_arr

    @api.one
    def generateExcelFile_perCompany(self):
        model_customer_branches = self.env['res.customer.branches'].search([('main_detail_id','=', self.company_assign.id)])

        model_customer_branch =  model_customer_branches.sorted(key=lambda r: r.name)
        str_dir = constants.GenXUtils.get_data_dir_excel_template
        int_rowindex = 6

        workbook_xlrd = xlrd.open_workbook(str_dir + 'Attendance 2.xls', formatting_info=True)

        workbook = copy(workbook_xlrd)

        sheet_xlrd = workbook_xlrd.sheet_by_index(0)
        sheet = workbook.get_sheet(0)

        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21,  196, 215, 155)
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_LEFT
        alignment.vert = xlwt.Alignment.VERT_CENTER
        alignment.Wrap = 1
        job_background_color = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour')
        job_background_color.alignment = alignment
        job_background_color.alignment.wrap = 1

        #border 1
        border = xlwt.Borders()
        border.bottom = xlwt.Borders.THIN
        border.top = xlwt.Borders.THIN
        border.left = xlwt.Borders.THIN
        border.right = xlwt.Borders.THIN
        job_background_color.borders = border
        job_background_color.font.bold =True

        for hr_attendance_detail_main in model_customer_branch:

            #Title
            sheet.write(1,2,self.company_assign.name)
            sheet.write(2,2,str(self.schedule_datefrom) + ' - ' + str(self.schedule_dateto))
            model_attendances = self.env['hr.payroll.attendance'].search([('employee_attendance_child_id', '=', self.id),
                                                                          ('employee_branches','=',hr_attendance_detail_main.customer_info.id)])
            model_attendance = model_attendances.sorted(key=lambda r: r.employee_sequence)
            #sheet.write_merge(int_rowindex,int_rowindex,0,15,'Branch : ' + hr_attendance_detail_main.name,job_background_color)
            #int_rowindex +=1
            if len(model_attendance) > 0:
                styleColumns =xlwt.XFStyle()
                border = xlwt.Borders()
                border.bottom = xlwt.Borders.THIN
                border.top = xlwt.Borders.THIN
                border.left = xlwt.Borders.THIN
                border.right = xlwt.Borders.THIN
                styleColumns.borders = border

                for employee in model_attendance:
                    fontData = xlwt.Font()
                    sheet.write(int_rowindex,0,employee.employee_branches.name,styleColumns)
                    if employee.has_a_reliever == True:
                        fontData.colour_index = 0x0A
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,1,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)
                    elif employee.is_reliever == True:
                        fontData.colour_index = 0x0C
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,1,2, '**' + employee.employee_reliever.last_name + ',' + employee.employee_reliever.first_name,styleColumns)
                    else:
                        fontData.colour_index = 0x08
                        styleColumns.font =fontData
                        sheet.write_merge(int_rowindex,int_rowindex,1,2,employee.employee_id.last_name + ',' + employee.employee_id.first_name,styleColumns)

                    sheet.write(int_rowindex,3,employee.regular_days_work,styleColumns)
                    sheet.write(int_rowindex,4,employee.absent,styleColumns)
                    sheet.write(int_rowindex,5,employee.tardiness,styleColumns)
                    sheet.write(int_rowindex,6,employee.straight_duty,styleColumns)
                    sheet.write(int_rowindex,7,employee.night_differential,styleColumns)
                    sheet.write(int_rowindex,8,employee.regular_overtime,styleColumns )
                    sheet.write(int_rowindex,9,employee.rest_day_work,styleColumns)
                    sheet.write(int_rowindex,10,employee.restday_overtime,styleColumns)
                    sheet.write(int_rowindex,11,employee.special_day_work,styleColumns)
                    sheet.write(int_rowindex,12,employee.special_overtime,styleColumns)
                    sheet.write(int_rowindex,13,employee.legal_holiday_day,styleColumns)
                    sheet.write(int_rowindex,14,employee.holiday_day_work,styleColumns)
                    sheet.write(int_rowindex,15,employee.holiday_overtime,styleColumns)
                    int_rowindex +=1
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        data_read = fp.read()
        fp.close()
        byte_arr = base64.b64encode(data_read)
        self.attendance_file = byte_arr


class payrollEmployeeAttendance(models.Model):
    _name = 'hr.payroll.attendance'
    _description = 'Payroll.Attendance.Per.Employee'
    _order ='employee_sequence,create_date'

    @api.model
    def reloadForm(self):
        res = {
                'type': 'ir.actions.client',
                'tag': 'reload'}
        return res

    def getValueID(self, cr, uid, ids, context=None):
        context = {}
        if context is None:  context = {}
        if context.get('active_model') != self._name:
            context.update(active_ids=ids, active_model='hr.attendance.main') #self._name
            context.update(default_attendance_detail_id=ids)
        employee = self.pool.get("hr.payroll.attendance").browse(cr,uid,ids,context=None)
        partial_id = self.pool.get("hr.attendance.detail.wiz").create(
            cr, uid, {'attendance_detail_id': ids[0], 'employee': employee.employee_id.id}, context=context)


        return {
            'name': "Employee Reliever",
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.attendance.detail.wiz',
            'res_id': partial_id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]',
            'context': context
        }

    @api.one
    def checkEmployeeHierarchy(self):
        total_employee_parent_count = self.env['hr.payroll.attendance'].search_count([('parent_employee_id', '=', self.parent_employee_id)])

        if total_employee_parent_count > 0:
            if self.parent_employee_id == self.employee_id:
                return True
        return False

    name = fields.Char('Name')
    employee_attendance_child_id = fields.Many2one('hr.attendance.main')

    employee_sequence = fields.Integer('Sequence', help ="Employee Sequence")
    employee_id = fields.Many2one('hr.employee', 'Employee', help ="Employee")
    employee_reliever = fields.Many2one('hr.employee', 'Reliever')
    employee_assign = fields.Char(related = 'employee_id.assignto.name', store=True)

    employee_branches = fields.Many2one('res.partner', 'Per Project')
    company_assign = fields.Many2one('res.customer.main', 'Company')

    regular_days_work = fields.Float('Regular Day/s Work (days)', default=0)
    rest_day_work = fields.Float('Rest Day/s Work (hrs)',default=0)
    legal_holiday_day = fields.Float('Legal Holiday (days)',default=0)
    holiday_day_work = fields.Float('Legal Holiday w/ Duty (hrs)', default=0)
    special_day_work = fields.Float('Special Holiday w/ Duty (hrs)', default=0)
    straight_duty = fields.Float('Straight Duty (hrs)', default=0)
    night_differential = fields.Float('Night Diff. (hrs)', default=0)
    regular_overtime = fields.Float('Regular Overtime. (hrs)', default=0)
    restday_overtime = fields.Float('Rest Day Overtime. (hrs)', default=0)
    special_overtime = fields.Float('Special Holiday Overtime. (hrs)', default=0)
    holiday_overtime = fields.Float('Legal Holiday Overtime. (hrs)', default=0)
    absent = fields.Float('Absent (days)', default=0)
    tardiness = fields.Float('Late/UT (minute)', default=0)
    undertime = fields.Float('Undertime (minute)', default=0) # Obselete Tardiness and Undertime is the same
    leaves = fields.Integer('Leaves (days)', default=0)
    schedule_datefrom = fields.Date('Date from', required=True)
    schedule_dateto = fields.Date('Date to', required=True)
    attendance_status = fields.Selection(ATTENDANCE_RIGHTS_STATUS, 'Status', default='draft')
    is_reliever = fields.Boolean('Reliever?', default =False)
    has_a_reliever = fields.Boolean('Has a reliever',  default =False)

    #for Reliever information
    parent_employee_id = fields.Many2one('hr.employee', 'Parent Employee')
    is_main_employee = fields.Boolean('Main Employee', compute="checkEmployeeHierarchy")

    #for Addtional Employee information
    is_additional_employee = fields.Boolean('Added Employee')

    # For Other Information
    computed_payroll = fields.Boolean('Is Payroll Computed', default=False)

    assignto_region = fields.Many2one('hr.regions','Region',required =True)
    assignto_workingdays = fields.Selection(constants.WORKING_DAYS, 'Working Days', required =True)
    assignto_branch = fields.Char('Branch', required = True,default = ' ')
    assignto_branch_2 = fields.Many2one('res.customer.branches','Branch', required =True)

    @api.one
    def checkleaves(self):
        #Check leaves for Selected Employees
        if len(self.employee_id) > 0:

            model_employee = self.env['hr.employee'].search([('id', '=', self.employee_id.id), '|',
                                                             ('active', '=',1),
                                                             ('active', '=',0)])
            #int_leaves = self.leaves
            #self.leaves = 0
            if model_employee.remaining_leave == 0 and self.leaves > 0:
                raise Warning(self.employee_id.name + ' has no remaining leave/s.')
            elif model_employee.remaining_leave > 0:
                if self.leaves > model_employee.remaining_leave:
                    raise Warning('Input leave/s for ' + self.employee_id.name + ' is greater than its given remaining leave/s.')
            #self.leaves = int_leaves


    @api.model
    def checkLeaves(self):

        #Check leaves for Selected Employees
        for employee in self:
            if len(employee.employee_id) > 0:
                model_employee = self.env['hr.employee'].search([('id', '=', employee.employee_id.id)])
                if model_employee.remaining_leave == 0 and self.leaves > 0:
                    raise Warning(employee.employee_id.name + ' has no remaining leave/s.')
                elif model_employee.remaining_leave > 0:
                    if employee.leaves > model_employee.remaining_leave:
                        raise Warning('Input leave/s for ' + employee.employee_id.name + ' is greater than its given remaining leave/s.')

     #--- Overriding Methods
    @api.multi
    def unlink(self):
        for perSelf in self:
            if perSelf.attendance_status == ATTENDANCE_RIGHTS_STATUS[1][0] or \
               perSelf.attendance_status == ATTENDANCE_RIGHTS_STATUS[2][0]:
                if isinstance(perSelf.name, object):
                    stname = ''
                else:
                    stname = perSelf.name

                raise Warning("The " + stname + " you've trying to delete is already Posted.")
        super(payrollEmployeeAttendance, self).unlink()
        return True

    @api.onchange('employee_id')
    def getEmployeeAssignment(self):
        if len(self.employee_id) > 0:
            self.employee_assign = self.employee_id.assignto.name
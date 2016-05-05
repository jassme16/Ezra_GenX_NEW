from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
#from parameters import constants as genx

class attendanceAdditionalEmployee(models.TransientModel):
    _name = 'hr.attendance.employee.wiz'
    _description = 'Wizard Form of Added for the Additional Employee'

    attendance_detail_id = fields.Many2one('hr.attendance.main', 'Attendance')
    name = fields.Many2one('hr.employee','Employee')
    #employee = fields.Many2one('hr.employee', 'Absent Employee')
    regular_days_work = fields.Float('Regular Day/s Work (days)', default=0)
    tardiness = fields.Float('Late/UT (minute)', default=0)
    absent = fields.Integer('Day/s Absent')
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

    @api.one
    def AddEmployee(self):
        attendance_detail = self.env['hr.payroll.attendance']

        # Check if selected Employee is already added as reliever to this absent employee
        attendance = attendance_detail.search([('employee_attendance_child_id','=', self.attendance_detail_id.id)])
        #raise Warning(attendance)
        if len(attendance) > 0:
            for employee in attendance:
                if employee.employee_id == self.name:
                    raise Warning('Reliever %(employee)s has already\n exists in Attendance.' %{'employee':self.name.name.title()})

        #attendance_detail = self.env['hr.payroll.attendance'].search([('parent_employee_id', '=', self.employee.id),
        #                                                              ('employee_attendance_child_id','=', self.attendance_detail_id.employee_attendance_child_id.id)])

        if self.name.assignto_region.id == False:
            raise Warning('Reliever has no region define in employee information.')
        if self.name.assignto_workingdays == False:
            raise Warning('Reliever has no working days define in employee information.')
        if self.name.assignto_branch_2.id == False:
            raise Warning('Reliever has no branch define in employee information.')

        #Model
        #model_holiday = self.env['hr.holiday']
        legal_holiday = 0 #model_holiday.checkHolidays_in_DateRange(self.attendance_detail_id.schedule_datefrom, self.attendance_detail_id.schedule_dateto)
        int_employee_sequence =0
        #Creation of Reliever
        attendance_detail.create({
            'name': 'Attendance for ' + self.name.name,
            'employee_id': self.name.id,
            'employee_assign': self.name.assignto.name,
            'schedule_datefrom': self.attendance_detail_id.schedule_datefrom,
            'schedule_dateto': self.attendance_detail_id.schedule_dateto,
            'attendance_status': self.attendance_detail_id.attendance_status,
            'employee_attendance_child_id': self.attendance_detail_id.id,
            'employee_sequence': int_employee_sequence,
            'assignto_region': self.name.assignto_region.id,
            'assignto_workingdays': self.name.assignto_workingdays,
            'assignto_branch_2': self.name.assignto_branch_2.id,

            'regular_days_work' : self.regular_days_work,
            'absent': self.absent,
            'tardiness': self.tardiness,
            'regular_overtime': self.regular_overtime,
            'rest_day_work': self.rest_day_work,
            'restday_overtime': self.restday_overtime,
            'holiday_day_work': self.holiday_day_work,
            'holiday_overtime': self.holiday_overtime,
            'special_day_work': self.special_day_work,
            'special_overtime': self.special_overtime,
            'straight_duty': self.straight_duty,
            'night_differential': self.night_differential,

            'legal_holiday_day':legal_holiday,
            'is_additional_employee': True,})
        int_employee_sequence +=1
        self.attendance_detail_id.Regenerate_Sorting(self.attendance_detail_id.id)
        #attendance_detail.()
        model_audit = self.env['sys.genx.audit']
        model_audit.createAuditTrail('Attendance adding of Employee from Other Project',
                                     'Attendance Additional Employee for ' + self.attendance_detail_id.name +
                                     ' Employee ' + self.name.name,
                                     self._uid,
                                     'Attendance',
                                     self.attendance_detail_id.name,
                                     'User triggered additional employee',
                                     '','',
                                     self.id)
        return {'type': 'ir_actions_act_close_wizard_and_reload_view'}



class attendanceReliever(models.TransientModel):
    _name = 'hr.attendance.detail.wiz'
    _description = 'Wizard Form of Attendance Reliever'
    billing_detail_id = fields.Many2one('billing.detail', 'Billing Detail')

    attendance_detail_id = fields.Many2one('hr.payroll.attendance', 'Attendance')

    employee = fields.Many2one('hr.employee', 'Absent Employee')
    name = fields.Many2one('hr.employee','Reliever')
    absent = fields.Integer('Day/s worked as a Reliever')
    regular_days_work = fields.Float('Regular Day/s Work (days)', default=0)
    tardiness = fields.Float('Late/UT (minute)', default=0)
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

    @api.one
    def createReliever(self):
        if self.name == False:
            raise Warning('No Reliever define.')
        if len(self.name) == 0:
           raise Warning('No Reliever define.')
        if self.employee == self.name:
            raise Warning('Absent employee and Reliever employee is the same.')

        #if self.absent == 0:
        #    raise Warning('No Day/s worked as a Reliever define.')
        #elif self.absent < 0:
        #    raise Warning('Day/s worked as a Reliever is less than zero.')

        if self.attendance_detail_id.absent == 0:
            raise Warning('Employee %(employee)s has no absences.' %{'employee':self.employee.name.title()})

        attendance_detail = self.env['hr.payroll.attendance']

        # Check if selected Employee is already added as reliever to this absent employee
        attendance = attendance_detail.search([('parent_employee_id', '=', self.employee.id),
                                               ('employee_reliever', '=', self.name.id),
                                               ('employee_attendance_child_id','=', self.attendance_detail_id.employee_attendance_child_id.id)])
        #raise Warning(attendance)
        if len(attendance) > 0:
           raise Warning('Reliever %(employee)s has already\n added to this Employee.' %{'employee':self.name.name.title()})
        #Check if
        attendance_detail = self.env['hr.payroll.attendance'].search([('parent_employee_id', '=', self.employee.id),
                                                                      ('employee_attendance_child_id','=', self.attendance_detail_id.employee_attendance_child_id.id)])
        attendance_detail_employee = self.env['hr.payroll.attendance'].search([('employee_id', '=', self.employee.id),
                                                                      ('employee_attendance_child_id','=', self.attendance_detail_id.employee_attendance_child_id.id)])
        absent  =0
        for attendance in attendance_detail:
            absent  += attendance.absent
        absent += self.absent
        if absent > attendance_detail_employee.absent:
           raise Warning('No. of Absent define has exceeded the no. of absent of the Employee %(employee)s.' %{'employee':self.employee.name.title()})



        if self.name.assignto_region.id == False:
            raise Warning('Reliever has no region define in employee information.')
        if self.name.assignto_workingdays == False:
            raise Warning('Reliever has no working days define in employee information.')
        if self.name.assignto_branch_2.id == False:
            raise Warning('Reliever has no branch define in employee information.')

        attendance_detail.create({
            'name': self.attendance_detail_id.name,
            'employee_attendance_child_id': self.attendance_detail_id.employee_attendance_child_id.id,
            'employee_reliever': self.name.id,
            'is_reliever': True,
            'parent_employee_id': self.employee.id,
            'regular_days_work' : self.regular_days_work,
            'absent': 0, #self.absent
            'tardiness': self.tardiness,
            'regular_overtime': self.regular_overtime,
            'rest_day_work': self.rest_day_work,
            'restday_overtime': self.restday_overtime,
            'holiday_day_work': self.holiday_day_work,
            'holiday_overtime': self.holiday_overtime,
            'special_day_work': self.special_day_work,
            'special_overtime': self.special_overtime,
            'straight_duty': self.straight_duty,
            'night_differential': self.night_differential,
            'schedule_datefrom': self.attendance_detail_id.schedule_datefrom,
            'schedule_dateto': self.attendance_detail_id.schedule_dateto,
            'attendance_status': self.attendance_detail_id.attendance_status,
            'employee_sequence': self.attendance_detail_id.employee_sequence,
            'assignto_region': self.name.assignto_region.id,
            'assignto_workingdays': self.name.assignto_workingdays,
            'assignto_branch_2': self.name.assignto_branch_2.id,
            'employee_branches': self.attendance_detail_id.employee_branches.id,
            'company_assign':self.attendance_detail_id.company_assign.id
        })

        #Updating the Absent Employee
        attendance_detail = self.env['hr.payroll.attendance'].search([('id', '=', self.attendance_detail_id.id)])
        attendance_detail.write({
            'has_a_reliever': True,
            'is_reliever': False,
            'is_main_employee' : True
        })
        model_attendance_form = self.env['hr.attendance.main']
        model_attendance_form.reloadForm()
        pass
        #res = {
        #        'type': 'ir.actions.client',
        #        'tag': 'reload'}
        #return res
        return {'type': 'ir_actions_act_close_wizard_and_reload_view'}


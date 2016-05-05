from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from openerp.addons.hr_payroll_ezra.parameters import constants

import datetime
import xlwt
import xlrd
from xlutils.copy import copy
from xlutils.styles import Styles
from cStringIO import StringIO
import base64


YEAR = 365
MONTH = 30

DATE_NOW = datetime.datetime.now()
MWE = constants.MINIMUM_WAGE_AMOUNT
EXEMPTION = constants.ComputeTaxExemption()

REPORT_TYPE = [
    (1, 'Incentive and Deductions'),
    (2, 'Incentive'),
    (3, 'Deductions')
]

PAYROLL_STATE_STATUS = [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid to Employees')
]



class IncentiveDeductionReportSummaryMain(models.Model):
    _name = 'hr.payroll.incen_deduc.report'
    _description = 'Incentive/Deduction Report'

    name = fields.Char('Report Name')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    payroll_releasedate_from = fields.Date('Date from',default = constants.DATE_NOW, required=True)
    payroll_releasedate_to = fields.Date('Date to',default = constants.DATE_NOW, required=True)
    report_type = fields.Selection(REPORT_TYPE, 'Report Type')
    payroll_status = fields.Selection(PAYROLL_STATE_STATUS, 'Status', default = 'post', required=True)

    payroll_incent_deduc_id = fields.One2many('hr.payroll.incen_deduc.report.detail','payroll_incen_deduc_id', readonly=False,copy=False)

    @api.one
    def generateReport(self):
        if len(self.employee_id) > 0:
            self.name = 'Report for Incentive/deduction ' + self.employee_id.name + ' ' + str(self.payroll_releasedate_to) + ' - ' + str(self.payroll_releasedate_from)
        else:
            self.name = 'Report for Incentive/deduction ' + str(self.payroll_releasedate_to) + ' - ' + str(self.payroll_releasedate_from)
        #Get first the Incentive in Payroll Detail
        model_incent_ded_report = self.env['hr.payroll.incen_deduc.report.detail'].search([('payroll_incen_deduc_id','=', self.id)])
        model_incent_ded_report.unlink()

        model_payroll_main = self.env['hr.payroll.main'].search([('payroll_releasedate','>=',self.payroll_releasedate_from),
                                                                 ('payroll_releasedate','<=',self.payroll_releasedate_to),
                                                                 ('state', '=', self.payroll_status)])
        for payroll_main in model_payroll_main:
            dict_filter = []
            if len(self.employee_id) > 0:
                dict_filter.append(('employee_id', '=', self.employee_id.id))
            dict_filter.append(('payroll_detail_id', '=', payroll_main.id))
            dict_filter.append(('is_reliever', '=', False))
            #raise Warning(dict_filter)
            model_payroll_detail = self.env['hr.payroll.detail'].search(dict_filter)
            model_incent_ded_detail_report = self.env['hr.payroll.incen_deduc.report.detail']
            for payroll_detail in model_payroll_detail:
                model_incent_ded_detail_report.create({
                    'payroll_incen_deduc_id': self.id,
                    'payroll_detail_id': payroll_detail.id})





class IncentiveDeductionReportSummaryDetail(models.Model):
    _name = 'hr.payroll.incen_deduc.report.detail'
    _description = 'Incentive/Deduction Detail Report'


    payroll_detail_id = fields.Many2one('hr.payroll.detail')
    payroll_incen_deduc_id = fields.Many2one('hr.payroll.incen_deduc.report', ondelete = 'cascade')

    employee_id = fields.Many2one('hr.employee', 'Employee')
    name = fields.Char('Name')
    is_incentive = fields.Boolean('Incentive')
    amount = fields.Float('Amount', digits=(18,2), default = 0)

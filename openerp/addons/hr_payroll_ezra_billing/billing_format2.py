# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.addons.hr_payroll_ezra.parameters import constants
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from cStringIO import StringIO
import xlwt
import xlrd
#import openpyxl
import base64

RECORD_STAT = [(1, 'NEW'),
               (2, 'CREATED'),
               (3, 'EDITED')]

FORMAT_STR = [(1, 'Format Report 1'),
              (2, 'Format Report 2')]


BILING_INFO_TYPE = [(1, 'Amount'),
                    (2, 'Percentage(%)')]


class customerProjectParameter(models.Model):

    _name = 'billing.parameter'
    _order = 'name'
    name = fields.Char('Parameter Name', required=True, size=50)
    parameter_type = fields.Selection('Type',BILING_INFO_TYPE, required=True, default=1)
    rate_or_amount = fields.Float('Rate/Amount', required=True, default=0, digits=(18, 2))


class customerBilling(models.Model):

    _name = 'billing.maininfo'
    _order = 'name'
    name = fields.Char('Billing Name', required=True)
    customer_id = fields.Many2one('res.partner', 'Customer', required=True)
    job_id = fields.Many2one('hr.job', 'Job Title', required=True)


    #name = fields.Many2one('hr.employee', 'Employee')
    #name_reliever = fields.Many2one('hr.employee', 'Employee')
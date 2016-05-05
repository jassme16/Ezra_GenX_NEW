# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError

import datetime

MONTHS_IN_YEAR = 12
WORK_HOURS = 8

class hr_contract(models.Model):
    _name = 'hr.contract'
    _inherit = 'hr.contract'

    regions = fields.Many2one('hr.regions.salary','Regions and Provinces')

    daily_rate = fields.Float('Daily Rate', digits=(16,2), required=True,default =0, help="Daily Rate of the employee")
    hourly_rate = fields.Float('Hourly Rate', digits=(16,2), required=True,default =0, help="Hourly Rate of the employee")
    weeks_in_years = fields.Integer('Weeks in a Year', required = True, default = 52, help="Total number of weeks in a year")
    workdays_in_weeks = fields.Integer('Working days in a week', required = True, default = 6, help="Total works days in a week")
    amount_allowance = fields.Float('Daily Allowance', digits=(18,2),required=True,default =0)
    cola_amount = fields.Float('COLA', digits=(18,2),required=True,default =0)

    @api.onchange('regions')
    def changeRegions(self):
        if not isinstance(self.regions, bool):
            self.daily_rate = self.regions.daily_rate_amount
            self.cola_amount = self.regions.cola_amount

    @api.one
    @api.onchange('wage')
    def recomputeRate(self):
        self.daily_rate = (self.wage * MONTHS_IN_YEAR) / (self.weeks_in_years * self.workdays_in_weeks)
        self.hourly_rate = self.daily_rate / WORK_HOURS

    @api.one
    @api.onchange('weeks_in_years')
    def recomputeRate1(self):
        self.daily_rate = (self.wage * MONTHS_IN_YEAR) / (self.weeks_in_years * self.workdays_in_weeks)
        self.hourly_rate = self.daily_rate / WORK_HOURS

    @api.one
    @api.onchange('workdays_in_weeks')
    def recomputeRate2(self):
        self.daily_rate = (self.wage * MONTHS_IN_YEAR) / (self.weeks_in_years * self.workdays_in_weeks)
        self.hourly_rate = self.daily_rate / WORK_HOURS

    @api.one
    @api.onchange('daily_rate')
    def recomputeRate3(self):
        self.wage = (self.daily_rate * (self.weeks_in_years * self.workdays_in_weeks)) / MONTHS_IN_YEAR
        self.hourly_rate = self.daily_rate / WORK_HOURS

    #@api.constrains('date_start','date_end')
    #def checkConstrainDate(self):
    #    if self.date_end < self.date_start:
    #        raise ValidationError('Date end is less than the Date start.')
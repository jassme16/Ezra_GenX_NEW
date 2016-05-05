# -*- encoding: utf-8 -*-
from openerp import models, fields, api
import datetime
# Main Models
DATE_NOW = datetime.datetime.now()


class ExtendHrApplicants(models.Model):
    _name = "hr.applicant"
    _inherit = ["hr.applicant"]

    def getApID(self):
        self.app_prim_id = self.id

    #@api.multi
    #@api.model
    #@api.onchange('applicants_Experience')
    def computeExperience(self):

        totalyears = 0
        #getExperiences = self.env['hr.applicants.experience'].search([('applicants_id', '=', self.app_prim_id)])
        getExperiences = self.applicants_Experience
        for getExperience in getExperiences:
            totalyears = totalyears + getExperience.years_of_exp


        #raise Warning(self.applicants_Experience)
        self.applicant_totalExperience = totalyears

    gender =  fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('widower', 'Widower'), ('divorced', 'Divorced')], 'Gender')
    applicants_address = fields.Text('Address')
    date_applied = fields.Date('Date Applied/Date Processed')
    applicants_Experience = fields.One2many('hr.applicants.experience', 'applicants_id', readonly=False,copy=False)
    applicant_totalExperience = fields.Float('Total Years of Experience', (18, 2), compute = computeExperience )
    app_prim_id  =fields.Integer('IDS', compute = getApID)

    #@api.multi
    #@api.model
    @api.onchange('applicants_Experience')
    def computeExperience(self):

        totalyears = 0
        #getExperiences = self.env['hr.applicants.experience'].search([('applicants_id', '=', self.app_prim_id)])
        getExperiences = self.applicants_Experience
        for getExperience in getExperiences:
            totalyears = totalyears + getExperience.years_of_exp
        self.applicant_totalExperience = totalyears


    # Overrides
    @api.multi
    def write(self, vals):
        super(ExtendHrApplicants, self).write(vals)
        return True
    # End Override Functions


class ApplicantsExperiences(models.Model):
    _name = 'hr.applicants.experience'

    applicants_id = fields.Many2one('hr.applicant')
    experiences_type = fields.Many2one('hr.applicants.experience.type', 'Experience Type')
    company_name = fields.Text('Company')
    date_from = fields.Date('Date from', default = DATE_NOW)
    date_to = fields.Date('Date to', default = DATE_NOW)
    years_of_exp = fields.Float('Years of Experience', (18, 2))


    #@api.onchange('date_from')
    def changeDateFrom(self):
        no_of_days = 0
        if isinstance(self.date_from, bool):
            if (self.date_from != False) and (self.date_to != False):
                date_from = datetime.datetime.strptime(self.date_from ,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to ,"%Y-%m-%d")
                no_of_days = abs((date_to - date_from).days)
            self.years_of_exp = no_of_days/365.2425
        elif isinstance(self.date_from, basestring):
            if (len(self.date_from)> 0) and (len(self.date_to)> 0):
                date_from = datetime.datetime.strptime(self.date_from ,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to ,"%Y-%m-%d")
                no_of_days = abs((date_to - date_from).days)
            self.years_of_exp = no_of_days/365.2425

    #@api.onchange('date_to')
    def changeDateTo(self):
        no_of_days = 0
        if isinstance(self.date_to, bool):
            if (self.date_from != False) and (self.date_to != False):
                date_from = datetime.datetime.strptime(self.date_from ,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to ,"%Y-%m-%d")
                no_of_days = abs((date_to - date_from).days)
            self.years_of_exp = no_of_days/365.2425
        elif isinstance(self.date_to, basestring):
            if (len(self.date_from)> 0) and (len(self.date_to)> 0):
                date_from = datetime.datetime.strptime(self.date_from ,"%Y-%m-%d")
                date_to = datetime.datetime.strptime(self.date_to ,"%Y-%m-%d")
                no_of_days = abs((date_to - date_from).days)
            self.years_of_exp = no_of_days/365.2425

# Param Models


class ExperienceType(models.Model):
    _name = 'hr.applicants.experience.type'

    code = fields.Char('Code')
    name = fields.Char('Experience Type')

    _sql_constraints = [
        ('hr_applicants_exp_type_uniq',
        'UNIQUE (code)',
        'Code must be unique!')]

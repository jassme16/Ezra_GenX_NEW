# -*- encoding: utf-8 -*-
from openerp import models, fields, api
#from openerp.osv import fields, osv
#from openerp.tools.translate import _

class ExtendHrApplicant(models.Model):
    _name = 'hr.applicant'
    _inherit = ['hr.applicant']

    first_name = fields.Char('First name')
    last_name = fields.Char('Last name')
    middle_name = fields.Char('Middle name')

    @api.onchange('first_name','middle_name','last_name')
    def getFullname(self):
        if self.first_name == False:
            self.first_name=''
        if self.middle_name == False:
            self.middle_name=''
        if self.last_name == False:
            self.last_name=''
        self.partner_name = self.first_name + " " + self.middle_name + " " + self.last_name


    # Overriding the create_employee_from_applicant from hr.applicants object
    @api.one
    def create_employee_from_applicant(self):
        cr = self._cr
        uid = self._uid
        ids = self.ids
        context = self._context

        super(ExtendHrApplicant, self).create_employee_from_applicant()
        hr_employee = self.env['hr.employee'].search([('id', '=', int(self.emp_id[0]))])
        hr_employee.write({
                            'first_name': self.first_name,
                            'middle_name': self.middle_name,
                            'last_name': self.last_name,
                            })


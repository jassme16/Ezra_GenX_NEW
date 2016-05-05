from openerp import models,fields, api

class BankAccountNumber(models.Model):
    _name = 'migrate.employee.acctnumber'
    _description = 'Migration for Employee Account Number'

    name = fields.Char('Employee Name')
    employee_id = fields.Many2one('Employee ID')
    employee_account_number = fields.Char('Account Number')


    @api.one
    def Generate(self):
        model_migration = self.env['migrate.employee.acctnumber'].search([])

        if len(model_migration) > 0:
            #Add first the Account Number in res.partner.bank
            for migrate in model_migration:
                if len(migrate.employee_account_number) > 0:
                    #Check first if Account Number Exists.
                    model_partner_bank = self.env['res.partner.bank']
                    model_to_unlink = model_partner_bank.search([('acc_number','=' , migrate.employee_account_number)])

                    if len(model_to_unlink) > 0:
                        model_to_unlink.unlink()
                    new_rec= model_partner_bank.create({
                            'name' : migrate.employee_account_number,
                            'footer':False,
                            'state': 'bank',
                            'acc_number' : migrate.employee_account_number})
                    hr_employee = self.env['hr.employee'].search([('name','=', migrate.name)])
                    if len(hr_employee) > 0:
                        hr_employee.write({'bank_account_id': new_rec.id})
        else:
            raise Warning('No Employee')






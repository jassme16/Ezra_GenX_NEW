from openerp import models,fields, api

class BankAccountNumber(models.Model):
    _name = 'migrate.employee.loans'
    _description = 'Migration for Employee Loan'

    name = fields.Char('Employee Name')
    employee_id = fields.Many2one('Employee ID')
    employee_account_number = fields.Char('Account Number')
    sss_loan_amount = fields.Float('SSS Loan Amount', default = 0)
    pagibig_salary_loan = fields.Float('Pagibig Salary Loan Amount', default = 0)
    pagibig_calamity_loan = fields.Float('Pagibig Calamity Loan Amount', default = 0)

    @api.one
    def Generate(self):
        MONTH_REMAINING = 24
        MONTH_START =1
        YEAR_START =2016


        model_migration = self.env['migrate.employee.loans'].search([])

        if len(model_migration) > 0:
            for migrate in model_migration:
                # SSS LOAN
                hr_employee = self.env['hr.employee'].search([('name','=', migrate.name)])
                if migrate.sss_loan_amount > 0:
                    if len(hr_employee) > 0:
                        hr_employee.write({
                            'sss_loans_monthly_amortization': migrate.sss_loan_amount,
                            'sss_loans_remaining_months': MONTH_REMAINING,
                            'sss_loans_start_Month': MONTH_START,
                            'sss_loans_start_year': YEAR_START,})

                # Salary Loan
                if migrate.pagibig_salary_loan > 0:
                    if len(hr_employee) > 0:
                        hr_employee.write({
                            'pagibig_salaryloan_monthly_amortization': migrate.pagibig_salary_loan,
                            'pagibig_salaryloan_remaining_months': MONTH_REMAINING,
                            'pagibig_salaryloan_start_Month': MONTH_START,
                            'pagibig_salaryloan_start_year': YEAR_START,})

                # Calamity Loan
                if migrate.pagibig_calamity_loan > 0:
                    if len(hr_employee) > 0:
                        hr_employee.write({
                            'pagibig_calamityloan_monthly_amortization': migrate.pagibig_calamity_loan,
                            'pagibig_calamityloan_remaining_months': MONTH_REMAINING,
                            'pagibig_calamityloan_start_Month': MONTH_START,
                            'pagibig_calamityloan_start_year': YEAR_START,})

        else:
            raise Warning('No Employee')

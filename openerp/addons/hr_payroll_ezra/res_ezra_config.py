from openerp import models, fields,api
from parameters import constants
from openerp.exceptions import ValidationError


class CompanySetup(models.Model):
    _name = 'res.company.setup'
    _description = 'Company Additional Information'
    _inherit = 'mail.thread'
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    sss_no = fields.Char('SSS No.',size=20, required=True)
    hdmf_no = fields.Char('Pag-ibig No.', size=20, required=True)
    phic_no = fields.Char('Philhealth No.', size=20, required=True)
    tin_no = fields.Char('Tax No.', size=20, required=True)

    old_minimum_wage = fields.Float('Previous Minimum Wage.', digits=(18,2) ,required=True)
    latest_minimum_wage = fields.Float('Latest Minimum Wage.', digits=(18,2), required=True)

    @api.one
    def ChangeMWEAmount(self):
        employees = self.env['hr.employee'].search([])
        if len(employees) > 0:
            for employee in employees:
                if employee.contract_id.daily_rate == self.old_minimum_wage:
                    employee.contract_id.write({'daily_rate': self.latest_minimum_wage})
                    employee.contract_id.recomputeRate3()
            self.old_minimum_wage = self.latest_minimum_wage
            self.latest_minimum_wage = 0


class CustomerBranchMain(models.Model):
    _name = 'res.customers.main'
    _description = 'Customer Branches'
    _inherit = 'mail.thread'
    code = fields.Char('Code')
    name = fields.Char('Customer')

    branches_id =fields.Many2one('res.customer.branches', 'Branches')

    customer_info = fields.Many2one('res.partner', 'Customer')
    main_cust_id = fields.One2many('res.customer.branches', 'main_detail_id',readonly=False,copy=False)
    assignment_ids = fields.One2many('res.customer.temp.projects', 'main_detail_id',readonly=False,copy=False)

    @api.onchange('assignment_ids')
    def checkAssignmentChanges(self):
        print 'Y'
        #raise Warning(11)
        #return True
    #This will Create a Job ID

    @api.one
    #@api.onchange('branches_id')
    def getAssignments(self):
        cust_id = self.id
        model_assignment_ids = self.assignment_ids.search([('main_detail_id', '=', self.id)])
        model_assignment_ids.unlink()
        #raise Warning(cust_id)
        #Select all Records in Project Setup
        model_customer_setup = self.env['res.customer.setup'].search([('customer_id', '=' , self.branches_id.customer_info.id)])
        #raise Warning(self.branches_id.customer_info.id)
        if len(model_customer_setup) > 0:
            for assignment in model_customer_setup:
               model_assignment_ids.create({
                    'main_detail_id': cust_id,
                    'customer_id': self.branches_id.customer_info.id,
                    'job_id': assignment.job_id.id,
                    'monthly_rate': assignment.monthly_rate,
                    'total_labor_cost': assignment.total_labor_cost,
                    'due_to_government': assignment.due_to_government,
                    'thirteenth_month': assignment.thirteenth_month,
                    'incentive_leaves': assignment.incentive_leaves,
                    'allowance': assignment.allowance,
                    'overhead_cost': assignment.overhead_cost,
                    'uniform_allowance': assignment.uniform_allowance,
                    'supplies': assignment.supplies,
                    'equipment': assignment.equipment,
                    'is_project_vatable': assignment.is_project_vatable,
                })
        self.assignment_ids = self.assignment_ids.ids

    @api.one
    def saveCustAssignment(self):
        model_cust_setup = self.env['res.customer.setup']
        for assignment in self.assignment_ids:
            model_cust_setup = self.env['res.customer.setup'].search([('customer_id', '=' , assignment.customer_id),
                                                                      ('job_id', '=' , assignment.job_id)])
            if len(model_cust_setup) > 0:
               model_cust_setup.create({
                    'name': assignment.customer_id.name + '/' + assignment.job_id.name,
                    'customer_id': assignment.customer_id.id,
                    'job_id': assignment.job_id.id,
                    'monthly_rate': assignment.monthly_rate,
                    'total_labor_cost': assignment.total_labor_cost,
                    'due_to_government': assignment.due_to_government,
                    'thirteenth_month': assignment.thirteenth_month,
                    'incentive_leaves': assignment.incentive_leaves,
                    'allowance': assignment.allowance,
                    'overhead_cost': assignment.overhead_cost,
                    'uniform_allowance': assignment.uniform_allowance,
                    'supplies': assignment.supplies,
                    'equipment': assignment.equipment,
                    'is_project_vatable': assignment.is_project_vatable,
                })
            else:
               model_cust_setup.write({
                    'name': assignment.customer_id.name + '/' + assignment.job_id.name,
                    'customer_id': assignment.customer_id.id,
                    'job_id': assignment.job_id.id,
                    'monthly_rate': assignment.monthly_rate,
                    'total_labor_cost': assignment.total_labor_cost,
                    'due_to_government': assignment.due_to_government,
                    'thirteenth_month': assignment.thirteenth_month,
                    'incentive_leaves': assignment.incentive_leaves,
                    'allowance': assignment.allowance,
                    'overhead_cost': assignment.overhead_cost,
                    'uniform_allowance': assignment.uniform_allowance,
                    'supplies': assignment.supplies,
                    'equipment': assignment.equipment,
                    'is_project_vatable': assignment.is_project_vatable,
                })


class CustomerBranches(models.Model):
    _name = 'res.customer.branches'
    _description = 'Customer Branches detail'
    main_detail_id = fields.Many2one('res.customers.main')
    code = fields.Char('Code')
    name = fields.Char('Name')
    customer_info = fields.Many2one('res.partner', 'Customer', required =True)
    @api.one
    def getProjects(self):
        cust_id = self.main_detail_id.id
        cust_branch = self.customer_info.id

        #Delete first all Records
        model_projects = self.env['res.customer.temp.projects'].search([('main_detail_id', '=', cust_id)])
        model_projects.unlink()

        #Select all Records in Project Setup
        model_customer_setup = self.env['res.customer.setup'].search([('customer_id', '=' , cust_branch)])

        if len(model_customer_setup) > 0:
            for assignment in model_customer_setup:
                create = model_projects.create({
                    'main_detail_id': cust_id,
                    'job_id': assignment.job_id.id,
                    'monthly_rate': assignment.monthly_rate,
                    'total_labor_cost': assignment.total_labor_cost,
                    'due_to_government': assignment.due_to_government,
                    'thirteenth_month': assignment.thirteenth_month,
                    'incentive_leaves': assignment.incentive_leaves,
                    'allowance': assignment.allowance,
                    'overhead_cost': assignment.overhead_cost,
                    'uniform_allowance': assignment.uniform_allowance,
                    'supplies': assignment.supplies,
                    'equipment': assignment.equipment,
                    'is_project_vatable': assignment.is_project_vatable,
                })

        return self.main_detail_id.checkAssignmentChanges()


#Temporary Tables because Transient Model has Limitation >.<
class CustomerProjects(models.Model):
    _name = 'res.customer.temp.projects'
    _description = 'Customer Projects'

    main_detail_id = fields.Many2one('res.customers.main')
    name = fields.Char('Assignment')
    customer_id = fields.Many2one('res.partner','Customer', required = True)
    job_id = fields.Many2one('hr.job', 'Assignment', required = True)
    factor_days = fields.Integer('Factors Days', required=True, default=0)
    monthly_rate = fields.Float('Monthly rate',digits=(18,2), required =True, default=0)
    is_project_vatable = fields.Boolean('With Vat?', default = False)
    total_labor_cost = fields.Float('Total Labor Cost',digits=(18,2), required =True, default=0)
    due_to_government = fields.Float('Due to Government',digits=(18,2), required =True, default=0)
    thirteenth_month = fields.Float('13th Month',digits=(18,2), required =True, default=0)
    incentive_leaves = fields.Float('Incentive Leaves',digits=(18,2), required =True, default=0)
    allowance = fields.Float('Allowance',digits=(18,2), required =True, default=0)
    overhead_cost = fields.Float('Overhead Cost (%)',digits=(18,2), required =True, default=0)
    uniform_allowance = fields.Float('Uniform Allowance',digits=(18,2), required =True, default=0)
    supplies = fields.Float('Supplies',digits=(18,2), required =True, default=0)
    equipment = fields.Float('Equipment',digits=(18,2), required =True, default=0)


class CustomerAdditionalSetup(models.Model):
    _name = 'res.customer.setup'
    _description = 'Customer Additional Setup for Ezra'
    _inherit = 'mail.thread'
    name = fields.Char('Name', default = '/')
    customer_id = fields.Many2one('res.partner','Customer', required = True)
    job_id = fields.Many2one('hr.job', 'Job Title', required = True)
    factor_days = fields.Integer('Factors Days', required=True, default=0)
    daily_rate = fields.Float('Daily Wage',digits=(18,2), required =True, default=0)
    monthly_rate = fields.Float('Monthly Project Cost',digits=(18,2), required =True, default=0)
    is_project_vatable = fields.Boolean('With Vat?', default = False)
    total_labor_cost = fields.Float('Total Labor Cost',digits=(18,2), required =True, default=0)
    due_to_government = fields.Float('Due to Government',digits=(18,2), required =True, default=0)
    thirteenth_month = fields.Float('13th Month',digits=(18,2), required =True, default=0)
    incentive_leaves = fields.Float('Incentive Leaves',digits=(18,2), required =True, default=0)
    allowance = fields.Float('Allowance',digits=(18,2), required =True, default=0)
    overhead_cost = fields.Float('Overhead Cost (%)',digits=(18,2), required =True, default=0)
    uniform_allowance = fields.Float('Uniform Allowance',digits=(18,2), required =True, default=0)
    supplies = fields.Float('Supplies',digits=(18,2), required =True, default=0)
    equipment = fields.Float('Equipment',digits=(18,2), required =True, default=0)

    @api.one
    def computeContract(self):
        if self.factor_days <=0:
            raise Warning('Factor day/s is less than or equal to zero.')
        if self.daily_rate <= 0:
            raise Warning('Daily rate is less than or equal to zero.')
        cur_basic_pay = (self.daily_rate * self.factor_days) / constants.MONTHS_IN_YEAR
        self.thirteenth_month = cur_basic_pay / constants.MONTHS_IN_YEAR
        self.incentive_leaves = (cur_basic_pay / self.factor_days) * constants.INCENTIVE_LEAVES

        if self.total_labor_cost > 0:
            flt_laborcost = self.total_labor_cost / constants.ONE_HUNDRED_PERCENT
        else:
            flt_laborcost = 0

        curr_overhead_cost  = 0
        curr_allowance = self.allowance + self.supplies + self.equipment

        if self.overhead_cost > 0:
            curr_overhead_cost = (self.total_labor_cost + self.due_to_government + curr_allowance) * (self.overhead_cost/constants.ONE_HUNDRED_PERCENT)

        if self.is_project_vatable:
            curr_vatable_amount = ((self.total_labor_cost + self.due_to_government) + curr_overhead_cost + curr_allowance) * constants.VAT_RATE
            self.monthly_rate = ((self.total_labor_cost + self.due_to_government) + curr_overhead_cost + curr_allowance) + curr_vatable_amount
        else:
            self.monthly_rate = ((self.total_labor_cost + self.due_to_government) + curr_overhead_cost + curr_allowance)

    #Override Function
    @api.model
    def create(self, vals):
        job_exist = self.env['res.customer.setup'].search([('customer_id', '=', int(vals['customer_id'])),
                                                           ('job_id', '=', int(vals['job_id']))])
        if len(job_exist) > 0:
            raise Warning(job_exist.job_id.name + ' already exist in customer ' + job_exist.customer_id.name)

        new_record = super(CustomerAdditionalSetup, self).create(vals)
        # Code after create
        # Can use the `new` record created
        return new_record

    @api.one
    def write(self, vals):
        super(CustomerAdditionalSetup, self).write(vals)
        return True

    @api.one
    @api.onchange('customer_id','job_id')
    def getDefaultName(self):
        if len(self.customer_id) > 0 and len(self.job_id) > 0:
            #raise Warning(self.customer_id.name + '/' + self.job_id.name)
            self.name = self.customer_id.name + '/' + self.job_id.name




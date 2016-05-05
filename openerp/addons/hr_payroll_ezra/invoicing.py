# -*- coding: utf-8 -*-
from openerp import models, fields,api


class clientInformation(models.Model):
    _name = 'hr.payroll.client'
    #_inherit = 'res.partner'

    is_company = fields.Boolean('(Client is a Company?)', default = False)
    #is_branch = fields.Boolean('(Client is a Company?)', default = False)
    name = fields.Char('Client')
    client_tin = fields.Char('TIN')
    client_laborcost = fields.Float('Total Labor Cost', default=0, required =True)
    client_duetoGovernment = fields.Float('Due to Government', default=0, required =True)
    client_13thMonthPay = fields.Float('13th Month Pay', default=0, required =True)
    client_incentiveleave = fields.Float('Incentive leaves', default=0, required =True)
    client_allowance = fields.Float('Allowance', default=0, required =True)
    client_overheadcost = fields.Float('Overhead Cost(%)', default=0, required =True)
    client_uniform_allowance = fields.Float('Uniform Allowance', default=0, required =True)
    client_supplies = fields.Float('Supplies', default=0, required =True)
    client_equipment = fields.Float('Equipment', default=0, required =True)


# -*- coding: utf-8 -*-
from openerp import models, fields,api


class genxMenuAudit(models.Model):
    _name = 'sys.genx.audit'

    _description = 'A Basic audit trail for Genx'

    name = fields.Char('Name')
    description = fields.Text('Description')
    user_id_trigger = fields.Many2one('res.users', 'User ID')
    menu_triggered = fields.Char('Menu Used')
    menu_information = fields.Char('Document Name')
    event_happened = fields.Char('User Interactions')
    old_value = fields.Char('Old Value')
    new_value = fields.Char('New Value')
    count  = fields.Integer('No.')
    related_id = fields.Integer('Table ID')

    #Follow Up
    #dev_object_triggered = fields.Char()

    @api.model
    def createAuditTrailForPayrollGeneration(self, name = '', description = '', user_id_trigger = '',menu_triggered ='',
                         menu_information ='', event_happened ='', old_value = '', new_value ='', payroll_id = 0):
        int_count = 0
        model_audit = self.env['sys.genx.audit'].search([('related_id', '=', payroll_id)])
        if len(model_audit)  == 0:
            int_count = 1
        else:
            event_happened = 'Recompute Payroll'
            int_count = len(model_audit) + 1

        self.create(
            {
                'name': name,
                'description': description,
                'user_id_trigger': user_id_trigger,
                'menu_triggered': menu_triggered,
                'menu_information':menu_information,
                'event_happened':event_happened,
                'old_value':old_value,
                'new_value':new_value,
                'count': int_count,
                'related_id' : payroll_id,
            })

    @api.model
    def createAuditTrail(self, name = '', description = '', user_id_trigger = '',menu_triggered ='',
                         menu_information ='', event_happened ='', old_value = '', new_value ='', id = 0):
        self.create(
            {
                'name': name,
                'description': description,
                'user_id_trigger': user_id_trigger,
                'menu_triggered': menu_triggered,
                'menu_information':menu_information,
                'event_happened':event_happened,
                'old_value':old_value,
                'new_value':new_value,
                'related_id': id,
            })
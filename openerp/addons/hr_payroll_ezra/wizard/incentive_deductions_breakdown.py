from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
#from parameters import constants as genx

class payrollIncentiveMain(models.TransientModel):
    # 1 Incentive
    # 2 Deduction

    _name = 'payroll.incentive.main.wiz'
    _description = 'Payroll Incentive Deduction Main Wizard'
    other_type = fields.Integer('Deduction/Incentive', default = 1)
    payroll_detail_id = fields.Many2one('hr.payroll.detail', 'Payroll Detail')
    name = fields.Char('Name')
    incentive_ids = fields.One2many('payroll.incen.breakdown.wiz', 'main_id', readonly=False, copy=False,auto_join=True)
    state = fields.Integer('Payroll statle', default=1)


    @api.model
    def create(self, vals):
        new_record = super(payrollIncentiveMain, self).create(vals)
        incent_wiz = self.env['payroll.incen.breakdown.wiz'].search([])
        incent_wiz.unlink()
        incentive_main = self.env["payroll.detail.incentives"].search([('payroll_detail_id', '=', new_record.payroll_detail_id.id)])
        if len(incentive_main) > 0:
            for incentive in incentive_main:
                model_incentive = self.incentive_ids.search([('breakdown_id','=',incentive.id),
                                                             ('type','=',1)])
                if len(model_incentive) == 0:

                        self.incentive_ids.create({
                            'main_id' : new_record.id,
                            'name': incentive.name.id,
                            'amount': incentive.amount,
                            'breakdown_id' : incentive.id,
                            'type': 1
                        })

        incentive_main = self.env["payroll.detail.deduction"].search([('payroll_detail_id', '=', new_record.payroll_detail_id.id)])
        if len(incentive_main) > 0:
            for incentive in incentive_main:
                model_incentive = self.incentive_ids.search([('breakdown_id','=',incentive.id),
                                                             ('type','=',2)])
                if len(model_incentive) == 0:

                        self.incentive_ids.create({
                            'main_id' : new_record.id,
                            'name_deduction': incentive.name.id,
                            'amount': incentive.amount *-1,
                            'breakdown_id' : incentive.id,
                            'type': 2
                        })
        return new_record


    #@api.onchange('payroll_detail_id')
    #def getInfos(self):
    #    if self.other_type == 1:
    #        incentive_main = self.env['payroll.incentive.main'].search([('payroll_detail_id', '=', self.payroll_detail_id.id)])
    #        incentive_breakdown = self.env['payroll.incen.breakdown'].search([('main_id', '=', incentive_main.id)])
    #        if len(incentive_main) > 0:
    #            self.name = incentive_main.name
    #            for incentive in incentive_breakdown:
    #                model_incentive = self.incentive_ids.search([('breakdown_id','=',incentive.id)])
    #                if len(model_incentive) == 0:
    #                    self.incentive_ids.create({
    #                        'main_id' : self.id,
    #                        'name': incentive.name.id,
    #                        'amount': incentive.amount,
    #                        'breakdown_id' : incentive.id
    #                    })
    #            #if len(self.incentive_ids) > 0:
    #            self.incentive_ids = self.incentive_ids.search([('breakdown_id' , 'in', incentive_breakdown.ids)])

    @api.one
    def updateReliever(self):
        for incentive in self.incentive_ids:
            if incentive.type ==1:
                model_incentive = self.env['payroll.detail.incentives'].search([('id', '=', incentive.breakdown_id)])
                model_incentive.write({
                    'amount': incentive.amount})
            else:
                model_incentive = self.env['payroll.detail.deduction'].search([('id', '=', incentive.breakdown_id)])
                model_incentive.write({
                    'amount': incentive.amount *-1})
        model_payroll_main = self.env['hr.payroll.main']
        model_payroll_main.computePayrollExternal(self.payroll_detail_id.id)
        pass


class payrollIncentiveBreakdown(models.TransientModel):
    _name = 'payroll.incen.breakdown.wiz'
    _description = 'Payroll Incentive Deduction breakdown Wizard'

    main_id = fields.Many2one('payroll.inctv.dedct.main.wiz', 'Incentive Main ID')
    breakdown_id = fields.Integer('Breakdown ID')
    name = fields.Many2one('hr.incentives', 'Incentive')
    name_deduction = fields.Many2one('hr.deductions', 'Deduction')
    amount = fields.Float('Amount', digits=(18,2), default =0)
    type = fields.Integer('Type')

    @api.onchange('amount')
    def ChangeType(self):
        if self.type == 2:
            self.amount = self.amount * -1

from openerp.osv import fields, osv
from openerp.exceptions import Warning

from openerp.addons.hr_payroll_ezra.parameters import constants as genx

class payslip_per_EmployeeOSV(osv.osv_memory):
    _name = 'payroll.payslip.employee.temp'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee')
    }

    def print_report(self, cr, uid, ids, context=None):

        model_payroll_detail_temp_create = self.pool.get("hr.payroll.detail.temp")

        model_payroll_detail_temp = self.pool.get("hr.payroll.detail.temp").browse(cr,uid,ids,context=None)

        model_payroll_detail_temp_create.search(cr,uid,[('create_uid', '=',uid)],context=context)

        unlink_ids= []

        #unlink_ids = [pay_detail.id for pay_detail in model_payroll_detail_temp_create.browse(cr,uid,ids,context=None)]
        for pay_detail in model_payroll_detail_temp_create.browse(cr,uid,ids,context=None):
            #print(pay_detail.create_uid)
            #raise Warning(pay_detail.id)
            unlink_ids.append(pay_detail.id)

        #raise Warning(unlink_ids)

        model_payroll_detail_temp_create.unlink(cr, uid, unlink_ids, context=context)


        model_payroll_detail= self.pool.get("hr.payroll.detail")
        pay_ids = model_payroll_detail.search(cr,uid,[('create_uid', '=',uid)],context=context)


        for payroll_detail in model_payroll_detail.browse(cr,uid,pay_ids,context=None):
            dict_save = {
                'payroll_detail_id':payroll_detail.payroll_detail_id.id,
                'name':payroll_detail.name,
                'employee_id':payroll_detail.employee_id.id,
                'employee_project_assign':payroll_detail.employee_project_assign.id,
                'is_reliever':payroll_detail.is_reliever,
                'basic_pay_perday':payroll_detail.basic_pay_perday,
                'basic_pay_perday_rate':payroll_detail.basic_pay_perday_rate,
                'basic_pay_amount':payroll_detail.basic_pay_amount,
                'basic_pay_leaves_perhour':payroll_detail.basic_pay_leaves_perhour,
                'basic_pay_leaves_amount':payroll_detail.basic_pay_leaves_amount,
                'reg_otpay_perhour':payroll_detail.reg_otpay_perhour,
                'reg_otpay_amount':payroll_detail.reg_otpay_amount,
                'reg_nightdiff_perhour':payroll_detail.reg_nightdiff_perhour,
                'reg_nightdiffy_amount':payroll_detail.reg_nightdiffy_amount,
                'basic_pay_restday_perhour':payroll_detail.basic_pay_restday_perhour,
                'basic_pay_restday_amount':payroll_detail.basic_pay_restday_amount,
                'basic_pay_restday_ot_perhour':payroll_detail.basic_pay_restday_ot_perhour,
                'basic_pay_restday_ot_amount':payroll_detail.basic_pay_restday_ot_amount,
                'reg_straightduty_perhour':payroll_detail.reg_straightduty_perhour,
                'reg_straightduty_amount':payroll_detail.reg_straightduty_amount,
                'cola_rate_perday':payroll_detail.cola_rate_perday,
                'cola_amount':payroll_detail.cola_amount,
                'reg_hol_pay_perday':payroll_detail.reg_hol_pay_perday,
                'reg_hol_pay_amount':payroll_detail.reg_hol_pay_amount,
                'reg_hol_work_pay_perhour':payroll_detail.reg_hol_work_pay_perhour,
                'reg_hol_work_pay_amount':payroll_detail.reg_hol_work_pay_amount,
                'reg_hol_otpay_perhour':payroll_detail.reg_hol_otpay_perhour,
                'reg_hol_otpay_amount':payroll_detail.reg_hol_otpay_amount,
                'reg_spechol_perhour':payroll_detail.reg_spechol_perhour,
                'reg_spechol_amount':payroll_detail.reg_spechol_amount,
                'reg_spechol_otpay_perhour':payroll_detail.reg_spechol_otpay_perhour,
                'reg_spechol_otpay_amount':payroll_detail.reg_spechol_otpay_amount,
                'other_incentive':payroll_detail.other_incentive,
                'tardiness':payroll_detail.tardiness,
                'tardiness_permin_rate':payroll_detail.tardiness_permin_rate,
                'tardiness_amount':payroll_detail.tardiness_amount,
                'undertime':payroll_detail.undertime,
                'tardiness_pay_permin_rate':payroll_detail.tardiness_pay_permin_rate,
                'undertime_amount':payroll_detail.undertime_amount,
                'gross_salary':payroll_detail.gross_salary,
                'sss_premium':payroll_detail.sss_premium,
                'sss_loan':payroll_detail.sss_loan,
                'hdmf_premium':payroll_detail.hdmf_premium,
                'hdmf_salary_loan':payroll_detail.hdmf_salary_loan,
                'hdmf_calamity_loan':payroll_detail.hdmf_calamity_loan,
                'hmo_premium':payroll_detail.hmo_premium,
                'other_deductions':payroll_detail.other_deductions,
                'deductions':payroll_detail.deductions,
                'net_pay':payroll_detail.net_pay,
                'computed_tax':payroll_detail.computed_tax,
                'month_half_period':payroll_detail.month_half_period,
                'month_name_period':payroll_detail.month_name_period,
                'year_payroll_period':payroll_detail.year_payroll_period,
                'payroll_detail_date':payroll_detail.payroll_detail_date,
                'incentive_id':payroll_detail.incentive_id,
                'deduction_id':payroll_detail.deduction_id,}

            model_payroll_detail_temp_create.create(cr, uid, dict_save)

        if context is None:
            context = {}

        data = self.read(cr, uid, ids, ['employee_id'], context=context)[0]
        #data= self.pool.get("hr.payroll.detail").browse(cr,uid,ids,context=None)
        #raise Warning(ids)
        #x_data = {'employee_id': self.employee_id}

        #raise Warning(data)
        obj = self.pool.get('hr.payroll.detail.temp')
        ids = obj.search(cr, uid, [('employee_id','=',9729)])

        #raise Warning(ids)
        #x_data = {'employee_id':9729}
        datas = {
             'ids': [],
             'model': 'hr.payroll.detail.temp',
             'form': data
            }

        return self.pool['report'].get_action(
                    cr, uid, [], 'hr_payroll_ezra.report_payslip_employee', data=datas, context=context)

        #return {
        #    'type': 'ir.actions.report.xml',
        #    'report_name': 'hr_payroll_ezra.report_payslip_employee',
        #    'datas': datas,
        #    }
        #pass
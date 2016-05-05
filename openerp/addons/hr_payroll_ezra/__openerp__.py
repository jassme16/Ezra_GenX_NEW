{
    'name': 'GenX Payroll(Ezra)',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'GenX Payroll for Ezra',
    'description': 'hr_ezra',
    'author': 'GenXERP',
    'depends': ['hr_payroll','mail','web'],
    'data': [
            'view\payroll_incentive_deduction_breakdown.xml',
            'wizard\payroll_incentive_deduction_breakdown_wiz.xml',
            'wizard\wiz_attendance_reliever.xml',
            'wizard\hr_payroll_attendance.xml',
            'view\hr_attendance.xml',
            'view\hr_payroll_menu.xml',
            'view\hr_payroll_view.xml',
            'view\hr_ezra_config.xml',
            'view\hr_ezra_customer_add_setup.xml',
            'view\hr_holiday.xml',
            'report\_rpt_payslip_ezra.xml',
            'report\employee_payslip_view.xml',
            'report\_rpt_payslip_employee_ezra2.xml',
            'bank_payroll\securit_bank.xml',
            'security\ir.model.access.csv',
            'security\payslip_employee_checklist_rules.xml',
            'security\payroll_ezra_rules.xml',
            'data\ir_sequence.xml',
            'audit_trail\_audit_trail.xml'

    ],

    'application': True,
}
#
#            'report\_rpt_payslip_employee_ezra.xml',
#            'report\_rpt_payslip_employee_ezra2.xml',
#            'wizard\payroll_payslip_employee.xml',
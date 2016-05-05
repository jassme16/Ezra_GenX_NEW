{
    'name': 'GenX 13th Month Pay',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': '13th Month Pay Generation',
    'description': 'Generation of 13th Month Pay and be Reflected in Payroll',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
         'report\hbonus_thirteenth_month_rpt.xml',
         'report\hbonus_summary_rpt.xml',
         'view\hr_payroll_13thmonth_pay.xml',
         'security\ir.model.access.csv'
    ],
    'application': True,
}
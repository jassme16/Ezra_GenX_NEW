{
    'name': 'GenX PHIC RF-1',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'GenX Philhealth RF-1 Employers Remittance Form',
    'description': 'hr_payroll_phic_rf1',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
        'views\hr_payroll_phic_rf1.xml',
        'security\ir.model.access.csv'
    ],

    'application': True,
}
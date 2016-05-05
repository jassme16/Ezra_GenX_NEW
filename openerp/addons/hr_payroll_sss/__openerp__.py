{
    'name': 'GenX SSS Premium/Loan',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'GenX SSS Form',
    'description': 'SSS Contribution and loans generator based on generated payroll months',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
        'view\hr_payroll_sss_contribution.xml',
        'view\hr_payroll_sss_loan.xml',
        'security\ir.model.access.csv'
    ],
    'application': True,
}
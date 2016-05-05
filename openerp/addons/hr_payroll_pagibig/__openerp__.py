{
    'name': 'GenX HDMF Premium contribution',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'List of Pag-ibig Members Contribution',
    'description': 'hr_payroll_phic_rf1',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
         'view\pagibig_conribution.xml',
         'view\pagibig_loans.xml',
         'security\ir.model.access.csv'
    ],

    'application': True,
}
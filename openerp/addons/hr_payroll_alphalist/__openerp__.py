{
    'name': 'GenX Alphalist',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'Alphalist Generation',
    'description': 'List of Employees Annual Withholding Tax',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
         'view\hr_payroll_alphalist.xml',
         'view\hr_payroll_alphalist_config.xml'
    ],
    'application': True,
}

#'security\ir.model.access.csv'
{
    'name': 'GenX Client Billing',
    'category': 'Invoicing',
    'sequence': 25,
    'summary': 'Client''s Billing',
    'description': 'Client Billing Generation',
    'author': 'GenXERP',
    'depends': ['mail'],
    'data': [
         'wizard\hr_payroll_ezra_batch_billing_report.xml',
         'view\hr_payroll_ezra_billing_relievers.xml',
         'view\hr_payroll_ezra_billing.xml',
         'view\hr_payroll_billing_batch.xml',
         'security\ir.model.access.csv',
    ],

    'application': True,
}
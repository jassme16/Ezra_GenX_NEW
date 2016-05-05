{
    'name': 'GenX Recruitment Process',
    'category': 'Human Resources',
    'sequence': 25,
    'summary': 'Jobs, Recruitment, Applications, Job Interviews, Surveys',
    'description': 'hr_recruitment_2',
    'author': 'GenXERP',
    'depends': ['hr','mail', 'resource', 'board'],
    'data': ['views\hr_recruitment_view.xml',
             'views\hr_recruitment_seabased_menu.xml',
             'views\hr_recruitment_dialog.xml',
             'reports\hr_recruitment_base_report.xml',
             'data\ir_sequence.xml'],
    'css': ['static/src/css/hr.css'],
    'application': True,
}
#'data': ['hr_recruitment_view.xml','views\hr_recruitment_personnel_view.xml'],
#'security\ir.model.access.csv'


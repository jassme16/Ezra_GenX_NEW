# Right Now this must be Constant Value
import datetime
import calendar
from openerp.models import Model, fields, api
from openerp.api import Environment
from openerp import tools

DETAIL_STATUS = [
    (1, 'GENERATED'),
    (2, 'EDITED'),
]

STATE_ALPHA= [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Submitted')
]

SCHEDULE_PAY=[
    'quarterly',
    'monthly',
    'semi-annually'
    'weekly',
    'bi-weekly',
    'bi-monthly',
    'annually'
]

ALPHALIST_SCHEDULE = [
    (1, 'Schedule 7.1'),
    (2, 'Schedule 7.2'),
    (3, 'Schedule 7.3'),
    (4, 'Schedule 7.4'),
    (5, 'Schedule 7.5'),
]

MONTH_SELECTION = [
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December')]

MONTH_QUARTER_SELECTION = [
    (1, '1st Half'),
    (2, '2nd Half')
]

STATE= [
    ('draft', 'Draft'),
    ('approved', 'Approved'),
    ('post', 'Paid')
]

WORK_CODE ={'DRATE': 'DRATE',
            'ROT': 'ROT',
            'NDIFF': 'NDIFF',
            'RESTDRATE': 'RESTDRATE',
            'RESTOT': 'RESTOT',
            'RESTNDIFF': 'RESTNDIFF',
            'SPEHDRATE': 'SPEHDRATE',
            'SPEHOT': 'SPEHOT',
            'REGHDRATE': 'REGHDRATE',
            'REGHOT': 'REGHOT',
            'REGHNDIFF': 'REGHNDIFF',
            'SPEHNDIFF': 'SPEHNDIFF',
            'STRDUTY': 'STRDUTY'
            }

ISLAND_GROUP = [
    (1, 'Luzon'),
    (2, 'Visayas'),
    (3, 'Mindanao')
]

WORKING_DAYS=[
    (5,'5 Days'),
    (6,'6 Days'),
    (7,'7 Days'),
    (8,'Not Available'),
]

PER_DAY = 15.00

HOURS_PER_DAY = 8
ONE_HUNDRED_PERCENT = 100
VAT_RATE = 0.12

MINUTES =60

PER_PIXEL = 36

MINIMUM_WAGE_AMOUNT = 466 #env['payroll.alphalist.config'].GetAmount('MWE')

YEAR_NOW = datetime.datetime.now().year

DATE_NOW = datetime.datetime.now()
DATE_NOW_FORMATTED = datetime.datetime.now().strftime('%b %d, %Y')

MONTHS_IN_YEAR =12
WEEKS_IN_YEAR =52
WORK_IN_WEEK = 6

SQL_SELECT = " SELECT "

INCENTIVE_LEAVES = 5

SQL_FROM = " FROM "
SQL_WHERE = " WHERE "
SQL_AND = " AND "
SQL_OR = " OR "

EXCEL_TEMPLATES ="\excel-templates\\"

class GenXUtils:
    #def __init__(self):
    #    self.get_data_dir()

    #This will get the Values of openerp.server.conf
    #data_dir value
    get_data_dir = tools.config['data_dir']
    get_data_dir_excel_template = tools.config['data_dir'] + EXCEL_TEMPLATES

class ComputeTaxExemption(object):


    def returnExemptionAmout(self):
        additional_days = 0.00
        # Check if Year is in Leap Year
        if calendar.isleap(YEAR_NOW):
            additional_days = 1
        exemption_amount = ((MINIMUM_WAGE_AMOUNT * (52 *6)) + additional_days) /12
        return exemption_amount

class CreateSQLQuery(object):

    def __init__(self, tablename = "", columnnames = [], condition = "" ):
        self.tablename= tablename
        self.columnnames= columnnames
        self.condition= condition
        self.returnQuery()

    def returnQuery(self):
        query =""
        query  = SQL_SELECT
        columns =""
        if len(self.columnnames) > 0:
            count  = len(self.columnnames) -1
            counter = 0
            for columnname in self.columnnames:
                if counter == count:
                    columns =  columns + columnname
                else:
                    columns =  columns + columnname + ','
                counter = counter + 1
        else:
            columns = "*"
        query  =  query + columns + SQL_FROM + self.tablename
        if len(self.condition) > 0:
            query = query + SQL_WHERE + self.condition
        return query








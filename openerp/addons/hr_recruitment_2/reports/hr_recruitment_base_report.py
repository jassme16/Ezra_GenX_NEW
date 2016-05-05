# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp import tools
from openerp.report import report_sxw
from .. import hr_parameter_model
from .. import hr_recruitment_seabased
import datetime

PASSPORT_CODE = 'P'
SSRIB_CODE = 'S'
ACTIVE_ON_BOARD = '00001'

YEAR = 365
MONTH = 30
SECOND_PER_MINUTE = 60
MINUTE_PER_HOUR = 60
HOUR_PER_DAY = 24
FIFTY_MINUTES_TO_SECOND = 3540
DATE_NOW = datetime.datetime.now()

SQL_QUERY = " SELECT (DOCUMENT_NUMBER::CHAR(120)), (DATE_ISSUED::DATE), (DATE_EXPIRY::DATE) FROM HR_EMPLOYEE_DOCUMENTS" \
            " WHERE ('%(my_date)s'::date) BETWEEN DATE_ISSUED and DATE_EXPIRY" \
            " AND EMPLOYEE_DOC_ID = %(employee_id)d" \
            " AND DOCUMENT = (SELECT ID FROM hr_documenttype WHERE ABBREVIATION = '%(my_abbrv)s')" \
            " ORDER BY DATE_EXPIRY DESC" \
            " LIMIT 1"

SQL_QUERY_EMPLOYMENT_HISTORY =  " SELECT OBJECT_CODE FROM HR_EMPLOYMENTHISTORY"\
                                " WHERE ('%(my_date)s'::date) BETWEEN DATE_SERVICEFROM AND DATE_SERVICETO"\
                                " AND EMPLOYMENT_STATUS = (SELECT ID FROM HR_EMPLOYMENT_STATUS WHERE STATUS_ID = '%(statusid)s')"\
                                " AND EMPLOYEE_EMPLOYMENT_ID = %(employee_id)d"\
                                " ORDER BY DATE_SERVICETO DESC"\
                                " LIMIT 1"

# To View all the records and to create a customized reports
# Must be Naming convent

class hrPersonnelActiveOnBoardwithRemarks(models.Model):
    _name = "hr.personnel.withremrks.report"
    _auto = False

    employee_number = fields.Char("Employee Number", readonly=True)
    ccl_number = fields.Char("CCL Number", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    birth_date = fields.Date("Birth Date", readonly=True)
    employment_status = fields.Many2one("hr.employment.status", readonly=True, string="Status")
    date_servicefrom = fields.Date("Service from", readonly=True)
    date_serviceto = fields.Date("Service to", readonly=True)
    remarks = fields.Char("Remarks", readonly=True)
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")


    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_personnel_withremrks_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_personnel_withremrks_report AS (
                        SELECT
                            MIN(EMPH.ID) AS ID,
                            EMPLOYEE_NUMBER,
                            CCL_NUMBER,
                            EMPLOYMENT_RANK,
                            LAST_NAME,
                            FIRST_NAME,
                            BIRTHDAY AS BIRTH_DATE,
                            EMPLOYMENT_STATUS,
                            DATE_SERVICEFROM,
                            DATE_SERVICETO,
                            REMARKS,
                            EMPLOYMENT_DEPT_CODE,
                            OBJECT_CODE
                        FROM HR_EMPLOYEE EMP, HR_EMPLOYMENTHISTORY EMPH
                        WHERE EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID
                        AND LENGTH(TRIM(REMARKS )) > 0
                        GROUP BY OBJECT_CODE,
                             EMPLOYMENT_DEPT_CODE,
                             EMPLOYEE_NUMBER,
                             CCL_NUMBER,
                             EMPLOYMENT_RANK,
                             LAST_NAME ,
                             FIRST_NAME,
                             BIRTHDAY,
                             EMPLOYMENT_STATUS,
                             DATE_SERVICEFROM,
                             DATE_SERVICETO,
                             REMARKS,
                             EMPLOYMENT_DEPT_CODE)
                   """)


class hrCrewlistperDepartment(models.Model):
    _name = 'hr.crewlist.report'
    _auto = False

    @api.one
    def getPassportNumber(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY %{'my_date': date, 'employee_id': self.employee_id, 'my_abbrv': PASSPORT_CODE}
        self.env.cr.execute(query)
        passportInfos = self.env.cr.fetchall()
        if len(passportInfos) > 0:
            self.passport = passportInfos[0][0]
            self.passport_date_issued = passportInfos[0][1]
            self.passport_date_expiry = passportInfos[0][2]

    employee_number = fields.Char("Employee Number", readonly=True)
    ccl_number = fields.Char("CCL Number", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    birth_date = fields.Date("Birth Date", readonly=True)
    placeof_birth = fields.Char("Place of Birth", readonly=True)
    passport = fields.Char('Passport', readonly=True, compute =getPassportNumber)
    passport_date_issued = fields.Date('Date issued', readonly=True, compute = getPassportNumber)
    passport_date_expiry = fields.Date('Date expiry', readonly=True, compute = getPassportNumber)

    date_depart = fields.Date("Depart Date", readonly=True)
    date_servicefrom = fields.Date("Sign On Date", readonly=True)
    date_serviceto = fields.Date("Sign Off Date", readonly=True)
    place_signon = fields.Many2one('hr.port', 'Place signOn')

    employee_id = fields.Integer('Employee ID',readonly=True)
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")

    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_crewlist_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_crewlist_report AS (
                        SELECT
                            EMPH.ID ID,
                            EMP.ID EMPLOYEE_ID,
                            EMPLOYEE_NUMBER,
                            CCL_NUMBER,
                            LAST_NAME,
                            FIRST_NAME,
                            EMPLOYMENT_RANK,
                            COUNTRY_ID,
                            BIRTHDAY BIRTH_DATE,
                            PLACEOF_BIRTH,
                            '' PASSPORT,
                            '' PASSPORT_DATE_ISSUED,
                            '' PASSPORT_DATE_EXPIRY,
                            DATE_DEPARTURE DATE_DEPART,
                            DATE_SERVICETO,
                            DATE_SERVICEFROM,
                            "place_signOn" PLACE_SIGNON,
                            OBJECT_CODE,
                            EMPLOYMENT_DEPT_CODE
                        FROM HR_EMPLOYEE EMP, HR_EMPLOYMENTHISTORY EMPH
                        WHERE EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID
                        )
                   """)

class hrServiceRecordperDepartment(models.Model):
    _name = "hr.service.record.report"
    _auto = False

    @api.one
    def getServiceLength(self):
        days_remaining = 0
        service_days = int(abs(((self.days_of_service /SECOND_PER_MINUTE)/MINUTE_PER_HOUR)/HOUR_PER_DAY))
        if service_days == 0:
            self.service_length = '0Y 0M 0D'
        elif service_days <= 30:
            self.service_length = '0Y 1M 0D'
        else:
            year = int(abs(service_days/ YEAR))

            days_remaining = int(service_days- (year * YEAR))

            months = int(abs(days_remaining / MONTH))
            days_remaining =days_remaining -  (months * MONTH)
            self.service_length = str(year) + 'Y ' + str(months) + 'M ' +  str(days_remaining)  + 'D'
    @api.one
    def getEarnedIncentive(self):
        incentive_days = int(abs(((self.incentive_length /SECOND_PER_MINUTE)/MINUTE_PER_HOUR)/HOUR_PER_DAY))
        days_remaining = incentive_days
        if incentive_days == 0:
            self.earned_incentive = '0Y 0M 0D'
        elif incentive_days <= 30:
            self.earned_incentive = '0Y 1M 0D'
        else:
            years = int(abs(incentive_days/YEAR))

            days_remaining = int(incentive_days- (years * YEAR))
            months = abs(days_remaining / MONTH)
            days_remaining =days_remaining -  (months * MONTH)
            self.earned_incentive = str(int(years)) + 'Y ' + str(months) + 'M ' +  str(days_remaining) + 'D'

    @api.one
    def getserviceincentive(self):
        incentives = int(self.year_3) + int(self.year_5) + int(self.year_7) + int(self.year_10) + int(self.year_15) + int(self.year_20) + int(self.year_25)
        total = self.incentive_rate * incentives
        self.service_incentive = total

    @api.one
    def getIncentiveYearsRange(self):
        incentive_length_days = int(abs(((self.incentive_length /SECOND_PER_MINUTE)/MINUTE_PER_HOUR)/HOUR_PER_DAY))

        incentive_in_years = abs(incentive_length_days/YEAR)

        if incentive_in_years >= 3:
            self.year_3 = True
        else:
            self.year_3 = False

        if incentive_in_years >= 3:
            self.year_3 = True
        else:
            self.year_3 = False

        if incentive_in_years >= 5:
            self.year_5 = True
        else:
            self.year_5 = False

        if incentive_in_years >= 7:
            self.year_7 = True
        else:
            self.year_7 = False

        if incentive_in_years >= 10:
            self.year_10 = True
        else:
            self.year_10 = False

        if incentive_in_years >= 15:
            self.year_15 = True
        else:
            self.year_15 = False

        if incentive_in_years >= 20:
            self.year_20 = True
        else:
            self.year_20 = False

        if incentive_in_years >= 25:
            self.year_25 = True
        else:
            self.year_25 = False


    employee_number = fields.Char("Employee Number", readonly=True)
    name = fields.Char("Name", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    employment_ranktype = fields.Char("Rank Type") #fields.Many2one("hr.rank", readonly=True, string="Rank Type")
    service_length = fields.Char("Service Length", readonly=True, compute = getServiceLength)
    earned_incentive = fields.Char("Earned Incentive", readonly=True, compute = getEarnedIncentive)
    incentive_rate = fields.Float("Incentive Rate",(18,2),  readonly=True)
    year_3 = fields.Boolean('3 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_5 = fields.Boolean('5 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_7 = fields.Boolean('7 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_10 = fields.Boolean('10 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_15 = fields.Boolean('15 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_20 = fields.Boolean('20 Years',  readonly=True, compute = getIncentiveYearsRange)
    year_25 = fields.Boolean('25 Years',  readonly=True, compute = getIncentiveYearsRange)
    service_incentive = fields.Float("Service Incentive(US$)",(18,2),  readonly=True, compute = getserviceincentive)

    employment_status = fields.Many2one("hr.employment.status", readonly=True, string="Status")
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")
    date_servicefrom = fields.Date("Service from", readonly=True)
    date_serviceto = fields.Date("Service to", readonly=True)
    date_maxservicefrom = fields.Date("Service from", readonly=True)
    date_maxserviceto = fields.Date("Service to", readonly=True)

    years_of_service = fields.Float("Years of Service",(18,2),  readonly=True)
    days_of_service = fields.Float("Days of Service",(18,2),  readonly=True)
    incentive_length = fields.Float("Incentive Length",(18,2),  readonly=True)


    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_service_record_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_service_record_report AS (
                            SELECT
                                ID,
                                EMPLOYEE_NUMBER,
                                NAME,
                                EMPLOYMENT_RANK,
                                CODE EMPLOYMENT_RANKTYPE,
                                RATE INCENTIVE_RATE,
                                0 AS SERVICE_LENGHT,
                                0 AS EARNED_INCENTIVE,
                                0 YEAR_3,
                                0 YEAR_5,
                                0 YEAR_7,
                                0 YEAR_10,
                                0 YEAR_15,
                                0 YEAR_20,
                                0 YEAR_25,
                                0 AS SERVICE_INCENTIVE	,
                                EMPLOYMENT_STATUS,
                                EMPLOYMENT_DEPT_CODE,
                                DATE_SERVICEFROM,
                                DATE_SERVICETO,
                                OBJECT_CODE,
                                MAX_SERVICEFROM,
                                MAX_SERVICETO	,
                                ((((SERVICE_LENGTH /60)/60)/24)/30)/365 years_of_service,
                                SERVICE_LENGTH days_of_service,
                                INCENTIVE_LENGTH,
                                SERVICE_LENGTH
                            FROM (
                                SELECT
                                    EMPH.ID AS ID,
                                    EMPLOYEE_NUMBER,
                                    LAST_NAME || ', ' || FIRST_NAME AS NAME,
                                    EMPLOYMENT_RANK,
                                    RANKS.CODE,
                                    RATE,
                                    INCENTIVE_LENGTH,
                                    SERVICE_LENGTH,
                                    EMPLOYMENT_STATUS,
                                    EMPLOYMENT_DEPT_CODE,
                                    DATE_SERVICEFROM,
                                    DATE_SERVICETO,
                                    OBJECT_CODE,
                                    (SELECT MIN(DATE_SERVICEFROM) FROM HR_EMPLOYMENTHISTORY
                                     WHERE EMPLOYEE_EMPLOYMENT_ID = EMP.ID) MAX_SERVICEFROM,
                                    (SELECT MAX(DATE_SERVICETO) FROM HR_EMPLOYMENTHISTORY
                                     WHERE EMPLOYEE_EMPLOYMENT_ID = EMP.ID) MAX_SERVICETO
                                FROM HR_EMPLOYEE EMP
                                INNER JOIN HR_EMPLOYMENTHISTORY EMPH
                                    ON EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID
                                LEFT OUTER JOIN (SELECT CODE,HRT.ID, RATE
                                         FROM  HR_RANK HR,hr_ranktype HRT
                                         WHERE HR.RANK_TYPE = HRT.ID) RANKS
                                    ON EMPLOYMENT_RANK = RANKS.ID) A
                        )
                   """)


class hrFoclServiceBoard(models.Model):
    _name = "hr.focl.record.report"
    _auto = False

class hrSignOn(models.Model):
    _name = 'hr.signonoff.report'
    _auto = False

    employee_number = fields.Char("Employee Number", readonly=True)
    ccl_number = fields.Char("CCL Number", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    birth_date = fields.Date("Birth Date", readonly=True)
    employment_status = fields.Many2one("hr.employment.status", readonly=True, string="Status")
    date_depart = fields.Date("Depart Date", readonly=True)
    date_servicefrom = fields.Date("Sign On Date", readonly=True)
    date_serviceto = fields.Date("Sign Off Date", readonly=True)
    remarks = fields.Char("Remarks", readonly=True)
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")
    remarks = fields.Text('Remarks')
    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_signonoff_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_signonoff_report AS (
                        SELECT
                            ID,
                            EMPLOYEE_NUMBER,
                            CCL_NUMBER,
                            EMPLOYMENT_RANK,
                            LAST_NAME,
                            FIRST_NAME,
                            birthday BIRTH_DATE,
                            EMPLOYMENT_STATUS,
                            DATE_DEPARTURE DATE_DEPART,
                            EMPLOYMENT_DEPT_CODE,
                            DATE_SERVICEFROM,
                            DATE_SERVICETO,
                            OBJECT_CODE,
                            '' Remarks
                        FROM (
                            SELECT
                                EMPH.ID AS ID,
                                EMPLOYEE_NUMBER,
                                CCL_NUMBER,
                                LAST_NAME ,
                                FIRST_NAME,
                                birthday,
                                EMPLOYMENT_RANK,
                                EMPLOYMENT_STATUS,
                                EMPLOYMENT_DEPT_CODE,
                                DATE_DEPARTURE,
                                DATE_SERVICEFROM,
                                DATE_SERVICETO,
                                OBJECT_CODE
                            FROM HR_EMPLOYEE EMP
                            INNER JOIN HR_EMPLOYMENTHISTORY EMPH
                                ON EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID) A
                        )
                   """)


class hrDisembarkationReport(models.Model):
    _name = 'hr.disembarkation.report'
    _auto = False

    @api.one
    def getPassportNumber(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY %{'my_date': date, 'employee_id': self.employee_id, 'my_abbrv': PASSPORT_CODE}
        self.env.cr.execute(query)
        passportInfos = self.env.cr.fetchall()
        if len(passportInfos) > 0:
            self.passport = passportInfos[0][0]
            self.passport_date_issued = passportInfos[0][1]
            self.passport_date_expiry = passportInfos[0][2]

    @api.one
    def getSsribNumber(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY %{'my_date': date, 'employee_id': self.employee_id, 'my_abbrv': SSRIB_CODE}
        self.env.cr.execute(query)
        ssribInfos = self.env.cr.fetchall()
        if len(ssribInfos) > 0:
            self.ssrib = ssribInfos[0][0]
            self.ssrib_date_issued = ssribInfos[0][1]
            self.ssrib_date_expiry = ssribInfos[0][2]


    employee_number = fields.Char("Employee Number", readonly=True)
    ccl_number = fields.Char("CCL Number", readonly=True)
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    country_id = fields.Many2one('res.country', 'Nationality',readonly=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], readonly=True, string ='Gender')
    placeof_birth = fields.Char("Place of Birth", readonly=True)

    passport = fields.Char('Passport', readonly=True, compute =getPassportNumber)
    passport_date_issued = fields.Date('Date issued', readonly=True, compute = getPassportNumber)
    passport_date_expiry = fields.Date('Date expiry', readonly=True, compute = getPassportNumber)

    ssrib = fields.Char('SSIRB', readonly=True, compute=getSsribNumber)
    ssrib_date_issued = fields.Date('Date issued', readonly=True, compute=getSsribNumber)
    ssrib_date_expiry = fields.Date('Date expiry', readonly=True, compute=getSsribNumber)

    place_signoff = fields.Many2one('hr.port', 'Place signoff')

    date_depart = fields.Date("Depart Date", readonly=True)
    date_servicefrom = fields.Date("Sign On Date", readonly=True)
    date_serviceto = fields.Date("Sign Off Date", readonly=True)
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")
    employee_id = fields.Integer('Employee ID',readonly=True)

    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_disembarkation_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_disembarkation_report AS (
                        SELECT
                            ID,
                            EMPLOYEE_NUMBER,
                            CCL_NUMBER,
                            LAST_NAME,
                            FIRST_NAME,
                            EMPLOYMENT_RANK,
                            COUNTRY_ID,
                            GENDER,
                            PLACEOF_BIRTH,
                            '' PASSPORT_NUMBER,
                            '' PASSPORT_DATE_ISSUED,
                            '' PASSPORT_DATE_EXPIRY,
                            '' SSRIB,
                            '' SSRIB_DATE_ISSUED,
                            '' SSRIB_DATE_EXPIRY,
                            "place_signOff" PLACE_SIGNOFF,
                            DATE_DEPARTURE DATE_DEPART,
                            DATE_SERVICEFROM,
                            DATE_SERVICETO,
                            EMPLOYMENT_DEPT_CODE,
                            OBJECT_CODE,
                            EMPLOYEE_ID
                        FROM (
                            SELECT
                                EMPH.ID AS ID,
                                EMPLOYEE_NUMBER,
                                CCL_NUMBER,
                                LAST_NAME ,
                                FIRST_NAME,
                                EMPLOYMENT_RANK,
                                EMPLOYMENT_STATUS,
                                EMPLOYMENT_DEPT_CODE,
                                DATE_DEPARTURE,
                                DATE_SERVICEFROM,
                                DATE_SERVICETO,
                                OBJECT_CODE,
                                COUNTRY_ID,
                                GENDER,
                                PLACEOF_BIRTH,
                                "place_signOff",
                                EMP.ID EMPLOYEE_ID
                            FROM HR_EMPLOYEE EMP
                            INNER JOIN HR_EMPLOYMENTHISTORY EMPH
                                ON EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID) A
                        )
                   """)


class hrEmbarkationReport(models.Model):
    _name = 'hr.embarkation.report'
    _auto = False

    @api.one
    def getPassportNumber(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY %{'my_date': date, 'employee_id': self.employee_id, 'my_abbrv': PASSPORT_CODE}
        self.env.cr.execute(query)
        passportInfos = self.env.cr.fetchall()
        if len(passportInfos) > 0:
            self.passport = passportInfos[0][0]
            self.passport_date_issued = passportInfos[0][1]
            self.passport_date_expiry = passportInfos[0][2]

    @api.one
    def getSsribNumber(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY %{'my_date': date, 'employee_id': self.employee_id, 'my_abbrv': SSRIB_CODE}
        self.env.cr.execute(query)
        ssribInfos = self.env.cr.fetchall()
        if len(ssribInfos) > 0:
            self.ssrib = ssribInfos[0][0]
            self.ssrib_date_issued = ssribInfos[0][1]
            self.ssrib_date_expiry = ssribInfos[0][2]

    employee_number = fields.Char("Employee Number", readonly=True)
    ccl_number = fields.Char("CCL Number", readonly=True)
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    employment_rank = fields.Many2one("hr.rank", readonly=True, string="Rank")
    country_id = fields.Many2one('res.country', 'Nationality',readonly=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], readonly=True, string ='Gender')
    placeof_birth = fields.Char("Place of Birth", readonly=True)

    passport = fields.Char('Passport', readonly=True, compute =getPassportNumber)
    passport_date_issued = fields.Date('Date issued', readonly=True, compute = getPassportNumber)
    passport_date_expiry = fields.Date('Date expiry', readonly=True, compute = getPassportNumber)

    ssrib = fields.Char('SSIRB', readonly=True, compute=getSsribNumber)
    ssrib_date_issued = fields.Date('Date issued', readonly=True, compute=getSsribNumber)
    ssrib_date_expiry = fields.Date('Date expiry', readonly=True, compute=getSsribNumber)

    place_signon = fields.Many2one('hr.port', 'Place signOn')

    date_depart = fields.Date("Depart Date", readonly=True)
    date_servicefrom = fields.Date("Sign On Date", readonly=True)
    date_serviceto = fields.Date("Sign Off Date", readonly=True)
    employment_dept_code = fields.Many2one("hr.ship.department", readonly=True, string="Ship Department")
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel")
    employee_id = fields.Integer('Employee ID',readonly=True)

    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_embarkation_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_embarkation_report AS (
                        SELECT
                            ID,
                            EMPLOYEE_NUMBER,
                            CCL_NUMBER,
                            LAST_NAME,
                            FIRST_NAME,
                            EMPLOYMENT_RANK,
                            COUNTRY_ID,
                            GENDER,
                            PLACEOF_BIRTH,
                            '' PASSPORT_NUMBER,
                            '' PASSPORT_DATE_ISSUED,
                            '' PASSPORT_DATE_EXPIRY,
                            '' SSRIB,
                            '' SSRIB_DATE_ISSUED,
                            '' SSRIB_DATE_EXPIRY,
                            "place_signOn" PLACE_SIGNON,
                            DATE_DEPARTURE DATE_DEPART,
                            DATE_SERVICEFROM,
                            DATE_SERVICETO,
                            EMPLOYMENT_DEPT_CODE,
                            OBJECT_CODE,
                            EMPLOYEE_ID
                        FROM (
                            SELECT
                                EMPH.ID AS ID,
                                EMPLOYEE_NUMBER,
                                CCL_NUMBER,
                                LAST_NAME ,
                                FIRST_NAME,
                                EMPLOYMENT_RANK,
                                EMPLOYMENT_STATUS,
                                EMPLOYMENT_DEPT_CODE,
                                DATE_DEPARTURE,
                                DATE_SERVICEFROM,
                                DATE_SERVICETO,
                                OBJECT_CODE,
                                COUNTRY_ID,
                                GENDER,
                                PLACEOF_BIRTH,
                                "place_signOn",
                                EMP.ID EMPLOYEE_ID
                            FROM HR_EMPLOYEE EMP
                            INNER JOIN HR_EMPLOYMENTHISTORY EMPH
                                ON EMP.ID = EMPH.EMPLOYEE_EMPLOYMENT_ID) A
                        )
                   """)


class hrBeneficiaryList(models.Model):
    _name = 'hr.beneficiary.report'
    _auto = False

    @api.one
    def currentVessel(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY_EMPLOYMENT_HISTORY %{'my_date': date, 'employee_id': self.employee_id, 'statusid': ACTIVE_ON_BOARD}
        self.env.cr.execute(query)
        vessel = self.env.cr.fetchall()
        if len(vessel) > 0:
            self.object_code = vessel[0][0]


    employee_number = fields.Char("Employee Number", readonly=True)
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    middle_name = fields.Char("Middle Name", readonly=True)
    address_1 = fields.Char("Address 1", readonly=True)
    city = fields.Char('City', readonly=True)
    country_id = fields.Many2one('res.country', 'Country',readonly=True)
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel", compute =currentVessel)
    employee_id = fields.Integer('Employee ID',readonly=True)

    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_beneficiary_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_beneficiary_report AS (
                        SELECT
                            EMF.ID ID,
                            EMP.ID EMPLOYEE_ID,
                            EMPLOYEE_NUMBER,
                            EMF.LAST_NAME,
                            EMF.FIRST_NAME,
                            EMF.MIDDLE_NAME,
                            EMF.ADDRESS_1,
                            CITY,
                            EMF.COUNTRY_ID,
                            '' OBJECT_CODE
                        FROM HR_EMPLOYEE EMP, HR_EMPLOYEE_FAMILIES EMF
                        WHERE EMP.ID = EMF.EMPLOYEE_FAMILY_RELATIONSHIP_ID
                        AND IS_LIVING = (1::BOOLEAN)
                        AND IS_BENEFICIARY = (1::BOOLEAN))
                   """)


class hrAllotteeList(models.Model):
    _name = 'hr.allottee.report'
    _auto = False

    @api.one
    def currentVessel(self):
        date = datetime.datetime.strftime(DATE_NOW, "%Y-%m-%d")
        query = SQL_QUERY_EMPLOYMENT_HISTORY %{'my_date': date, 'employee_id': self.employee_id, 'statusid': ACTIVE_ON_BOARD}
        self.env.cr.execute(query)
        vessel = self.env.cr.fetchall()
        if len(vessel) > 0:
            self.object_code = vessel[0][0]

    employee_number = fields.Char("Employee Number", readonly=True)
    last_name = fields.Char("Last Name", readonly=True)
    first_name = fields.Char("First Name", readonly=True)
    middle_name = fields.Char("Middle Name", readonly=True)
    address_1 = fields.Char("Address 1", readonly=True)
    city = fields.Char('City', readonly=True)
    country_id = fields.Many2one('res.country', 'Country',readonly=True)
    object_code = fields.Many2one("hr.vessel", readonly=True, string="Vessel", compute =currentVessel)
    employee_id = fields.Integer('Employee ID',readonly=True)

    def init(self,cr):
        tools.drop_view_if_exists(cr, 'hr_allottee_report')
        cr.execute("""
                   CREATE OR REPLACE VIEW hr_allottee_report AS (
                        SELECT
                            EMF.ID ID,
                            EMPLOYEE_NUMBER,
                            EMP.ID EMPLOYEE_ID,
                            EMF.LAST_NAME,
                            EMF.FIRST_NAME,
                            EMF.MIDDLE_NAME,
                            EMF.ADDRESS_1,
                            CITY,
                            EMF.COUNTRY_ID,
                            '' OBJECT_CODE
                        FROM HR_EMPLOYEE EMP, HR_EMPLOYEE_FAMILIES EMF
                        WHERE EMP.ID = EMF.EMPLOYEE_FAMILY_RELATIONSHIP_ID
                        AND IS_LIVING = (1::BOOLEAN)
                        AND EMF.IS_ALLOTTEE = (1::BOOLEAN)
                        )
                   """)
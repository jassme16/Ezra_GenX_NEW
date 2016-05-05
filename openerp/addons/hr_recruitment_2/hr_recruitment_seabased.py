# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError

import datetime

YEAR = 365
MONTH = 30

DATE_NOW = datetime.datetime.now()

class HrPersonner(models.Model):
    _name = 'hr.personnel'
	
    #employee_number = fields.Char('Employee Number', required = True, default =1)
    full_name = fields.Char(string = 'Name', store = False, readonly=True,compute ="getFullname")
    first_name = fields.Char('First name', required = True)
    last_name = fields.Char('Last name', required = True)
    middle_name = fields.Char('Middle name')
    self_alotte = fields.Boolean('Self Allottee?', default = True)
    weight = fields.Char('Weight')
    height = fields.Char('Height')
    placeof_birth = fields.Char('Place of birth')
    sss_no = fields.Char('SSS No')
    hdmf_no = fields.Char('HDMF No')
    philhealth_no = fields.Char('Philhealth No')
    tin_no = fields.Char('Tin')
    aa_reg_no = fields.Char('AA Registry No')
    service_length = fields.Integer('Service Length')
    focllength = fields.Integer('Foclength')
    incentive_length = fields.Integer('Incentive Length')
    booking_id = fields.Char('Booking ID')
    bankacctno = fields.Text('Bank account number')
    checklistID = fields.Char('Checklist ID')
    ccl_number = fields.Char('CCL Number')
    pcn= fields.Char('PCN')
    legacy_doc_1 = fields.Binary('Confidential Reports')
    legacy_doc_2 = fields.Binary('Personal Data')
    legacy_doc_3 = fields.Binary('Personal Summary')
	
    employee_addresses = fields.One2many('hr.employeeaddress','employee_address_id', readonly=False,copy=False)
    #employee_education = fields.One2many('hr.employeducation','employee_education_id', readonly=False,copy=False)
    #employee_families = fields.One2many('hr.employee_families','employee_family_relationship_id', readonly=False,copy=False)
    #employee_documents = fields.One2many('hr.employee_documents','employee_doc_id', readonly=False,copy=False)
    #emloyee_medical = fields.One2many('hr.employee_medical_records','employee_med_rec_id', readonly=False,copy=False)
    #employee_licenses = fields.One2many('hr.employeelicenses','employee_licenses_id', readonly=False,copy=False)
    #employee_employment = fields.One2many('hr.employmenthistory','employee_employment_id', readonly=False,copy=False)

    def getFullname(self):
        if self.first_name == False:
           self.first_name=''
        if self.middle_name == False:
           self.middle_name=''
        if self.last_name == False:
           self.last_name=''

        self.name_related = self.first_name + " " +  self.middle_name + " " + self.last_name

class HrEmployeeExtend(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee']
    _description = 'Extension of Employee Information in Recruitment Process'

    #---------------- Functions/Methods
    def getCheckListId(self):

        #checklistTemplates = self.env['hr.checklist_template'].search([])
        #employeeChecklist = self.env['hr.employee_checklist']
        SQL_QUERY ="SELECT id,1 employee_id ,id checklist_template_id"\
                   " FROM hr_checklist_template;"

        self.env.cr.execute(SQL_QUERY)
        checklistTemplates = self.env.cr.fetchall()
        #raise Warning(checklistTemplates)

        return checklistTemplates

    # Overrides
    @api.multi
    def write(self, vals):

        super(HrEmployeeExtend, self).write(vals)

        checklistTemplates = self.env['hr.checklist_template'].search([])
        employeeChecklist = self.env['hr.employee_checklist'].search([])

        for checklistTemplate in checklistTemplates:

            if len(checklistTemplate.checklist_temp_param_1) > 0:
                temp_1 = int(checklistTemplate.checklist_temp_param_1[0])
            else:
                temp_1 = None

            if len(checklistTemplate.checklist_temp_param_2) > 0:
                temp_2 = int(checklistTemplate.checklist_temp_param_2[0])
            else:
                temp_2 = None

            if len(checklistTemplate.checklist_temp_param_3) > 0:
                temp_3 = int(checklistTemplate.checklist_temp_param_3[0])
            else:
                temp_3 = None

            count_Template = self.env['hr.employee_checklist'].search_count([('checklist_template_id', '=', checklistTemplate.id),
                                                                             ('employee_id', '=', self.id)])
            if count_Template == 0:
                employeeChecklist.create({
                    'employee_id': self.id,
                    'checklist_template_id': checklistTemplate.id,
                    'param_name_1': temp_1,
                    'param_name_1_value': '',
                    'param_name_1_check': False,
                    'param_name_2': temp_2,
                    'param_name_2_value': '',
                    'param_name_2_check': False,
                    'param_name_3': temp_3,
                    'param_name_3_value': '',
                    'param_name_3_check': False,
                    'param_name_1_value_visible':  checklistTemplate.checklist_temp_param_1_with_value,
                    'param_name_2_value_visible':  checklistTemplate.checklist_temp_param_2_with_value,
                    'param_name_3_value_visible':  checklistTemplate.checklist_temp_param_3_with_value})
        return True

    # End Override Functions

    @api.model
    def _getEmpId(self):

        cr = self._cr
        uid = self._uid
        context =self._context
        obj_sequence = self.pool.get('ir.sequence')
        return obj_sequence.next_by_code(cr, uid, 'hr.employee.sequence', context=context)

    @api.onchange('first_name','middle_name','last_name')
    def getFullname(self):
        if self.first_name == False:
            self.first_name=''
        if self.middle_name == False:
            self.middle_name=''
        if self.last_name == False:
            self.last_name=''
        self.name_related = self.first_name + " " + self.middle_name + " " + self.last_name
        self.name = self.first_name + " " + self.middle_name + " " + self.last_name

    @api.onchange('employee_employment')
    def computeServiceLenght(self):
        totalyears = 0
        getEmployments = self.employee_employment
        for getEmployment in getEmployments:
            #employmenthistory = self.env['hr.employmenthistory'].search([('id', '=', getEmployments.id)])
            if isinstance(getEmployment.id, models.NewId):
                if getEmployment.date_servicefrom != False and getEmployment.date_serviceto != False:
                    date_from = datetime.datetime.strptime(getEmployment.date_servicefrom ,"%Y-%m-%d")
                    date_to = datetime.datetime.strptime(getEmployment.date_serviceto ,"%Y-%m-%d")
                    no_of_days =(((abs((date_to - date_from).days) * 24) * 60) * 60)
                    self.service_length = self.service_length + no_of_days

    def getEmployeeID(self):
        prim_key = None
        empids = self.env['hr.employee'].search([('employee_number', '=', self.employee_number)])
        if len(empids) >0:
            prim_key = int(empids[0])
        else:
            prim_key = 0
        self.employee_id = prim_key
        return prim_key

    @api.one
    def getdocumentStatus(self):
        server_date = datetime.datetime.strptime(DATE_NOW.strftime("%Y-%m-%d") ,"%Y-%m-%d")
        totaldoc = self.env['hr.employee_documents'].search_count([('date_expiry', '<', server_date),('employee_doc_id','=', self.id)])

        if totaldoc > 0:
            self.documents_status = True
        else:
            self.documents_status = False

    @api.one
    def getMedicalStatus(self):
        server_date = datetime.datetime.strptime(DATE_NOW.strftime("%Y-%m-%d") ,"%Y-%m-%d")
        totaldoc = self.env['hr.employee_medical_records'].search_count([('date_to', '<', server_date),('employee_med_rec_id','=', self.id)])

        if totaldoc > 0:
            self.medical_status = True
        else:
            self.medical_status = False

    @api.one
    def legacy_doc1_getFilename(self):

        if len(self.employee_number) > 0:
            self.filename = self.employee_number + '_ConfidentialReports.pdf'
        else:
            self.filename = 'filename_ConfidentialReports.pdf'

    @api.one
    def legacy_doc2_getFilename(self):

        if len(self.employee_number) > 0:
            self.filename2 = self.employee_number + '_PersonalData.pdf'
        else:
            self.filename2 = 'filename_PersonalData.pdf'

    @api.one
    def legacy_doc3_getFilename(self):

        if len(self.employee_number) > 0:
            self.filename3 = self.employee_number + '_PersonalSummary.pdf'
        else:
            self.filename3 = 'filename_PersonalSummary.pdf'

    # End Functions/Methods


    #-------- Attributes/Fields
    employee_number = fields.Char('Employee Number',select = True, default = _getEmpId)
    first_name = fields.Char('First name', required = True)
    last_name = fields.Char('Last name', required = True)
    middle_name = fields.Char('Middle name')
    self_alotte = fields.Boolean('Self Allottee?', default = True)
    weight = fields.Char('Weight')
    height = fields.Char('Height')
    placeof_birth = fields.Char('Place of birth')
    sss_no = fields.Char('SSS No')
    hdmf_no = fields.Char('HDMF No')
    philhealth_no = fields.Char('Philhealth No')
    tin_no = fields.Char('Tin')
    aa_reg_no = fields.Char('AA Registry No')
    service_length = fields.Integer('Service Length')
    focllength = fields.Integer('Foclength')
    incentive_length = fields.Integer('Incentive Length')
    booking_id = fields.Char('Booking ID')
    bankacctno = fields.Text('Bank account number')
    checklistID = fields.Char('Checklist ID')
    ccl_number = fields.Char('CCL Number')
    religion = fields.Many2one('hr.religion', 'Religion')
    #employee_rank = fields.One2many('hr.rank','Rank')
    pcn = fields.Char('PCN')
    legacy_doc_1 = fields.Binary('Confidential Reports', filters='*.pdf,*.docx,*.doc')
    legacy_doc_2 = fields.Binary('Personal Data', filters='*.pdf,*.docx,*.doc')
    legacy_doc_3 = fields.Binary('Personal Summary', filters='*.pdf,*.docx,*.doc')
    employee_addresses = fields.One2many('hr.employeeaddress','employee_address_id', readonly=False,copy=False)
    employee_education = fields.One2many('hr.employeducation','employee_education_id', readonly=False,copy=False)
    employee_families = fields.One2many('hr.employee_families','employee_family_relationship_id', readonly=False,copy=False)
    employee_documents = fields.One2many('hr.employee_documents','employee_doc_id', readonly=False,copy=False)
    emloyee_medical = fields.One2many('hr.employee_medical_records','employee_med_rec_id', readonly=False,copy=False)
    employee_licenses = fields.One2many('hr.employeelicenses','employee_licenses_id', readonly=False,copy=False)
    employee_employment = fields.One2many('hr.employmenthistory','employee_employment_id', readonly=False,copy=False)
    employee_checklists = fields.One2many('hr.employee_checklist','employee_id', readonly=False,copy=False)
    employee_id = fields.Integer('employee_id', readonly=False,copy=False,store =False, compute='getEmployeeID')
    documents_status = fields.Boolean('Document status', readonly = True,store = False,compute ='getdocumentStatus')
    medical_status = fields.Boolean('Medical documents', readonly = True,store = False,compute ='getMedicalStatus')
    filename = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc1_getFilename')
    filename2 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc2_getFilename')
    filename3 = fields.Char('file name', readonly = True,store = False,compute ='legacy_doc3_getFilename')

class HrEmployeeAddresses(models.Model):
    _name = 'hr.employeeaddress'
    employee_address_id = fields.Many2one('hr.employee','Employee Addresses')
    addresstype = fields.Many2one('hr.addresstype','Address Type')
    address_1 = fields.Char('Address 1')
    address_2 = fields.Char('Address 2')
    address_3 = fields.Char('Address 3')
    city = fields.Char('City')
    province = fields.Char('Province')
    country = fields.Many2one('res.country', 'Country')
    telephone_number = fields.Char('Landline number')
    mobile_number = fields.Char('Mobile number')
    email_number = fields.Char('E-mail')

class HrEmployeeEducation(models.Model):
    _name = 'hr.employeducation'
    employee_education_id = fields.Many2one('hr.employee')
    schooltype = fields.Many2one('hr.recruitment.degree','Degree')
    name_school = fields.Char('School/College University')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    school_address = fields.Char('Place')
    description = fields.Text('Remarks')

    @api.onchange('date_to')
    def checkDate(self):
        if self.date_to < self.date_from:
            raise ValidationError('Date to is less than the Date from.')

    @api.constrains('date_to','date_from')
    def checkConstrainDate(self):
        if self.date_to < self.date_from:
            raise ValidationError('Date to is less than the Date from.')

class HrEmployeeFamilies(models.Model):
    _name = 'hr.employee_families'
    employee_family_relationship_id = fields.Many2one('hr.employee')
    relationship = fields.Many2one('hr.familyrelations','Relationship')
    address_1 = fields.Char('Address 1')
    address_2 = fields.Char('Address 2')
    address_3 = fields.Char('Address 3')
    is_beneficiary = fields.Boolean('Beneficiary', default = True)
    is_allottee = fields.Boolean('Allottee', default = True)
    is_living = fields.Boolean('Living', default = True)
    occupation = fields.Char('Occupation')
    bank_details = fields.Text('Bank Details')
    telephone_number = fields.Char('Landline number')
    mobile_number = fields.Char('Mobile number')
    email_number = fields.Char('E-mail')
    city = fields.Char('City')
    province = fields.Char('Province')
    country_id = fields.Many2one('res.country', 'Nationality')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], 'Gender')
    birthday = fields.Date("Date of Birth")
    full_name = fields.Char('Name', readonly=True)
    first_name = fields.Char('First name', required = True)
    last_name = fields.Char('Last name', required = True)
    middle_name = fields.Char('Middle name', required = True)
    placeof_birth = fields.Char('Place of birth')

class HrEmployeeDocuments(models.Model):
    _name = 'hr.employee_documents'

    _order = 'date_expiry,date_expiry,document'

    employee_doc_id =  fields.Many2one('hr.employee')
    document = fields.Many2one('hr.documenttype','Document Type')
    document_number = fields.Char('Document ID')
    date_issued = fields.Date('Date Issued',default = DATE_NOW)
    date_expiry = fields.Date('Date Expiry',default = DATE_NOW)
    issuing_authority = fields.Char('Issuing Authority')
    place_ofissue = fields.Char('Place of Issue')
    expired = fields.Char('Expired?',store = False,compute ='checkDocExpiration')

    @api.one
    def checkDocExpiration(self):
        server_date = datetime.datetime.strptime(DATE_NOW.strftime("%Y-%m-%d") ,"%Y-%m-%d")
        if (self.date_expiry == False):
            self.expired = 'NOT'
        else:
            dt_date_expiry = datetime.datetime.strptime(self.date_expiry ,"%Y-%m-%d")
            if dt_date_expiry < server_date:
                self.expired = 'EXP'
            else:
                self.expired = 'NOT'

    @api.onchange('date_expiry')
    def checkDate(self):
        if self.date_expiry < self.date_issued:
            raise ValidationError('Date expiry is less than the Date issued.')

    @api.constrains('date_issued','date_expiry' )
    def checkConstrainDate(self):
        if self.date_expiry < self.date_issued:
            raise ValidationError('Date expiry is less than the Date issued.')

    #@api.constrains('document')
    #def checkDocumentExists(self):
    #    #raise Warning(int(self.employee_doc_id[0]))
    #    if len(self.document) > 0:
    #        totaldoc = self.env['hr.employee_documents'].search_count([('document', '=', int(self.document)),
    #                                                                   ('employee_doc_id','=', int(self.employee_doc_id[0]))])
    #        if totaldoc > 0:
    #            raise Warning('Selected documents already exists.')

    #@api.one
    #@api.onchange('document')
    #def checkDocumentsExists(self):
        #raise Warning(int(self.employee_doc_id))
    #    raise Warning(int(self.employee_doc_id))
    #    if not isinstance(self.id, models.NewId):
    #        raise Warning(int(self.employee_doc_id))
    #        totaldoc = self.env['hr.employee_documents'].search_count([('document', '=', self.document),('employee_med_rec_id','=', int(self.employee_doc_id)),
    #                                                                    ('expired', '=', 'NOT')])
    #        if totaldoc > 0:
    #            raise ValidationError('Selected documents has already exists.')

class HrEmployeeMedicalRecords(models.Model):
    _name = 'hr.employee_medical_records'
    employee_med_rec_id = fields.Many2one('hr.employee')
    medical_type = fields.Many2one('hr.medicalrecord','Medical')
    medical_clinic = fields.Many2one('hr.clinic','Clinic')
    date_from = fields.Date('Date From',required = True)
    date_to = fields.Date('Date To',required = True)
    expired = fields.Char('Expired?',store = False,compute ='checkDocExpiration')

    #@api.constrains('date_from','date_to')
    #def checkConstrainDate(self):
    #    if self.date_to < self.date_from:
    #        raise ValidationError('Date to is less than the Date from.')

    @api.one
    def checkDocExpiration(self):
        server_date = datetime.datetime.strptime(DATE_NOW.strftime("%Y-%m-%d") ,"%Y-%m-%d")
        dt_date_expiry = datetime.datetime.strptime(self.date_to ,"%Y-%m-%d")
        if self.date_to == False:
            self.expired = 'NOT'
        else:
            if dt_date_expiry < server_date:
                self.expired = 'EXP'
            else:
                self.expired = 'NOT'

    @api.onchange('date_to')
    def checkDate(self):
        if self.date_to < self.date_from:
            raise ValidationError('Date to is less than the Date from.')

    #@api.constrains('medical_type')
    #def checkMedicalType(self):
    #    #raise Warning(int(self.employee_doc_id[0]))
    #    if len(self.medical_type) > 0:
    #        if self.env['hr.employee_medical_records'].search_count([ ('employee_med_rec_id','=', int(self.employee_med_rec_id[0]))]) > 0:
    #            totaldoc = self.env['hr.employee_medical_records'].search_count([('medical_type', '=', int(self.medical_type)),
    #                                                                       ('employee_med_rec_id','=', int(self.employee_med_rec_id[0]))])
    #            if totaldoc > 0:
    #                raise ValidationError('Selected Medical documents already exists.')

class HrEmployeeLicenses(models.Model):
    _name = 'hr.employeelicenses'

    employee_licenses_id = fields.Many2one('hr.employee')
    licensetype = fields.Many2one('hr.licensetype','License Type', required=True)
    license = fields.Many2one('hr.license','License', required=True)
    doc_number = fields.Char('Document Number', required=True)
    country = fields.Many2one('res.country', 'Country', required=True)
    date_issued = fields.Date('Issue', required=True)
    date_expiry = fields.Date('Expiry', required=True)
    place_issue = fields.Char('Place Issue', required=True)
    authority_issue = fields.Char('Authority Issue')
    remarks = fields.Text('Remarks')

    @api.constrains('date_issued','date_expiry')
    def checkConstrainDate(self):
        if self.date_expiry < self.date_issued:
            raise ValidationError('Date expiry is less than the Date issued.')

    @api.onchange('date_expiry')
    def checkDate(self):
        if self.date_expiry < self.date_issued:
            raise ValidationError('Date expiry is less than the Date issued.')

    @api.one
    @api.onchange('licensetype')
    def getlicense(self):
        if len(self.licensetype) > 0:
            mdlLicense= self.env['hr.license'].search([('license_name', '=', int(self.licensetype[0]))])
            #raise Warning(mdlLicense.ids)
            self.license = mdlLicense.ids

    @api.onchange('license')
    def getlicense(self):
        if len(self.licensetype) > 0:
            mdlLicense= self.env['hr.license'].search([('license_name', '=', int(self.licensetype[0]))])
            #raise Warning(mdlLicense.ids)
            return mdlLicense.ids

class HrEmployeeEmployment(models.Model):
    YEAR = 365
    MONTH = 30
    
    _name = 'hr.employmenthistory'
    employee_employment_id = fields.Many2one('hr.employee')
    date_departure =fields.Date('Departure Date')
    date_servicefrom =fields.Date('Service from')
    date_serviceto =fields.Date('Service to')
    object_name = fields.Char('Object')
    object_code = fields.Many2one('hr.vessel','Vessel', required =True)
    employment_dept_code = fields.Many2one('hr.ship.department','Department', required =True)
    employment_rank = fields.Many2one('hr.rank','Rank')
    employment_status = fields.Many2one('hr.employment.status','Status')
    remarks = fields.Text('Remarks')
    place_signOn = fields.Many2one('hr.port', 'Sign On')
    place_signOff = fields.Many2one('hr.port', 'Sign Off')
    service_range = fields.Char('Service range',store = False,compute ='getYearMonthDay')


    @api.one
    def getYearMonthDay(self):

        if self.date_servicefrom == False or self.date_serviceto == False:
            self.service_range = '0Y 0M 0D'
        else:
            date_from = datetime.datetime.strptime(self.date_servicefrom ,"%Y-%m-%d")
            date_to = datetime.datetime.strptime(self.date_serviceto ,"%Y-%m-%d")
            no_of_days = abs((date_to - date_from).days) + 1
            # Get Years of Service


            #raise Warning(no_of_days)
            no_of_years = abs(no_of_days/365)
            no_of_days =  no_of_days - (no_of_years * 365)
            no_of_months = abs(no_of_days/30)
            no_of_days = no_of_days - (no_of_months * 30)
            no_of_day = no_of_days

            self.service_range = str(no_of_years) + 'Y ' + str(no_of_months) + 'M ' +  str(no_of_day)  + 'D'

    @api.onchange('date_servicefrom')
    def checkDate(self):
        if self.date_servicefrom < self.date_departure:
            raise ValidationError('Date service from is less than the Departure date.')

    @api.onchange('date_serviceto')
    def checkDate(self):
        if self.date_serviceto < self.date_servicefrom:
            raise ValidationError('Date service to is less than the Date service from.')

    @api.constrains('date_servicefrom')
    def checkConstrainDate(self):
        if self.date_servicefrom < self.date_departure:
            raise ValidationError('Date service from is less than the Date departure.')

    @api.constrains('date_serviceto')
    def checkConstrainDate(self):
        if self.date_serviceto < self.date_servicefrom:
            raise ValidationError('Date service to is less than the Date service from.')

class EmployeeCheckList(models.Model):
    _name = 'hr.employee_checklist'
    employee_id = fields.Many2one('hr.employee')
    checklist_template_id = fields.Many2one('hr.checklist_template')

    param_name_1 = fields.Many2one('hr.checklist', 'Parameter 1')
    param_name_2 = fields.Many2one('hr.checklist', 'Parameter 2')
    param_name_3 = fields.Many2one('hr.checklist', 'Parameter 3')

    param_name_1_value = fields.Char("Parameter 1 value")
    param_name_2_value = fields.Char("Parameter 2 value")
    param_name_3_value = fields.Char("Parameter 3 value")

    param_name_1_check = fields.Boolean("Parameter 1 Checked?")
    param_name_2_check = fields.Boolean("Parameter 2 Checked?")
    param_name_3_check = fields.Boolean("Parameter 3 Checked?")

    param_name_1_value_visible = fields.Boolean("Parameter 1 Value visible?")
    param_name_2_value_visible = fields.Boolean("Parameter 2 Value visible?")
    param_name_3_value_visible = fields.Boolean("Parameter 3 Value visible?")

    issued_at = fields.Char("Issued at")
    date_issued = fields.Date("Date issued")
    date_expiry = fields.Date("Date Expiry")

    @api.onchange('date_expiry')
    def checkDate(self):
        if self.date_expiry < self.date_issued:
            raise ValidationError('Date expiry is less than the Date issued.')

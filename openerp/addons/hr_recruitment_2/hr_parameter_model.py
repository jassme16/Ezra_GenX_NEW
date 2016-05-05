# -*- coding: utf-8 -*-
from openerp import models, fields,api
from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError


#Abstract Implementation

class ParameterModel(models.AbstractModel):
    _name ='hr.abs.parameter'
    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')


#Models
class AddressType(models.Model):
    _name = 'hr.addresstype'
    name = fields.Char('Address Type', required = True)
    description = fields.Text('Description')

    _sql_constraints = [
        ('hr_addresstype_name',
        'UNIQUE (name)',
        'Address Type must be unique!')]



class EducationType(models.Model):
    _name = 'hr.educationtype'
    name = fields.Char('Education')
    description = fields.Text('Description')

class DocumentType(models.Model):
    _name = 'hr.documenttype'
    abbreviation = fields.Char('Code', required =True)
    name = fields.Char('Document name', required=True)
    description = fields.Text('Full Description')

    _sql_constraints = [
        ('hr_documenttype_name',
        'UNIQUE (abbreviation)',
        'Code must be unique!')]

class FamilyRelations(models.Model):
    _name = 'hr.familyrelations'
    code = fields.Char('Code', required =True)
    name = fields.Char('Relationship', required=True)
    description = fields.Text('Description')

    _sql_constraints = [
        ('hr_familyrelations_name',
        'UNIQUE (code,name)',
        'Family relation must be unique!')]

class MedicalRecordType(models.Model):
    _name = 'hr.medicalrecord'
    code = fields.Char('Code', required =True)
    name = fields.Char('Medical', required =True)
    description = fields.Text('Description')

    _sql_constraints = [
        ('hr_medicalrecord_name',
        'UNIQUE (code,name)',
        'Medical record type must be unique!')]

class LicenseType(models.Model):
    _name ='hr.licensetype'

    @api.model
    def _getClassID(self):

        cr = self._cr
        uid = self._uid
        context =self._context
        obj_sequence = self.pool.get('ir.sequence')
        return obj_sequence.next_by_code(cr, uid, 'hr.licensetype.sequence', context=context)

    #id_name = fields.Integer('Class ID', default=_getClassID)
    id_name = fields.Char('Class ID', default=_getClassID)
    name = fields.Char('Class Name', required =True)


    _sql_constraints = [
        ('hr_medicalrecord_name_uniq',
        'UNIQUE (id_name)',
        'License type must be unique')]

class License(models.Model):
    _name = 'hr.license'
    id_class_name = fields.Integer('Class ID')
    license_name = fields.Many2one('hr.licensetype','Class Name', required=True)
    name = fields.Char('Doc Abbreviation', required=True)
    doc_description = fields.Text('Doc Full Description')

    _sql_constraints = [
        ('hr_license_name_uniq',
        'UNIQUE (id_class_name,name)',
        'License must be unique')]

class MedicalClinic(models.Model):
    _name = 'hr.clinic'
    _inherit = 'hr.documenttype'
    _sql_constraints = [
        ('hr_clinic_name_uniq',
        'UNIQUE (abbreviation,name)',
        'Clinic name must be unique!')]

class LengthOfExpiration(models.Model):
    _name = 'hr.lengthofexpiration'
    _inherit = 'hr.familyrelations'
    days = fields.Integer('Days before Expiration')

    _sql_constraints = [
        ('hr_lengthofexp_name_uniq',
        'UNIQUE (abbreviation,name)',
        'Length of expiration must be unique!')]

class PortInformation(models.Model):
    _name = 'hr.port'
    _inherit = 'hr.abs.parameter'

    _sql_constraints = [
        ('hr_port_name_uniq',
        'UNIQUE (code, name)',
        'Port must be unique!')]

class Companies(models.Model):
    _name = 'hr.companies'
    _inherit = 'hr.abs.parameter'

    _sql_constraints = [
        ('hr_company_name_uniq',
        'UNIQUE (code, name)',
        'Port must be unique!')]

class VesselCategory(models.Model):
    _name = 'hr.vesselcategory'
    category = fields.Char('Category', required=True)
    name = fields.Char('Name', required=True)
    vessel_cat_ids = fields.Many2many('hr.ship.department','department_vessel_rel', 'vessel_cat_id','department_id')

    _sql_constraints = [
        ('hr_vesselcat_name_uniq',
        'UNIQUE (category,name)',
        'Vessel category must be unique!')]

class Vessel(models.Model):
    _name = 'hr.vessel'
    _inherit ='hr.abs.parameter'
    company_code = fields.Many2one('hr.companies', 'Company', required =True)
    vessel_category = fields.Many2one('hr.vesselcategory','Category', required =True)

    _sql_constraints = [
        ('hr_vessel_name_uniq',
        'UNIQUE (code,name,vessel_category,company_code)',
        'Vessel must be unique!')]

class RankType(models.Model):
    _name = 'hr.ranktype'
    _inherit = 'hr.abs.parameter'
    rate = fields.Float('Incentive Rate',digits=(18,2))

    _sql_constraints = [
        ('hr_ranktype_name_uniq',
        'UNIQUE (code,name)',
        'Rank type must be unique!')]

class Rank(models.Model):
    _name = 'hr.rank'
    rank_identification = fields.Char('Rank ID')
    rank = fields.Char('Rank')
    name= fields.Char('Name')
    rank_type = fields.Many2one('hr.ranktype', 'Rank Type')

    _sql_constraints = [
        ('hr_rank_name_uniq',
        'UNIQUE (rank_identification,name,rank_type)',
        'Rank must be unique!')]

    #rank_department_ids = fields.Many2many('hr.ship.department', 'dep_rank_rel','rank_department_id','department_rank_id','Departments')
    #rank_ids = fields.Many2many('hr.ranktype','rank_type_rel', 'rank_id','ship_code_id')

class ShipDepartment(models.Model):
    _name = 'hr.ship.department'
    ship_dept_code = fields.Char('Code', required=True)
    name = fields.Char('Department', required=True)
    #department_rank_ids = fields.Many2many('ranktype','dep_rank_rel','department_rank_id','rank_department_id')
    department_ids = fields.Many2many('hr.vesselcategory','department_vessel_rel', 'department_id','vessel_cat_id')

    _sql_constraints = [
        ('hr_shipdep_name_uniq',
        'UNIQUE (ship_dept_code,name,department_ids)',
        'Ship Department must be unique!')]

class Status(models.Model):
    _name = 'hr.employment.status'
    status_id = fields.Char('Status ID')
    name = fields.Text('Description', required=True)

    _sql_constraints = [
        ('hr_empstat_name_uniq',
        'UNIQUE (status_id,name)',
        'Rank must be unique!')]

class CheckList(models.Model):
    _name= 'hr.checklist'
    checklist_code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('hr_chekclist_name_uniq',
        'UNIQUE (checklist_code,name)',
        'Checklist must be unique!')]


class religion(models.Model):
    _name= 'hr.religion'
    religion_code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)

    _sql_constraints = [
        ('hr_religion_code_uniq',
        'UNIQUE (religion_code)',
        'Checklist must be unique!')]


class ChecklistTemplate(models.Model):
    _name = 'hr.checklist_template'
    _order =  'csequence'
    checklist_temp_code = fields.Char('Code')
    name = fields.Char('Name')
    checklist_temp_param_1 = fields.Many2one('hr.checklist', 'Parameter 1')
    checklist_temp_param_1_with_value = fields.Boolean('With Value')

    checklist_temp_param_2 = fields.Many2one('hr.checklist', 'Parameter 2')
    checklist_temp_param_2_with_value = fields.Boolean('With Value')

    checklist_temp_param_3 = fields.Many2one('hr.checklist', 'Parameter 3')
    checklist_temp_param_3_with_value = fields.Boolean('With Value')
    csequence = fields.Integer("Sequence", default = 0)


    @api.model
    def create(self, vals):
        if vals['csequence'] == False:
            raise Warning('No Checklist template sequence define.')

        if vals['name'] == False:
            raise Warning('No Checklist template name define.')
        #raise Warning(vals)
        new_record = super(ChecklistTemplate, self).create(vals)

        return new_record

    _sql_constraints = [
        ('hr_chekclist_name_uniq',
        'UNIQUE (name,name)',
        'Template name must be unique!')]


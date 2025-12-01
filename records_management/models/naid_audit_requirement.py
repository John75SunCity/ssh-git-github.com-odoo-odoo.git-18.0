# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class NAIDAuditRequirement(models.Model):
    _name = 'naid.audit.requirement'
    _description = 'NAID AAA Audit Requirement & Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'next_audit_date, frequency_months, audit_type'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Audit Requirement Name',
        required=True,
        help='Name of the NAID AAA audit requirement'
    )
    audit_type = fields.Selection([
        ('certification', 'NAID AAA Certification Audit'),
        ('internal', 'Internal Compliance Audit'),
        ('compliance', 'Regulatory Compliance Review'),
        ('security', 'Security Assessment'),
        ('performance', 'Performance Review'),
        ('surprise', 'Surprise Audit')
    ], string='Audit Type', required=True, default='internal')

    frequency_months = fields.Integer(
        string='Audit Frequency (Months)',
        required=True,
        default=12,
        help='How often this audit must be performed (NAID AAA requires annual audits)'
    )

    # Audit Details
    scope = fields.Text(
        string='Audit Scope',
        help='Description of what areas and processes this audit covers'
    )
    auditor_requirements = fields.Text(
        string='Auditor Requirements',
        help='Qualifications and requirements for auditors performing this audit'
    )
    documentation_requirements = fields.Text(
        string='Documentation Requirements',
        help='Documentation that must be available and reviewed during audit'
    )

    # Survey Integration for Checklists
    survey_id = fields.Many2one(
        'survey.survey',
        string='Audit Checklist Template',
        help='Survey template containing the audit checklist questions'
    )

    # Quality Control Integration (only if quality module is installed)
    quality_check_id = fields.Many2one(
        'quality.check',
        string='Quality Check Template',
        help='Quality control template for automated audit checks (requires quality module)',
        ondelete='set null'  # Prevent errors if quality module is uninstalled
    )
    
    def _get_quality_module_installed(self):
        """Check if quality module is installed"""
        return self.env['ir.module.module'].search([
            ('name', '=', 'quality'),
            ('state', '=', 'installed')
        ], limit=1)

    # Calendar Integration for Scheduling
    calendar_event_ids = fields.One2many(
        'calendar.event',
        'audit_requirement_id',
        string='Scheduled Audit Events',
        help='Calendar events for scheduled audits'
    )

    # Project/Task Integration
    project_id = fields.Many2one(
        'project.project',
        string='Audit Project',
        help='Project for managing audit tasks and activities'
    )

    task_ids = fields.One2many(
        'project.task',
        'audit_requirement_id',
        string='Audit Tasks',
        help='Project tasks related to this audit requirement'
    )

    # Document Management Integration
    document_ids = fields.Many2many(
        'documents.document',
        'audit_requirement_document_rel',
        'audit_requirement_id',
        'document_id',
        string='Audit Documents',
        help='Documents related to this audit requirement'
    )

    # Sign Integration for Digital Signatures
    sign_template_id = fields.Many2one(
        'sign.template',
        string='Signature Template',
        help='Digital signature template for audit verification'
    )

    sign_request_ids = fields.One2many(
        'sign.request',
        'audit_requirement_id',
        string='Signature Requests',
        help='Digital signature requests for this audit'
    )

    # Automated Scheduling
    last_audit_date = fields.Date(
        string='Last Audit Date',
        help='Date when this audit was last performed'
    )
    next_audit_date = fields.Date(
        string='Next Audit Date',
        compute='_compute_next_audit_date',
        store=True,
        help='Calculated date when next audit is due'
    )

    # Status Tracking
    status = fields.Selection([
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue')
    ], string='Audit Status', default='pending', compute='_compute_status', store=True)

    # Checklist Categories based on NAID AAA Requirements
    checklist_category = fields.Selection([
        ('employee_screening', 'Employee Screening & Background Checks'),
        ('operational_security', 'Operational Security Protocols'),
        ('destruction_process', 'Destruction Process Standards'),
        ('facility_security', 'Facility Security & Access Control'),
        ('surveillance_systems', 'Surveillance & Monitoring Systems'),
        ('documentation_compliance', 'Documentation & Record Keeping'),
        ('equipment_maintenance', 'Equipment Maintenance & Calibration'),
        ('training_certification', 'Training & Certification Requirements'),
        ('emergency_procedures', 'Emergency Procedures & Response'),
        ('regulatory_compliance', 'Regulatory Compliance Verification'),
        ('chain_of_custody', 'Chain of Custody Procedures'),
        ('data_protection', 'Data Protection & Privacy'),
        ('vendor_management', 'Vendor & Supplier Management'),
        ('incident_response', 'Incident Response & Breach Notification')
    ], string='Checklist Category', required=True)

    # NAID AAA Specific Requirements
    requires_signature = fields.Boolean(
        string='Requires Digital Signature',
        default=True,
        help='Whether this audit item requires digital signature for completion'
    )

    critical_item = fields.Boolean(
        string='Critical Compliance Item',
        help='Items that are critical for NAID AAA certification'
    )

    # Signature and Notes
    last_verified_by_id = fields.Many2one(
        'res.users',
        string='Last Verified By',
        readonly=True,
        help='User who last verified this audit item'
    )

    last_verified_date = fields.Datetime(
        string='Last Verified Date',
        readonly=True,
        help='Date and time when this audit item was last verified'
    )

    verification_notes = fields.Text(
        string='Verification Notes',
        help='Notes from the last verification'
    )

    # Compliance Tracking
    compliance_score = fields.Float(
        string='Compliance Score (%)',
        compute='_compute_compliance_score',
        store=True,
        help='Current compliance score based on audit history'
    )

    days_since_last_audit = fields.Integer(
        string='Days Since Last Audit',
        compute='_compute_days_since_last_audit',
        store=True
    )

    # Audit Results
    audit_answer_ids = fields.One2many(
        'survey.user_input',
        'audit_requirement_id',
        string='Audit Responses',
        help='Survey responses from completed audits'
    )

    # Related Records
    related_audit_ids = fields.One2many(
        'naid.audit.log',
        'audit_requirement_id',
        string='Audit History'
    )

    # Active status
    active = fields.Boolean(string='Active', default=True)

    # Display name computation
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')

    @api.depends('name', 'audit_type', 'status')
    def _compute_display_name(self):
        for record in self:
            if record.audit_type and record.name:
                audit_type_display = dict(record._fields['audit_type'].selection).get(record.audit_type, record.audit_type)
                status_indicator = f" [{record.status.title()}]" if record.status != 'pending' else ""
                record.display_name = f"{record.name} ({audit_type_display}){status_indicator}"
            else:
                record.display_name = record.name or 'New Audit Requirement'

    @api.depends('last_audit_date', 'frequency_months')
    def _compute_next_audit_date(self):
        for record in self:
            if record.last_audit_date and record.frequency_months:
                record.next_audit_date = record.last_audit_date + timedelta(days=record.frequency_months * 30)
            else:
                record.next_audit_date = False

    @api.depends('next_audit_date')
    def _compute_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.next_audit_date:
                record.status = 'pending'
            elif record.next_audit_date < today:
                record.status = 'overdue'
            elif record.next_audit_date <= today + timedelta(days=30):
                record.status = 'scheduled'
            else:
                record.status = 'pending'

    @api.depends('last_audit_date')
    def _compute_days_since_last_audit(self):
        today = fields.Date.today()
        for record in self:
            if record.last_audit_date:
                record.days_since_last_audit = (today - record.last_audit_date).days
            else:
                record.days_since_last_audit = 0

    @api.depends('related_audit_ids', 'critical_item')
    def _compute_compliance_score(self):
        for record in self:
            if not record.related_audit_ids:
                record.compliance_score = 0.0
                continue

            # Calculate compliance based on audit results
            total_audits = len(record.related_audit_ids)
            passed_audits = len(record.related_audit_ids.filtered(lambda a: a.result == 'pass'))

            if record.critical_item:
                # Critical items must have 100% pass rate
                record.compliance_score = 100.0 if passed_audits == total_audits else 0.0
            else:
                # Non-critical items can have some failures
                record.compliance_score = (passed_audits / total_audits) * 100.0 if total_audits > 0 else 0.0

    def action_schedule_audit(self):
        """Schedule the next audit"""
        self.ensure_one()
        if not self.survey_id:
            raise ValidationError(_("Please configure an audit checklist template first."))

        # Create survey session
        survey_action = {
            'name': f'Audit: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'survey.survey',
            'view_mode': 'form',
            'res_id': self.survey_id.id,
            'target': 'current',
        }
    def action_schedule_calendar_event(self):
        """Schedule a calendar event for this audit"""
        self.ensure_one()
        return {
            'name': f'Schedule Audit: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'Audit: {self.name}',
                'default_audit_requirement_id': self.id,
                'default_start': self.next_audit_date,
                'default_stop': self.next_audit_date,
                'default_duration': 2.0,  # 2 hours default
                'default_description': self.scope,
            }
        }

    def action_create_project_task(self):
        """Create a project task for this audit requirement"""
        self.ensure_one()

        # Create or get audit project
        if not self.project_id:
            project = self.env['project.project'].create({
                'name': f'Audit Project: {self.name}',
                'description': self.scope,
                'user_id': self.env.user.id,
            })
            self.project_id = project.id

        return {
            'name': f'Audit Task: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'Audit: {self.name}',
                'default_project_id': self.project_id.id,
                'default_audit_requirement_id': self.id,
                'default_description': self.scope,
                'default_date_deadline': self.next_audit_date,
                'default_user_ids': [(6, 0, [self.env.user.id])],
            }
        }

    def action_create_sign_request(self):
        """Create a digital signature request for audit verification"""
        self.ensure_one()

        if not self.sign_template_id:
            raise ValidationError(_("Please configure a signature template first."))

        return {
            'name': f'Signature Request: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'sign.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.sign_template_id.id,
                'default_audit_requirement_id': self.id,
                'default_subject': f'Audit Verification: {self.name}',
                'default_message': f'Please sign to verify completion of: {self.scope}',
            }
        }

    def action_create_quality_check(self):
        """Create a quality check for this audit requirement (requires quality module)"""
        self.ensure_one()
        
        # Check if quality module is installed
        if not self._get_quality_module_installed():
            raise ValidationError(_("Quality module is not installed. Please install it to use quality checks."))

        if not self.quality_check_id:
            raise ValidationError(_("Please configure a quality check template first."))

        return {
            'name': f'Quality Check: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.check',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'Audit Check: {self.name}',
                'default_quality_check_id': self.quality_check_id.id,
                'default_audit_requirement_id': self.id,
                'default_note': self.scope,
            }
        }

    def action_view_documents(self):
        """View documents related to this audit requirement"""
        self.ensure_one()
        return {
            'name': f'Audit Documents: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'documents.document',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.document_ids.ids)],
            'context': {
                'default_audit_requirement_ids': [(6, 0, [self.id])],
                'search_default_audit_requirement_id': self.id,
            }
        }

    def action_create_maintenance_request(self):
        """Create a maintenance request for equipment-related audit items"""
        self.ensure_one()

        if self.checklist_category != 'equipment_maintenance':
            raise ValidationError(_("This action is only available for equipment maintenance audit items."))

        return {
            'name': f'Maintenance Request: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'Audit: {self.name}',
                'default_description': self.scope,
                'default_maintenance_type': 'preventive',
                'default_audit_requirement_id': self.id,
            }
        }
        """Mark checklist item as verified with signature and notes"""
        self.ensure_one()

        return {
            'name': f'Verify: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'naid.audit.verification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_audit_requirement_id': self.id,
                'default_checklist_category': self.checklist_category,
            }
        }

    def action_view_audit_reports(self):
        """View audit reports and compliance history"""
        self.ensure_one()
        return {
            'name': f'Audit Reports: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'naid.audit.log',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('audit_requirement_id', '=', self.id)],
            'context': {'default_audit_requirement_id': self.id},
        }

    def _setup_default_checklist_items(self):
        """Create comprehensive NAID AAA checklist items based on official requirements"""
        default_items = [
            # Employee Screening & Background Checks
            {
                'name': 'Employee Background Checks & Drug Screenings',
                'checklist_category': 'employee_screening',
                'scope': 'Verify all employees have current background checks, drug screenings, and reference checks as required by NAID AAA',
                'frequency_months': 12,
                'critical_item': True,
                'documentation_requirements': 'Background check reports, drug screening results, reference check documentation'
            },
            {
                'name': 'Employee Training Records',
                'checklist_category': 'employee_screening',
                'scope': 'Verify all employees have completed required NAID training and maintain current certifications',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Training certificates, attendance records, certification renewals'
            },

            # Operational Security Protocols
            {
                'name': 'Security Policies & Procedures Review',
                'checklist_category': 'operational_security',
                'scope': 'Review and verify all security policies are current, documented, and being followed',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Security policy documents, procedure manuals, policy acknowledgment forms'
            },
            {
                'name': 'Chain of Custody Procedures',
                'checklist_category': 'chain_of_custody',
                'scope': 'Verify chain of custody procedures are followed for all document handling from pickup to destruction',
                'frequency_months': 3,
                'critical_item': True,
                'documentation_requirements': 'Chain of custody logs, transfer documentation, destruction certificates'
            },

            # Facility Security & Access Control
            {
                'name': 'Access Control Systems',
                'checklist_category': 'facility_security',
                'scope': 'Verify all access control systems are operational and properly configured',
                'frequency_months': 1,
                'critical_item': True,
                'documentation_requirements': 'Access logs, system maintenance records, security system tests'
            },
            {
                'name': 'Visitor Log Management',
                'checklist_category': 'facility_security',
                'scope': 'Review visitor logs and verify all visitors were properly escorted and logged',
                'frequency_months': 1,
                'critical_item': False,
                'documentation_requirements': 'Visitor logs, escort records, visitor badges'
            },
            {
                'name': 'Alarm System Testing',
                'checklist_category': 'facility_security',
                'scope': 'Test all alarm systems and verify they are functioning properly',
                'frequency_months': 1,
                'critical_item': True,
                'documentation_requirements': 'Alarm test logs, maintenance records, system status reports'
            },

            # Surveillance & Monitoring Systems
            {
                'name': 'CCTV System Verification',
                'checklist_category': 'surveillance_systems',
                'scope': 'Verify CCTV systems are operational and recording minimum 90 days of footage as required',
                'frequency_months': 3,
                'critical_item': True,
                'documentation_requirements': 'CCTV maintenance logs, storage capacity reports, footage retention verification'
            },
            {
                'name': 'Surveillance System Maintenance',
                'checklist_category': 'surveillance_systems',
                'scope': 'Verify all surveillance equipment is properly maintained and calibrated',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Maintenance records, calibration reports, system performance logs'
            },

            # Equipment Maintenance & Calibration
            {
                'name': 'Destruction Equipment Maintenance',
                'checklist_category': 'equipment_maintenance',
                'scope': 'Verify all destruction equipment is properly maintained and meets safety standards',
                'frequency_months': 3,
                'critical_item': True,
                'documentation_requirements': 'Maintenance logs, inspection reports, safety certifications'
            },
            {
                'name': 'Equipment Calibration Records',
                'checklist_category': 'equipment_maintenance',
                'scope': 'Verify all equipment calibration is current and documented',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Calibration certificates, test reports, calibration schedules'
            },

            # Emergency Procedures & Response
            {
                'name': 'Emergency Response Procedures',
                'checklist_category': 'emergency_procedures',
                'scope': 'Review emergency procedures and verify staff training and readiness',
                'frequency_months': 12,
                'critical_item': False,
                'documentation_requirements': 'Emergency procedures manual, training records, drill reports'
            },
            {
                'name': 'Incident Response Plan',
                'checklist_category': 'incident_response',
                'scope': 'Verify incident response plan is current and staff are trained',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Incident response plan, training records, incident logs'
            },

            # Documentation & Record Keeping
            {
                'name': 'Destruction Certificates',
                'checklist_category': 'documentation_compliance',
                'scope': 'Verify all destruction activities have proper certificates issued',
                'frequency_months': 1,
                'critical_item': True,
                'documentation_requirements': 'Destruction certificates, client acknowledgments, record retention logs'
            },
            {
                'name': 'Regulatory Compliance Documentation',
                'checklist_category': 'regulatory_compliance',
                'scope': 'Verify compliance with all applicable regulations (FACTA, GLBA, etc.)',
                'frequency_months': 12,
                'critical_item': True,
                'documentation_requirements': 'Compliance checklists, regulatory filings, audit reports'
            },

            # Data Protection & Privacy
            {
                'name': 'Data Protection Procedures',
                'checklist_category': 'data_protection',
                'scope': 'Verify data protection and privacy procedures are followed',
                'frequency_months': 6,
                'critical_item': True,
                'documentation_requirements': 'Privacy policy, data handling procedures, breach notification logs'
            },

            # Vendor & Supplier Management
            {
                'name': 'Vendor Security Assessments',
                'checklist_category': 'vendor_management',
                'scope': 'Verify vendor security assessments and contracts are current',
                'frequency_months': 12,
                'critical_item': False,
                'documentation_requirements': 'Vendor assessments, security agreements, performance reviews'
            }
        ]

        for item_data in default_items:
            self.create(item_data)

    @api.model
    def create_default_naid_checklist(self):
        """
        Create the complete NAID AAA audit checklist with default items.

        This method initializes the system with a comprehensive set of audit requirements
        based on NAID AAA certification standards. It creates checklist items covering
        all critical areas including employee screening, operational security, facility
        security, surveillance systems, equipment maintenance, emergency procedures,
        documentation compliance, regulatory requirements, data protection, and vendor
        management.

        The method checks if any audit requirements already exist to avoid duplication.
        If no existing items are found, it calls _setup_default_checklist_items() to
        populate the database with predefined NAID AAA compliant checklist items.

        Logs the creation of the checklist for audit and debugging purposes.

        :return: None
        :raises: None (handles logging internally)
        """
        existing = self.search([])
        if not existing:
            self._setup_default_checklist_items()
            _logger.info("Created default NAID AAA audit checklist with %d items", len(self.search([])))

    def action_mark_verified(self):
        """Mark the checklist item as verified"""
        self.ensure_one()
        self.write({
            'last_verified_by_id': self.env.user.id,
            'last_verified_date': fields.Datetime.now(),
            'last_audit_date': fields.Date.today(),
            'status': 'completed'
        })

        # Create audit log entry
        self.env['naid.audit.log'].create({
            'audit_requirement_id': self.id,
            'audit_date': fields.Date.today(),
            'auditor_id': self.env.user.id,
            'result': 'pass',
            'notes': self.verification_notes or 'Verified through checklist process',
            'checklist_category': self.checklist_category,
        })

        return True

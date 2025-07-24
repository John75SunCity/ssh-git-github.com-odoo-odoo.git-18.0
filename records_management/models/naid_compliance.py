# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class NAIDCompliance(models.Model):
    _name = 'naid.compliance'
    _description = 'NAID Compliance Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # Core identification fields
    name = fields.Char(string='Compliance Record Name', required=True, tracking=True)
    naid_member_id = fields.Char(string='NAID Member ID', required=True, tracking=True)
    facility_name = fields.Char(string='Facility Name', required=True, tracking=True)
    facility_manager = fields.Many2one('res.users', string='Facility Manager', tracking=True)
    
    # Compliance status and scoring
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('pending', 'Pending Review'),
        ('suspended', 'Suspended')
    ], string='Compliance Status', default='pending', required=True, tracking=True)
    
    overall_compliance_score = fields.Float(string='Overall Compliance Score', compute='_compute_compliance_scores')
    physical_security_score = fields.Float(string='Physical Security Score', tracking=True)
    operational_score = fields.Float(string='Operational Score', tracking=True)
    documentation_score = fields.Float(string='Documentation Score', tracking=True)
    security_score = fields.Float(string='Security Score', tracking=True)
    
    # Audit management
    audit_required = fields.Boolean(string='Audit Required', default=True, tracking=True)
    audit_frequency = fields.Selection([
        ('annual', 'Annual'),
        ('biannual', 'Bi-Annual'),
        ('quarterly', 'Quarterly'),
        ('monthly', 'Monthly')
    ], string='Audit Frequency', default='annual', tracking=True)
    
    last_audit_date = fields.Date(string='Last Audit Date', tracking=True)
    next_audit_date = fields.Date(string='Next Audit Date', compute='_compute_next_audit_date', store=True)
    audit_date = fields.Date(string='Current Audit Date', tracking=True)
    days_since_last_audit = fields.Integer(string='Days Since Last Audit', compute='_compute_audit_metrics')
    days_until_expiry = fields.Integer(string='Days Until Expiry', compute='_compute_audit_metrics')
    
    auditor_name = fields.Char(string='Auditor Name', tracking=True)
    third_party_auditor = fields.Boolean(string='Third Party Auditor', tracking=True)
    audit_result = fields.Text(string='Audit Result', tracking=True)
    audit_scope = fields.Text(string='Audit Scope')
    audit_type = fields.Selection([
        ('initial', 'Initial Certification'),
        ('renewal', 'Renewal'),
        ('surveillance', 'Surveillance'),
        ('special', 'Special Audit')
    ], string='Audit Type', tracking=True)
    
    # Certificate management
    certificate_required = fields.Boolean(string='Certificate Required', default=True)
    certificate_issued = fields.Boolean(string='Certificate Issued', tracking=True)
    certificate_valid = fields.Boolean(string='Certificate Valid', compute='_compute_certificate_status')
    certificate_number = fields.Char(string='Certificate Number', tracking=True)
    certificate_type = fields.Selection([
        ('naid_aaa', 'NAID AAA'),
        ('naid_aa', 'NAID AA'),
        ('naid_a', 'NAID A')
    ], string='Certificate Type', tracking=True)
    
    issue_date = fields.Date(string='Issue Date', tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    certification_date = fields.Date(string='Certification Date', tracking=True)
    issuing_authority = fields.Char(string='Issuing Authority', default='NAID')
    
    # Renewal and notifications
    auto_renewal = fields.Boolean(string='Auto Renewal', default=True)
    renewal_reminder = fields.Boolean(string='Renewal Reminder', default=True)
    expiry_notification = fields.Boolean(string='Expiry Notification', default=True)
    
    # Personnel and security
    security_officer = fields.Many2one('res.users', string='Security Officer', tracking=True)
    compliance_officer = fields.Many2one('res.users', string='Compliance Officer', tracking=True)
    responsible_person = fields.Many2one('res.users', string='Responsible Person', tracking=True)
    
    personnel_screening = fields.Boolean(string='Personnel Screening', default=True)
    background_checks = fields.Boolean(string='Background Checks', default=True)
    security_clearance = fields.Boolean(string='Security Clearance Required')
    training_completed = fields.Boolean(string='Training Completed', tracking=True)
    
    # Security and access control
    access_control_verified = fields.Boolean(string='Access Control Verified', tracking=True)
    surveillance_system = fields.Boolean(string='Surveillance System Active', default=True)
    secure_storage = fields.Boolean(string='Secure Storage Verified', default=True)
    equipment_certification = fields.Boolean(string='Equipment Certification', tracking=True)
    
    # Process verification
    process_verification = fields.Boolean(string='Process Verification', tracking=True)
    information_handling = fields.Boolean(string='Information Handling Compliant', default=True)
    quality_control = fields.Boolean(string='Quality Control', default=True)
    incident_management = fields.Boolean(string='Incident Management', default=True)
    
    # Missing technical view fields for XML processing
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    context = fields.Text(string='Context', help='View context information')
    help = fields.Text(string='Help', help='Help text for this record')
    model = fields.Char(string='Model', help='Model name for technical references')
    res_model = fields.Char(string='Resource Model', help='Resource model name')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View', help='Search view reference')
    view_mode = fields.Char(string='View Mode', help='View mode configuration')
    
    # Destruction tracking
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('incineration', 'Incineration'),
        ('pulverization', 'Pulverization'),
        ('disintegration', 'Disintegration')
    ], string='Destruction Method', tracking=True)
    
    destruction_verification = fields.Boolean(string='Destruction Verification', default=True)
    witness_present = fields.Boolean(string='Witness Present During Destruction', tracking=True)
    chain_of_custody = fields.Boolean(string='Chain of Custody Maintained', default=True)
    verification_method = fields.Text(string='Verification Method')
    
    # Material and client information
    material_type = fields.Selection([
        ('paper', 'Paper Documents'),
        ('electronic', 'Electronic Media'),
        ('mixed', 'Mixed Media')
    ], string='Material Type', tracking=True)
    
    client_name = fields.Many2one('res.partner', string='Client Name')
    naid_level = fields.Selection([
        ('aaa', 'NAID AAA'),
        ('aa', 'NAID AA'),
        ('a', 'NAID A')
    ], string='NAID Level', required=True, tracking=True)
    
    # Risk and compliance metrics
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='Risk Level', compute='_compute_risk_level', store=True)
    
    compliance_verified = fields.Boolean(string='Compliance Verified', tracking=True)
    last_verified = fields.Datetime(string='Last Verified', tracking=True)
    
    # Performance tracking
    score = fields.Float(string='Compliance Score', tracking=True)
    benchmark = fields.Float(string='Benchmark Score', default=85.0)
    variance = fields.Float(string='Variance from Benchmark', compute='_compute_variance')
    trend = fields.Selection([
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining')
    ], string='Trend', compute='_compute_trend')
    
    measurement_date = fields.Date(string='Measurement Date', default=fields.Date.today)
    metric_type = fields.Char(string='Metric Type', default='NAID Compliance')
    
    # Alerts and notifications
    compliance_alerts = fields.Boolean(string='Compliance Alerts Enabled', default=True)
    management_alerts = fields.Boolean(string='Management Alerts', default=True)
    regulatory_notifications = fields.Boolean(string='Regulatory Notifications', default=True)
    notification_recipients = fields.Many2many('res.users', string='Notification Recipients')
    escalation_contacts = fields.Many2many('res.users', string='Escalation Contacts')
    
    # One2many relationships
    audit_history_ids = fields.One2many('naid.audit.log', 'compliance_id', string='Audit History')
    certificate_ids = fields.One2many('naid.certificate', 'compliance_id', string='Certificates')
    destruction_record_ids = fields.One2many('destruction.item', 'naid_compliance_id', string='Destruction Records')
    performance_history_ids = fields.One2many('naid.performance.history', 'compliance_id', string='Performance History')
    compliance_checklist_ids = fields.One2many('naid.compliance.checklist', 'compliance_id', string='Compliance Checklist')
    
    # Computed counts
    audit_count = fields.Integer(string='Audit Count', compute='_compute_counts')
    certificate_count = fields.Integer(string='Certificate Count', compute='_compute_counts')
    destruction_count = fields.Integer(string='Destruction Count', compute='_compute_counts')
    findings_count = fields.Integer(string='Findings Count', compute='_compute_counts')
    
    # Status tracking fields
    certificate_status = fields.Char(string='Certificate Status', compute='_compute_certificate_status')
    certificate_tracking = fields.Boolean(string='Certificate Tracking Enabled', default=True)
    compliance_score = fields.Float(string='Current Compliance Score', tracking=True)
    compliance_trend = fields.Char(string='Compliance Trend', compute='_compute_trend')
    
    # Technical fields for view compatibility
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='naid.compliance')
    res_model = fields.Char(string='Resource Model', default='naid.compliance')
    context = fields.Text(string='Context')
    help = fields.Text(string='Help Text')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    view_mode = fields.Char(string='View Mode', default='tree,form')
    
    # Activity and message fields
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers')
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages')
    
    # Audit reminder
    audit_reminder = fields.Boolean(string='Audit Reminder Enabled', default=True)
    
    # Notes and additional information
    notes = fields.Text(string='Additional Notes')
    destruction_date = fields.Date(string='Last Destruction Date')
    
    # Missing fields for view compatibility
    requirement_name = fields.Char(string='Requirement Name', tracking=True,
                                   help='Name of the specific NAID requirement')
    requirement_type = fields.Selection([
        ('security', 'Security Requirement'),
        ('process', 'Process Requirement'),
        ('documentation', 'Documentation Requirement'),
        ('personnel', 'Personnel Requirement'),
        ('facility', 'Facility Requirement'),
        ('equipment', 'Equipment Requirement')
    ], string='Requirement Type', tracking=True,
       help='Type/category of the NAID requirement')
    
    # Company and user tracking
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)

    @api.depends('physical_security_score', 'operational_score', 'documentation_score', 'security_score')
    def _compute_compliance_scores(self):
        for record in self:
            scores = [
                record.physical_security_score or 0,
                record.operational_score or 0,
                record.documentation_score or 0,
                record.security_score or 0
            ]
            if any(scores):
                record.overall_compliance_score = sum(scores) / len([s for s in scores if s > 0])
            else:
                record.overall_compliance_score = 0.0

    @api.depends('last_audit_date', 'audit_frequency')
    def _compute_next_audit_date(self):
        for record in self:
            if record.last_audit_date and record.audit_frequency:
                from dateutil.relativedelta import relativedelta
                if record.audit_frequency == 'annual':
                    record.next_audit_date = record.last_audit_date + relativedelta(years=1)
                elif record.audit_frequency == 'biannual':
                    record.next_audit_date = record.last_audit_date + relativedelta(months=6)
                elif record.audit_frequency == 'quarterly':
                    record.next_audit_date = record.last_audit_date + relativedelta(months=3)
                elif record.audit_frequency == 'monthly':
                    record.next_audit_date = record.last_audit_date + relativedelta(months=1)
            else:
                record.next_audit_date = False

    @api.depends('last_audit_date', 'expiry_date')
    def _compute_audit_metrics(self):
        from datetime import date
        today = date.today()
        
        for record in self:
            if record.last_audit_date:
                record.days_since_last_audit = (today - record.last_audit_date).days
            else:
                record.days_since_last_audit = 0
                
            if record.expiry_date:
                record.days_until_expiry = (record.expiry_date - today).days
            else:
                record.days_until_expiry = 0

    @api.depends('certificate_issued', 'expiry_date')
    def _compute_certificate_status(self):
        from datetime import date
        today = date.today()
        
        for record in self:
            if record.certificate_issued and record.expiry_date:
                record.certificate_valid = record.expiry_date >= today
                if record.certificate_valid:
                    days_to_expiry = (record.expiry_date - today).days
                    if days_to_expiry <= 30:
                        record.certificate_status = 'Expiring Soon'
                    else:
                        record.certificate_status = 'Valid'
                else:
                    record.certificate_status = 'Expired'
            else:
                record.certificate_valid = False
                record.certificate_status = 'Not Issued'

    @api.depends('overall_compliance_score')
    def _compute_risk_level(self):
        for record in self:
            score = record.overall_compliance_score
            if score >= 90:
                record.risk_level = 'low'
            elif score >= 75:
                record.risk_level = 'medium'
            elif score >= 60:
                record.risk_level = 'high'
            else:
                record.risk_level = 'critical'

    @api.depends('score', 'benchmark')
    def _compute_variance(self):
        for record in self:
            if record.benchmark and record.score:
                record.variance = record.score - record.benchmark
            else:
                record.variance = 0.0

    @api.depends('variance')
    def _compute_trend(self):
        for record in self:
            if record.variance > 5:
                record.trend = 'improving'
                record.compliance_trend = 'Improving'
            elif record.variance < -5:
                record.trend = 'declining'
                record.compliance_trend = 'Declining'
            else:
                record.trend = 'stable'
                record.compliance_trend = 'Stable'

    @api.depends('audit_history_ids', 'certificate_ids', 'destruction_record_ids')
    def _compute_counts(self):
        for record in self:
            record.audit_count = len(record.audit_history_ids)
            record.certificate_count = len(record.certificate_ids)
            record.destruction_count = len(record.destruction_record_ids)
            record.findings_count = sum(audit.findings_count for audit in record.audit_history_ids)

    def action_schedule_audit(self):
        """Schedule the next audit"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Schedule Audit'),
            'res_model': 'naid.audit.scheduler',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_compliance_id': self.id}
        }

    def action_issue_certificate(self):
        """Issue a new certificate"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Issue Certificate'),
            'res_model': 'naid.certificate',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_compliance_id': self.id}
        }

    def action_verify_compliance(self):
        """Mark compliance as verified"""
        self.ensure_one()
        self.write({
            'compliance_verified': True,
            'last_verified': fields.Datetime.now(),
        })
        return True

    # Compute method for activity_ids One2many field
    @api.depends()
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "naid.compliance"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "naid.compliance"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "naid.compliance"),
                ("res_id", "=", record.id)
            ])

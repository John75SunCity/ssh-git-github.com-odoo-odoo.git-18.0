# -*- coding: utf-8 -*-
"""
Containeclass ContainerAccessWorkOrder(models.Model):
    _name = "container.access.work.order"
    _description = "Container Access Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.integration.mixin']
    _order = "priority desc, scheduled_date asc, name"
    _rec_name = "display_name"ss Work Order Module

This module manages work orders for temporary on-site access to records containers.
Supports various access scenarios including audits, inspections, relabeling, and
document review while maintaining chain of custody and security protocols.

Key Features:
- Temporary on-site access to containers without removal
- Multi-purpose access types (audit, inspection, relabeling, review)
- Chain of custody maintenance during access
- Time-limited access with automatic expiration
- Security escort and supervision requirements
- Integration with access control and key management
- Real-time monitoring and access logging

Business Processes:
1. Access Request Creation: Customer or internal request for container access
2. Authorization and Scheduling: Approve and schedule access appointments
3. Security Setup: Arrange escorts, keys, and security protocols
4. Access Session: Supervised access with continuous monitoring
5. Documentation: Record all activities and changes made
6. Session Completion: Secure containers and update custody records
7. Reporting: Generate access reports and audit documentation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerAccessWorkOrder(models.Model):
    _name = "container.access.work.order"
    _description = "Container Access Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "priority desc, scheduled_access_date asc, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Work Order Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
        help="Unique container access work order number"
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name for the work order"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary user responsible for this work order"
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # WORK ORDER STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'Access in Progress'),
        ('suspended', 'Access Suspended'),
        ('completed', 'Access Completed'),
        ('documented', 'Session Documented'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True,
       help="Current status of the container access work order")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
        ('4', 'Emergency Audit'),
    ], string='Priority', default='1', tracking=True,
       help="Work order priority level for processing")

    # ============================================================================
    # CUSTOMER AND REQUEST INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
        help="Customer requesting container access"
    )
    portal_request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Originating portal request if applicable"
    )
    requestor_name = fields.Char(
        string="Requestor Name",
        required=True,
        help="Name of person requesting access"
    )
    requestor_title = fields.Char(
        string="Requestor Title",
        help="Title/position of person requesting access"
    )
    access_purpose = fields.Text(
        string="Access Purpose",
        required=True,
        help="Detailed purpose for requesting container access"
    )

    # ============================================================================
    # ACCESS TYPE AND SCOPE
    # ============================================================================
    access_type = fields.Selection([
        ('audit', 'Audit/Compliance Review'),
        ('inspection', 'Document Inspection'),
        ('relabeling', 'Container Relabeling'),
        ('inventory', 'Physical Inventory'),
        ('quality_check', 'Quality Assessment'),
        ('legal_review', 'Legal Document Review'),
        ('maintenance', 'Container Maintenance'),
        ('other', 'Other (Specify in Purpose)'),
    ], string='Access Type', required=True,
       help="Type of access being requested")

    access_scope = fields.Selection([
        ('container_only', 'Container Exterior Only'),
        ('contents_view', 'View Contents Only'),
        ('contents_handle', 'Handle Contents (No Removal)'),
        ('limited_removal', 'Limited Item Removal'),
        ('full_access', 'Full Access'),
    ], string='Access Scope', default='contents_view', required=True,
       help="Scope of access to be granted")

    # ============================================================================
    # CONTAINERS AND LOCATIONS
    # ============================================================================
    container_ids = fields.Many2many(
        "records.container",
        "access_work_order_container_rel",
        "work_order_id",
        "container_id",
        string="Containers for Access",
        required=True,
        help="Containers requiring access"
    )
    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_metrics",
        store=True,
        help="Number of containers requiring access"
    )
    access_location_id = fields.Many2one(
        "records.location",
        string="Access Location",
        required=True,
        help="Physical location where access will take place"
    )

    # ============================================================================
    # SCHEDULING AND TIMING
    # ============================================================================
    scheduled_access_date = fields.Datetime(
        string="Scheduled Access Date",
        required=True,
        tracking=True,
        help="Planned start date/time for access"
    )
    scheduled_duration_hours = fields.Float(
        string="Scheduled Duration (Hours)",
        required=True,
        default=2.0,
        help="Expected duration of access session"
    )
    scheduled_end_time = fields.Datetime(
        string="Scheduled End Time",
        compute="_compute_scheduled_end_time",
        store=True,
        help="Calculated end time based on start time and duration"
    )
    
    # Actual timing
    actual_start_time = fields.Datetime(
        string="Actual Start Time",
        tracking=True,
        help="Actual time access session began"
    )
    actual_end_time = fields.Datetime(
        string="Actual End Time",
        tracking=True,
        help="Actual time access session ended"
    )
    actual_duration_hours = fields.Float(
        string="Actual Duration (Hours)",
        compute="_compute_actual_duration",
        store=True,
        help="Actual duration of access session"
    )

    # ============================================================================
    # SECURITY AND SUPERVISION
    # ============================================================================
    requires_escort = fields.Boolean(
        string="Requires Security Escort",
        default=True,
        help="Access requires security escort supervision"
    )
    escort_employee_id = fields.Many2one(
        "hr.employee",
        string="Security Escort",
        help="Employee providing security escort"
    )
    requires_key_access = fields.Boolean(
        string="Requires Key Access",
        default=True,
        help="Physical keys are required for container access"
    )
    bin_key_ids = fields.Many2many(
        "bin.key",
        "access_work_order_key_rel",
        "work_order_id",
        "key_id",
        string="Required Keys",
        help="Physical keys needed for container access"
    )
    
    # Visitor management
    visitor_ids = fields.One2many(
        "container.access.visitor",
        "work_order_id",
        string="Authorized Visitors",
        help="People authorized for this access session"
    )
    max_visitors = fields.Integer(
        string="Maximum Visitors",
        default=2,
        help="Maximum number of people allowed in access session"
    )

    # ============================================================================
    # ACCESS ACTIVITIES AND DOCUMENTATION
    # ============================================================================
    access_activity_ids = fields.One2many(
        "container.access.activity",
        "work_order_id",
        string="Access Activities",
        help="Record of activities performed during access"
    )
    items_accessed_count = fields.Integer(
        string="Items Accessed",
        compute="_compute_access_metrics",
        store=True,
        help="Number of individual items accessed"
    )
    items_modified_count = fields.Integer(
        string="Items Modified",
        compute="_compute_access_metrics",
        store=True,
        help="Number of items that were modified or remarked"
    )
    
    # Documentation requirements
    photo_documentation = fields.Boolean(
        string="Photo Documentation Required",
        help="Photos must be taken before and after access"
    )
    video_monitoring = fields.Boolean(
        string="Video Monitoring",
        help="Access session will be video recorded"
    )
    witness_required = fields.Boolean(
        string="Independent Witness Required",
        help="Independent witness must be present"
    )
    witness_name = fields.Char(
        string="Witness Name",
        help="Name of independent witness"
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT TRAIL
    # ============================================================================
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained",
        default=True,
        help="Chain of custody was maintained during access"
    )
    audit_trail_complete = fields.Boolean(
        string="Audit Trail Complete",
        compute="_compute_audit_trail_complete",
        store=True,
        help="Complete audit trail documentation available"
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes regarding compliance requirements and adherence"
    )

    # ============================================================================
    # SESSION RESULTS AND FINDINGS
    # ============================================================================
    session_summary = fields.Text(
        string="Session Summary",
        help="Summary of what was accomplished during access session"
    )
    findings = fields.Text(
        string="Findings",
        help="Any findings, issues, or observations from access session"
    )
    follow_up_required = fields.Boolean(
        string="Follow-up Required",
        help="Additional follow-up action is required"
    )
    follow_up_notes = fields.Text(
        string="Follow-up Notes",
        help="Details about required follow-up actions"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    coordinator_id = fields.Many2one('work.order.coordinator', string='Coordinator')

    # ============================================================================
    # MODEL CREATE WITH SEQUENCE
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'container.access.work.order') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id', 'container_count', 'access_type')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.container_count:
                access_type_display = dict(record._fields['access_type'].selection).get(record.access_type, record.access_type)
                record.display_name = _("%s - %s (%s containers - %s)", 
                    record.name, record.partner_id.name, record.container_count, access_type_display)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Container Access")

    @api.depends('container_ids')
    def _compute_container_metrics(self):
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends('scheduled_access_date', 'scheduled_duration_hours')
    def _compute_scheduled_end_time(self):
        for record in self:
            if record.scheduled_access_date and record.scheduled_duration_hours:
                record.scheduled_end_time = record.scheduled_access_date + timedelta(hours=record.scheduled_duration_hours)
            else:
                record.scheduled_end_time = False

    @api.depends('actual_start_time', 'actual_end_time')
    def _compute_actual_duration(self):
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                duration = record.actual_end_time - record.actual_start_time
                record.actual_duration_hours = duration.total_seconds() / 3600
            else:
                record.actual_duration_hours = 0.0

    @api.depends('access_activity_ids')
    def _compute_access_metrics(self):
        for record in self:
            activities = record.access_activity_ids
            record.items_accessed_count = len(activities)
            record.items_modified_count = len(activities.filtered('item_modified'))

    @api.depends('access_activity_ids', 'visitor_ids', 'chain_of_custody_maintained')
    def _compute_audit_trail_complete(self):
        for record in self:
            # Check if all required documentation is complete
            has_activities = len(record.access_activity_ids) > 0
            has_visitors = len(record.visitor_ids) > 0
            custody_maintained = record.chain_of_custody_maintained
            record.audit_trail_complete = has_activities and has_visitors and custody_maintained

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        """Submit access request for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be submitted"))
        
        self.write({'state': 'submitted'})
        self.message_post(
            body=_("Container access request submitted for approval"),
            message_type='notification'
        )
        return True

    def action_approve(self):
        """Approve access request"""
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be approved"))
        
        self.write({'state': 'approved'})
        self.message_post(
            body=_("Container access request approved"),
            message_type='notification'
        )
        return True

    def action_schedule(self):
        """Schedule the access session"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be scheduled"))
        
        self.write({'state': 'scheduled'})
        self.message_post(
            body=_("Access session scheduled for %s", self.scheduled_access_date.strftime('%Y-%m-%d %H:%M')),
            message_type='notification'
        )
        return True

    def action_start_access(self):
        """Start the access session"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled sessions can be started"))
        
        # Verify security requirements
        if self.requires_escort and not self.escort_employee_id:
            raise UserError(_("Security escort is required but not assigned"))
        
        if self.requires_key_access and not self.bin_key_ids:
            raise UserError(_("Key access is required but no keys are assigned"))
        
        self.write({
            'state': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })
        self.message_post(
            body=_("Container access session started"),
            message_type='notification'
        )
        return True

    def action_suspend_access(self):
        """Temporarily suspend access session"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only active sessions can be suspended"))
        
        self.write({'state': 'suspended'})
        self.message_post(
            body=_("Access session suspended"),
            message_type='notification'
        )
        return True

    def action_resume_access(self):
        """Resume suspended access session"""
        self.ensure_one()
        if self.state != 'suspended':
            raise UserError(_("Only suspended sessions can be resumed"))
        
        self.write({'state': 'in_progress'})
        self.message_post(
            body=_("Access session resumed"),
            message_type='notification'
        )
        return True

    def action_complete_access(self):
        """Complete the access session"""
        self.ensure_one()
        if self.state not in ['in_progress', 'suspended']:
            raise UserError(_("Only active or suspended sessions can be completed"))
        
        self.write({
            'state': 'completed',
            'actual_end_time': fields.Datetime.now()
        })
        self.message_post(
            body=_("Container access session completed"),
            message_type='notification'
        )
        return True

    def action_document_session(self):
        """Mark session as fully documented"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed sessions can be documented"))
        
        if not self.session_summary:
            raise UserError(_("Session summary is required before documentation"))
        
        self.write({'state': 'documented'})
        self.message_post(
            body=_("Access session documentation completed"),
            message_type='notification'
        )
        return True

    def action_close(self):
        """Close the work order"""
        self.ensure_one()
        if self.state != 'documented':
            raise UserError(_("Only documented sessions can be closed"))
        
        self.write({'state': 'closed'})
        self.message_post(
            body=_("Container access work order closed successfully"),
            message_type='notification'
        )
        return True

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def add_access_activity(self, container_id, activity_type, description, item_modified=False):
        """Add an access activity record"""
        self.ensure_one()
        return self.env['container.access.activity'].create({
            'work_order_id': self.id,
            'container_id': container_id,
            'activity_type': activity_type,
            'description': description,
            'item_modified': item_modified,
            'activity_time': fields.Datetime.now(),
            'user_id': self.env.user.id,
        })

    def generate_access_report(self):
        """Generate container access report"""
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.report_container_access',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'target': 'new',
        }

    @api.constrains('scheduled_access_date', 'scheduled_duration_hours')
    def _check_scheduling(self):
        for record in self:
            if record.scheduled_access_date and record.scheduled_duration_hours:
                if record.scheduled_duration_hours <= 0:
                    raise ValidationError(_("Scheduled duration must be positive"))
                
                if record.scheduled_duration_hours > 24:
                    raise ValidationError(_("Access sessions cannot exceed 24 hours"))

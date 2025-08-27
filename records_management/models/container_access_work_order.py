# -*- coding: utf-8 -*-
"""
Container Access Work Order Model

Manages and tracks work orders for accessing secure containers, ensuring
a complete audit trail for NAID AAA compliance and operational security.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerAccessWorkOrder(models.Model):
    """
    Container Access Work Order Management

    Handles the entire lifecycle of a container access request, from submission
    and approval to scheduling, execution, and final documentation. This model

    is central to maintaining security and a compliant chain of custody.
    """
    _name = 'container.access.work.order'
    _description = 'Container Access Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_access_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Work Order Reference',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New')
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Formatted display name for the work order."
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for coordinating this work order."
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('documented', 'Documented'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # REQUEST & CUSTOMER DETAILS
    # ============================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    portal_request_id = fields.Many2one(
        'portal.request',
        string='Portal Request',
        help="Link to the original customer request from the portal."
    )
    requestor_name = fields.Char(
        string='Requestor Name',
        tracking=True,
        help="Name of the person who requested access."
    )
    requestor_title = fields.Char(
        string='Requestor Title',
        tracking=True,
        help="Job title of the requestor."
    )

    # ============================================================================
    # ACCESS DETAILS
    # ============================================================================
    access_purpose = fields.Text(
        string='Purpose of Access',
        required=True,
        help="Detailed reason for requiring container access."
    )
    access_type = fields.Selection([
        ('retrieval', 'Document Retrieval'),
        ('audit', 'Compliance Audit'),
        ('inspection', 'Inspection'),
        ('maintenance', 'Maintenance')
    ], string='Access Type', default='retrieval', required=True, tracking=True)
    access_scope = fields.Selection([
        ('full', 'Full Access'),
        ('partial', 'Partial Access'),
        ('view_only', 'View Only')
    ], string='Access Scope', default='full', required=True)
    container_ids = fields.Many2many(
        'records.container',
        string='Containers to Access',
        required=True
    )
    container_count = fields.Integer(
        string='Container Count',
        compute='_compute_container_metrics',
        store=True
    )
    access_location_id = fields.Many2one(
        'records.location',
        string='Access Location',
        required=True,
        help="The physical location where access will occur."
    )

    # ============================================================================
    # SCHEDULING & DURATION
    # ============================================================================
    scheduled_access_date = fields.Datetime(string='Scheduled Start Time', tracking=True)
    scheduled_duration_hours = fields.Float(string='Scheduled Duration (Hours)', digits=(4, 2))
    scheduled_end_time = fields.Datetime(
        string='Scheduled End Time',
        compute='_compute_scheduled_end_time',
        store=True
    )
    actual_start_time = fields.Datetime(string='Actual Start Time', readonly=True, tracking=True)
    actual_end_time = fields.Datetime(string='Actual End Time', readonly=True, tracking=True)
    actual_duration_hours = fields.Float(
        string='Actual Duration (Hours)',
        compute='_compute_actual_duration',
        store=True,
        digits=(4, 2)
    )

    # ============================================================================
    # SECURITY & PERSONNEL
    # ============================================================================
    requires_escort = fields.Boolean(string='Requires Escort', default=False)
    escort_employee_id = fields.Many2one(
        'hr.employee',
        string='Escort Employee',
        tracking=True
    )
    requires_key_access = fields.Boolean(string='Requires Key Access', default=False)
    bin_key_ids = fields.Many2many('bin.key', string='Keys Required')
    visitor_ids = fields.One2many(
        'container.access.visitor',
        'work_order_id',
        string='Visitors'
    )
    max_visitors = fields.Integer(string='Max Visitors Allowed', default=1)
    coordinator_id = fields.Many2one(
        'hr.employee',
        string='Field Coordinator',
        help="Employee coordinating this access work order."
    )

    # ============================================================================
    # COMPLIANCE & DOCUMENTATION
    # ============================================================================
    access_activity_ids = fields.One2many(
        'container.access.activity',
        'work_order_id',
        string='Access Activities'
    )
    items_accessed_count = fields.Integer(
        string='Activities Logged',
        compute='_compute_access_metrics',
        store=True
    )
    items_modified_count = fields.Integer(
        string='Items Modified',
        compute='_compute_access_metrics',
        store=True
    )
    photo_documentation = fields.Boolean(string='Photo Documentation Required')
    video_monitoring = fields.Boolean(string='Video Monitoring Active')
    witness_required = fields.Boolean(string='Witness Required')
    witness_name = fields.Char(string='Witness Name')
    chain_of_custody_maintained = fields.Boolean(string='Chain of Custody Maintained', default=True)
    audit_trail_complete = fields.Boolean(
        string='Audit Trail Complete',
        compute='_compute_audit_trail_complete',
        store=True
    )
    compliance_notes = fields.Text(string='Compliance Notes')
    session_summary = fields.Text(string='Session Summary')
    findings = fields.Text(string='Findings / Observations')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_notes = fields.Text(string='Follow-up Notes')

    # ============================================================================
    # ORM & COMPUTE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('container.access.work.order') or _('New')
        return super().create(vals_list)

    @api.depends('name', 'partner_id.name', 'container_count', 'access_type')
    def _compute_display_name(self):
        for record in self:
            parts = [record.name or _("New")]
            if record.partner_id:
                parts.append(record.partner_id.name)
            if record.container_count > 0:
                access_type_display = dict(record._fields['access_type'].selection).get(record.access_type, '')
                parts.append(_("(%s containers - %s)") % (record.container_count, access_type_display))
            record.display_name = " - ".join(parts)

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

    @api.depends('access_activity_ids', 'access_activity_ids.documents_created')
    def _compute_access_metrics(self):
        for record in self:
            activities = record.access_activity_ids
            record.items_accessed_count = len(activities)
            record.items_modified_count = len(activities.filtered('documents_created'))

    @api.depends('access_activity_ids', 'visitor_ids', 'chain_of_custody_maintained')
    def _compute_audit_trail_complete(self):
        for record in self:
            has_activities = bool(record.access_activity_ids)
            has_visitors = bool(record.visitor_ids)
            record.audit_trail_complete = all([has_activities, has_visitors, record.chain_of_custody_maintained])

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft requests can be submitted."))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Container access request submitted for approval."), message_type='notification')

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be approved."))
        self.write({'state': 'approved'})
        self.message_post(body=_("Container access request approved."), message_type='notification')

    def action_schedule(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be scheduled."))
        if not self.scheduled_access_date:
            raise UserError(_("Please set a scheduled start time before scheduling."))
        self.write({'state': 'scheduled'})
        self.message_post(
            body=_("Access session scheduled for %s") % self.scheduled_access_date.strftime('%Y-%m-%d %H:%M'),
            message_type='notification'
        )

    def action_start_access(self):
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled sessions can be started."))
        if self.requires_escort and not self.escort_employee_id:
            raise UserError(_("Security escort is required but not assigned."))
        if self.requires_key_access and not self.bin_key_ids:
            raise UserError(_("Key access is required but no keys are assigned."))
        self.write({
            'state': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })
        self.message_post(body=_("Container access session started."), message_type='notification')

    def action_suspend_access(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only active sessions can be suspended."))
        self.write({'state': 'suspended'})
        self.message_post(body=_("Access session suspended."), message_type='notification')

    def action_resume_access(self):
        self.ensure_one()
        if self.state != 'suspended':
            raise UserError(_("Only suspended sessions can be resumed."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Access session resumed."), message_type='notification')

    def action_complete_access(self):
        self.ensure_one()
        if self.state not in ['in_progress', 'suspended']:
            raise UserError(_("Only active or suspended sessions can be completed."))
        self.write({
            'state': 'completed',
            'actual_end_time': fields.Datetime.now()
        })
        self.message_post(body=_("Container access session completed."), message_type='notification')

    def action_document_session(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed sessions can be documented."))
        if not self.session_summary:
            raise UserError(_("Session summary is required before completing documentation."))
        self.write({'state': 'documented'})
        self.message_post(body=_("Access session documentation completed."), message_type='notification')

    def action_close(self):
        self.ensure_one()
        if self.state != 'documented':
            raise UserError(_("Only documented sessions can be closed."))
        self.write({'state': 'closed'})
        self.message_post(body=_("Container access work order closed successfully."), message_type='notification')

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order has been cancelled."), message_type='notification')

    # ============================================================================
    # BUSINESS & UTILITY METHODS
    # ============================================================================
    def add_access_activity(self, container_id, activity_type, description, item_modified=False):
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
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.report_container_access_work_order',
            'report_type': 'qweb-pdf',
            'model': self._name,
            'res_id': self.id,
            'report_file': 'records_management.report_container_access_work_order',
        }

    @api.constrains('scheduled_access_date', 'scheduled_duration_hours')
    def _check_scheduling(self):
        for record in self:
            if record.scheduled_access_date and record.scheduled_duration_hours:
                if record.scheduled_duration_hours <= 0:
                    raise ValidationError(_("Scheduled duration must be positive."))
                if record.scheduled_duration_hours > 24:
                    raise ValidationError(_("Access sessions cannot exceed 24 hours."))

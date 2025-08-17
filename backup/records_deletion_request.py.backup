# -*- coding: utf-8 -*-

Records Deletion Request Module

This module manages deletion requests for the Records Management System,:
    pass
providing comprehensive tracking of document and container deletion workflows
with full NAID AAA compliance and audit trails.

Key Features
- Complete deletion request lifecycle management
- NAID compliance audit trails
- Integration with chain of custody tracking
- Customer portal integration for request submissions:
- Automated approval workflows with notifications
- Legal compliance documentation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDeletionRequest(models.Model):

        Records Deletion Request

    Manages comprehensive deletion request workflows for documents and containers""":
        with complete NAID compliance tracking and audit trail management.


    _name = "records.deletion.request"
    _description = "Records Deletion Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, name"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Request Reference",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for this deletion request":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Requested By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this deletion request"
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this deletion request is active"
    

        # ============================================================================
    # REQUEST DETAILS
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer requesting the deletion"
    

    request_date = fields.Date(
        string="Request Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        index=True,
        help="Date when the deletion was requested"
    

    scheduled_deletion_date = fields.Date(
        string="Scheduled Deletion Date",
        tracking=True,
        help="Planned date for executing the deletion":
    

    actual_deletion_date = fields.Date(
        string="Actual Deletion Date",
        tracking=True,
        help="Date when deletion was actually completed"
    

    deletion_type = fields.Selection([)]
        ("document", "Document Deletion"),
        ("container", "Container Deletion"),
        ("bulk", "Bulk Deletion"),
        ("emergency", "Emergency Deletion"),
    
        required=True,
       default="document",
       tracking=True,
       help="Type of deletion being requested"

    priority = fields.Selection([)]
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    
        default="normal",
       tracking=True,
       help="Priority level of the deletion request"

    # ============================================================================
        # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description",
        required=True,
        tracking=True,
        help="Detailed description of items to be deleted"
    

    reason = fields.Text(
        string="Deletion Reason",
        required=True,
        tracking=True,
        help="Business reason for the deletion request":
    

    notes = fields.Text(
        string="Internal Notes",
        help="Internal notes and comments about the deletion"
    

    special_instructions = fields.Text(
        string="Special Instructions",
        help="Any special handling instructions for the deletion":
    

        # ============================================================================
    # WORKFLOW STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([)]
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    
        default="draft",
       tracking=True,
       required=True,
       index=True,
       help="Current status of the deletion request"

    # ============================================================================
        # APPROVAL WORKFLOW FIELDS
    # ============================================================================
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who approved this deletion request"
    

    approval_date = fields.Datetime(
        string="Approval Date",
        tracking=True,
        help="Date and time when request was approved"
    

    rejection_reason = fields.Text(
        string="Rejection Reason",
        help="Reason why the request was rejected"
    

        # ============================================================================
    # ITEM RELATIONSHIPS
        # ============================================================================
    document_ids = fields.Many2many(
        "records.document",
        string="Documents to Delete",
        help="Specific documents to be deleted"
    

    container_ids = fields.Many2many(
        "records.container",
        string="Containers to Delete", 
        help="Specific containers to be deleted"
    

        # ============================================================================
    # LEGAL AND COMPLIANCE FIELDS
        # ============================================================================
    legal_hold_check = fields.Boolean(
        string="Legal Hold Check Complete",
        help="Confirms legal hold status has been verified"
    

    retention_policy_verified = fields.Boolean(
        string="Retention Policy Verified",
        help="Confirms retention policies have been checked"
    

    customer_authorization = fields.Boolean(
        string="Customer Authorization Received",
        tracking=True,
        help="Customer has provided proper authorization"
    

    compliance_approved = fields.Boolean(
        string="Compliance Approved",
        tracking=True,
        help="Compliance team has approved the deletion"
    

        # ============================================================================
    # NAID COMPLIANCE TRACKING
        # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether this deletion follows NAID standards"
    

    chain_of_custody_id = fields.Many2one(
        "records.chain.of.custody",
        string="Chain of Custody",
        help="Associated chain of custody record"
    

    certificate_of_deletion_id = fields.Many2one(
        "certificate.of.deletion",
        string="Certificate of Deletion",
        help="Generated certificate of deletion"
    

        # ============================================================================
    # FINANCIAL TRACKING
        # ============================================================================
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost for the deletion service":
    

    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost incurred for the deletion":
    

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    

    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this deletion service is billable to customer"
    

        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name with date and status"
    

    total_items_count = fields.Integer(
        string="Total Items",
        compute="_compute_total_items",
        store=True,
        help="Total number of items to be deleted"
    

    days_since_request = fields.Integer(
        string="Days Since Request",
        compute="_compute_days_since_request",
        help="Number of days since the request was created"
    

    can_approve = fields.Boolean(
        string="Can Approve",
        compute="_compute_can_approve",
        help="Whether current user can approve this request"
    

        # ============================================================================
    # PORTAL AND COMMUNICATION FIELDS
        # ============================================================================
    portal_request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        help="Related portal request if submitted through customer portal":
    

    customer_notified = fields.Boolean(
        string="Customer Notified",
        help="Whether customer has been notified of completion"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    

        # ============================================================================
    # COMPUTED METHODS
        # ============================================================================
    @api.depends("name", "request_date", "state")
    def _compute_display_name(self):
        """Compute display name with date and state info"""
        for record in self:
            if record.request_date:
                record.display_name = _("%(name)s (%(state)s) - %(date)s", {)}
                    'name': record.name,
                    'state': dict(record._fields['state'].selection).get(record.state, record.state),
                    'date': record.request_date.strftime("%Y-%m-%d")
                
            else:
                record.display_name = _("%(name)s - %(state)s", {)}
                    'name': record.name,
                    'state': dict(record._fields['state'].selection).get(record.state, record.state)
                

    @api.depends("document_ids", "container_ids")
    def _compute_total_items(self):
        """Compute total number of items to be deleted"""
        for record in self:
            record.total_items_count = len(record.document_ids) + len(record.container_ids)

    @api.depends("request_date")
    def _compute_days_since_request(self):
        """Compute days since request was created"""
        for record in self:
            if record.request_date:
    delta = fields.Date.today() - record.request_date
                record.days_since_request = delta.days
            else:
                record.days_since_request = 0

    def _compute_can_approve(self):
        """Check if current user can approve this request""":
        for record in self:
            record.can_approve = self.env.user.has_group('records_management.group_records_manager')

    # ============================================================================
        # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and validate"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code()
                    "records.deletion.request"
                ) or _("New"
        
        records = super().create(vals_list)
        
        for record in records:
            record._create_naid_audit_log()
        
        return records

    def write(self, vals):
        """Override write to track important changes"""
        result = super().write(vals)
        
        # Track status changes
        if "state" in vals:
            for record in self:
                record.message_post()
                    body=_("Deletion request status changed to %s", vals["state"])
                
        
        return result

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        """Submit deletion request for approval""":
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft requests can be submitted"))

        # Validation before submission
        self._validate_for_submission()

        self.write({"state": "submitted"})
        self._notify_approvers()
        self.message_post()
            body=_("Deletion request submitted for approval"):
        

    def action_approve(self):
        """Approve the deletion request"""
        self.ensure_one()
        if not self.can_approve:
            raise UserError(_("You don't have permission to approve deletion requests"))

        if self.state not in ["submitted", "under_review"]:
            raise UserError(_("Only submitted or under review requests can be approved"))

        self.write({)}
            "state": "approved",
            "approved_by_id": self.env.user.id,
            "approval_date": fields.Datetime.now(),
        

        self.message_post()
            body=_("Deletion request approved by %s", self.env.user.name)
        
        self._notify_requestor_approved()

    def action_reject(self):
        """Reject the deletion request"""
        self.ensure_one()
        if not self.can_approve:
            raise UserError(_("You don't have permission to reject deletion requests"))

        if self.state not in ["submitted", "under_review"]:
            raise UserError(_("Only submitted or under review requests can be rejected"))

        return {}
            "type": "ir.actions.act_window",
            "name": _("Rejection Reason"),
            "res_model": "deletion.rejection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_request_id": self.id,
            
        

    def action_schedule(self):
        """Schedule the approved deletion"""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Only approved requests can be scheduled"))

        if not self.scheduled_deletion_date:
            raise UserError(_("Please set a scheduled deletion date"))

        self.write({"state": "scheduled"})
        self._create_work_orders()
        self.message_post()
            body=_("Deletion scheduled for %s", self.scheduled_deletion_date):
        

    def action_start_deletion(self):
        """Start the deletion process"""
        self.ensure_one()
        if self.state != "scheduled":
            raise UserError(_("Only scheduled requests can be started"))

        self.write({"state": "in_progress"})
        self._create_chain_of_custody()
        self.message_post()
            body=_("Deletion process started")
        

    def action_complete_deletion(self):
        """Complete the deletion process"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress requests can be completed"))

        self.write({)}
            "state": "completed",
            "actual_deletion_date": fields.Date.today(),
        

        self._generate_certificate_of_deletion()
        self._update_chain_of_custody()
        self._notify_customer_completion()

        self.message_post()
            body=_("Deletion process completed successfully")
        

    def action_cancel(self):
        """Cancel the deletion request"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot cancel completed deletions"))

        self.write({"state": "cancelled"})
        self.message_post()
            body=_("Deletion request cancelled")
        

    def action_reset_to_draft(self):
        """Reset request to draft status"""
        self.ensure_one()
        if self.state in ["completed", "in_progress"]:
            raise UserError(_("Cannot reset completed or in-progress requests"))

        self.write({)}
            "state": "draft",
            "approved_by_id": False,
            "approval_date": False,
        

        self.message_post()
            body=_("Deletion request reset to draft")
        

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    def get_deletion_summary(self):
        """Get deletion request summary for reporting""":
        self.ensure_one()
        return {}
            'request_reference': self.name,
            'customer': self.partner_id.name,
            'deletion_type': self.deletion_type,
            'priority': self.priority,
            'status': self.state,
            'request_date': self.request_date,
            'scheduled_date': self.scheduled_deletion_date,
            'total_items': self.total_items_count,
            'estimated_cost': self.estimated_cost,
            'billable': self.billable,
        

    def _validate_for_submission(self):
        """Validate request before submission"""
        if not self.description:
            raise ValidationError(_("Please provide a description of items to be deleted"))

        if not self.reason:
            raise ValidationError(_("Please provide a reason for the deletion")):
        if not self.document_ids and not self.container_ids:
            raise ValidationError(_("Please specify documents or containers to be deleted"))

        if not self.customer_authorization:
            raise ValidationError(_("Customer authorization is required"))

    def _notify_approvers(self):
        """Notify approvers of pending request"""
        approvers = self.env['res.users'].search([)]
            ('groups_id', 'in', [self.env.ref('records_management.group_records_manager').id])
        

        for approver in approvers:
            self.activity_schedule()
                'mail.mail_activity_data_todo',
                summary=_('Deletion Request Approval: %s', self.name),
                note=_('Please review and approve deletion request %s', self.name),
                user_id=approver.id,
            

    def _notify_requestor_approved(self):
        """Notify requestor of approval"""
        if self.user_id:
            self.activity_schedule()
                'mail.mail_activity_data_todo',
                summary=_('Deletion Request Approved: %s', self.name),
                note=_('Your deletion request has been approved and will be scheduled'),
                user_id=self.user_id.id,
            

    def _create_work_orders(self):
        """Create work orders for the deletion""":
        if self.document_ids or self.container_ids:
            work_order = self.env['deletion.work.order'].create({)}
                'name': _('Deletion: %s', self.name),
                'deletion_request_id': self.id,
                'partner_id': self.partner_id.id,
                'scheduled_date': self.scheduled_deletion_date,
                'document_ids': [(6, 0, self.document_ids.ids)],
                'container_ids': [(6, 0, self.container_ids.ids)],
            
            return work_order

    def _create_chain_of_custody(self):
        """Create chain of custody record"""
        if not self.chain_of_custody_id:
            custody = self.env['records.chain.of.custody'].create({)}
                'name': _('Deletion Chain: %s', self.name),
                'deletion_request_id': self.id,
                'partner_id': self.partner_id.id,
                'event_type': 'deletion_start',
                'date': fields.Datetime.now(),
                'responsible_user_id': self.env.user.id,
            
            self.chain_of_custody_id = custody.id

    def _update_chain_of_custody(self):
        """Update chain of custody with completion"""
        if self.chain_of_custody_id:
            self.chain_of_custody_id.add_event('deletion_complete', {)}
                'date': fields.Datetime.now(),
                'responsible_user_id': self.env.user.id,
                'notes': _('Deletion completed successfully'),
            

    def _generate_certificate_of_deletion(self):
        """Generate certificate of deletion"""
        if not self.certificate_of_deletion_id:
            certificate = self.env['certificate.of.deletion'].create({)}
                'name': _('Certificate: %s', self.name),
                'deletion_request_id': self.id,
                'partner_id': self.partner_id.id,
                'deletion_date': self.actual_deletion_date,
                'method': 'secure_shredding',
                'items_count': self.total_items_count,
                'naid_compliant': self.naid_compliant,
            
            self.certificate_of_deletion_id = certificate.id

    def _notify_customer_completion(self):
        """Notify customer of completion"""
        if self.partner_id.email:
            template = self.env.ref('records_management.email_template_deletion_complete')
            template.send_mail(self.id, force_send=True)
            self.customer_notified = True

    def _create_naid_audit_log(self):
        """Create NAID audit log entry"""
        try:
            self.env['naid.audit.log'].create({)}
                'event_type': 'deletion_request',
                'description': _("Deletion request created: %s", self.name),
                'user_id': self.env.user.id,
                'partner_id': self.partner_id.id,
                'deletion_request_id': self.id,
                'compliance_level': 'aaa',
            
        except Exception as e
            # Log error but don't fail the creation
            self.message_post()
                body=_("Warning: Could not create NAID audit log: %s", str(e)),
                message_type='comment'
            

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains("request_date", "scheduled_deletion_date")
    def _check_dates(self):
        """Validate date consistency"""
        for record in self:
            if record.request_date and record.request_date > fields.Date.today():
                raise ValidationError(_("Request date cannot be in the future"))

            if record.scheduled_deletion_date and record.request_date:
                if record.scheduled_deletion_date < record.request_date:
                    raise ValidationError(_("Scheduled deletion date cannot be before request date"))

    @api.constrains("estimated_cost", "actual_cost")
    def _check_costs(self):
        """Validate cost amounts"""
        for record in self:
            if record.estimated_cost and record.estimated_cost < 0:
                raise ValidationError(_("Estimated cost cannot be negative"))
            if record.actual_cost and record.actual_cost < 0:
                raise ValidationError(_("Actual cost cannot be negative"))

    @api.constrains("document_ids", "container_ids")
    def _check_items_to_delete(self):
        """Validate items to be deleted"""
        for record in self:
            if record.state != 'draft' and not record.document_ids and not record.container_ids:
                raise ValidationError(_("Please specify documents or containers to be deleted"))

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display using computed display_name"""
        result = []
        for record in self:
            name = record.display_name or record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, customer, or description"""
        args = args or []
        domain = []
        
        if name:
            domain = []
                "|", "|", "|",
                ("name", operator, name),
                ("partner_id.name", operator, name),
                ("description", operator, name),
                ("reason", operator, name),
            
        
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_deletion_dashboard_data(self):
        """Get dashboard data for deletion requests""":
        return {}
            'total_requests': self.search_count([,
            'pending_approval': self.search_count([('state', '=', 'submitted')]),
            'in_progress': self.search_count([('state', '=', 'in_progress')]),
            'completed_this_month': self.search_count([)]
                ('state', '=', 'completed'),
                ('actual_deletion_date', '>=', fields.Date.today().replace(day=1)),
            
            'by_type': self.read_group()
                [('state', '!=', 'cancelled')],
                ['deletion_type'],
                ['deletion_type']
            
        

    @api.model
    def generate_deletion_report(self, date_from=None, date_to=None):
        """Generate comprehensive deletion report"""
        domain = []
        
        if date_from:
            domain.append(('request_date', '>=', date_from))
        if date_to:
            domain.append(('request_date', '<=', date_to))
        
        requests = self.search(domain)
        
        return {}
            'period': {'from': date_from, 'to': date_to},
            'total_requests': len(requests),
            'by_status': {}
                status: len(requests.filtered(lambda r: r.state == status))
                for status, _ in self._fields['state'].selection:
            
            'total_items_deleted': sum(requests.mapped('total_items_count')),
            'total_cost': sum(requests.mapped('actual_cost')),
            'requests': [req.get_deletion_summary() for req in requests],:
        


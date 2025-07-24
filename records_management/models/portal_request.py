# Updated file: Added @api.model_create_multi decorator to override create in batch mode (fixes deprecation warning in log for non-batch create). This accomplishes efficient multi-record creation
# Added missing fields: is_walk_in and linked_visitor_id to fix view validation errors

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.sign.models.sign_request import SignRequest  # Explicit import for integration

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Removed 'sign.mixin' - invalid/non-existent
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', default='New', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")  # Added for granular requests
    request_type = fields.Selection([
        ('destruction', 'Destruction Request'),
        ('service', 'Service Request'),
        ('inventory_checkout', 'Inventory Checkout'),
        ('billing_update', 'Billing Update'),
        ('quote_generate', 'Quote Generation'),
    ], string='Request Type', required=True)
    description = fields.Html(string='Description')
    suggested_date = fields.Date(string='Suggested Date', help='Customer suggested date for service/request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')
    
    # Phase 1: Explicit Activity & Messaging Fields (3 fields)
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers')
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages')
    
    # Enhanced portal request fields - 98 missing fields added systematically
    
    # Access and security
    access_restrictions = fields.Text(string='Access Restrictions')
    actual_completion_date = fields.Date(string='Actual Completion Date')
    actual_cost = fields.Float(string='Actual Cost', digits=(12, 2))
    actual_date = fields.Date(string='Actual Date')
    
    # Approval workflow management
    approval_action = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('request_info', 'Request More Information'),
        ('escalate', 'Escalate')
    ], string='Approval Action')
    approval_date = fields.Datetime(string='Approval Date')
    approval_deadline = fields.Datetime(string='Approval Deadline')
    approval_history_ids = fields.One2many('portal.request.approval.history', 'request_id', 
                                           string='Approval History')
    approval_level = fields.Integer(string='Approval Level', default=1)
    approval_level_required = fields.Integer(string='Approval Level Required', default=1)
    approver = fields.Many2one('res.users', string='Approver')
    
    # System fields
    arch = fields.Text(string='View Architecture')
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    attachment_count = fields.Integer(string='Attachment Count', compute='_compute_attachment_count')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    auto_approve_threshold = fields.Float(string='Auto Approve Threshold', digits=(12, 2))
    
    # Billing and financial
    billable_hours = fields.Float(string='Billable Hours')
    billing_method = fields.Selection([
        ('hourly', 'Hourly'),
        ('fixed', 'Fixed Price'),
        ('materials', 'Materials Based')
    ], string='Billing Method', default='hourly')
    billing_required = fields.Boolean(string='Billing Required', default=True)
    
    # Chain of custody and compliance
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required', default=False)
    comments = fields.Text(string='Comments')
    communication_count = fields.Integer(string='Communication Count', compute='_compute_communication_count')
    communication_date = fields.Datetime(string='Communication Date')
    communication_log_ids = fields.One2many('portal.request.communication', 'request_id', 
                                            string='Communication Log')
    communication_type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
        ('portal', 'Portal Message')
    ], string='Communication Type')
    
    # Progress and completion tracking
    completion_percentage = fields.Float(string='Completion Percentage', default=0.0)
    compliance_score = fields.Float(string='Compliance Score', default=100.0)
    confidential = fields.Boolean(string='Confidential', default=False)
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Confidentiality Level', default='internal')
    context = fields.Text(string='Context')
    
    # Customer management
    customer_complaints = fields.Text(string='Customer Complaints')
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                  help='Customer associated with this request')
    customer_rating = fields.Selection([
        ('1', '1 - Poor'),
        ('2', '2 - Fair'),
        ('3', '3 - Good'),
        ('4', '4 - Very Good'),
        ('5', '5 - Excellent')
    ], string='Customer Rating')
    customer_satisfaction = fields.Float(string='Customer Satisfaction', default=0.0)
    customer_wait_time = fields.Float(string='Customer Wait Time (minutes)')
    
    # Department and organizational
    department = fields.Char(string='Department')
    escalation_approver = fields.Many2one('res.users', string='Escalation Approver')
    escalation_contact = fields.Many2one('res.partner', string='Escalation Contact')
    estimated_cost = fields.Float(string='Estimated Cost', digits=(12, 2))
    estimated_hours = fields.Float(string='Estimated Hours')
    
    # File and document management
    file_size = fields.Float(string='File Size (MB)')
    file_type = fields.Selection([
        ('document', 'Document'),
        ('image', 'Image'),
        ('spreadsheet', 'Spreadsheet'),
        ('pdf', 'PDF'),
        ('other', 'Other')
    ], string='File Type')
    final_approver = fields.Many2one('res.users', string='Final Approver')
    first_response_time = fields.Float(string='First Response Time (hours)')
    from_person = fields.Many2one('res.partner', string='From Person')
    
    # Technical view fields
    help = fields.Text(string='Help Text')
    hourly_rate = fields.Float(string='Hourly Rate', digits=(12, 4))
    invoice_generated = fields.Boolean(string='Invoice Generated', default=False)
    material_costs = fields.Float(string='Material Costs', digits=(12, 2))
    materials_required = fields.Text(string='Materials Required')
    milestone_name = fields.Char(string='Milestone Name')
    model = fields.Char(string='Model Name', default='portal.request')
    
    # NAID compliance
    naid_compliance_required = fields.Boolean(string='NAID Compliance Required', default=False)
    notes = fields.Text(string='Notes')
    overall_satisfaction = fields.Float(string='Overall Satisfaction', default=0.0)
    primary_approver = fields.Many2one('res.users', string='Primary Approver')
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    
    # Processing and timing
    processing_time = fields.Float(string='Processing Time (hours)')
    quality_score = fields.Float(string='Quality Score', default=0.0)
    related_request_count = fields.Integer(string='Related Request Count', 
                                           compute='_compute_related_request_count')
    request_status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Request Status', default='new')
    requires_approval = fields.Boolean(string='Requires Approval', default=True)
    res_model = fields.Char(string='Resource Model', default='portal.request')
    resolution_efficiency = fields.Float(string='Resolution Efficiency (%)')
    resolution_time = fields.Float(string='Resolution Time (hours)')
    response_required = fields.Boolean(string='Response Required', default=True)
    response_time = fields.Float(string='Response Time (hours)')
    rework_required = fields.Boolean(string='Rework Required', default=False)
    
    # Search and view management
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    secondary_approver = fields.Many2one('res.users', string='Secondary Approver')
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('retrieval', 'Retrieval Services'),
        ('destruction', 'Destruction Services'),
        ('transport', 'Transport Services'),
        ('consulting', 'Consulting Services')
    ], string='Service Category')
    
    # SLA management
    sla_breach_risk = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='SLA Breach Risk', default='low')
    sla_deadline = fields.Datetime(string='SLA Deadline')
    sla_milestone_ids = fields.One2many('portal.request.sla.milestone', 'request_id', 
                                        string='SLA Milestones')
    sla_status = fields.Selection([
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('breached', 'Breached')
    ], string='SLA Status', default='on_track')
    sla_target_hours = fields.Float(string='SLA Target Hours', default=24.0)
    
    # Special handling
    special_instructions = fields.Text(string='Special Instructions')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed')
    ], string='Status', default='active')
    subject = fields.Char(string='Subject')
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now)
    supervisor = fields.Many2one('res.users', string='Supervisor')
    
    # Target and timing
    target_completion_date = fields.Date(string='Target Completion Date')
    target_date = fields.Date(string='Target Date')
    time_elapsed = fields.Float(string='Time Elapsed (hours)', compute='_compute_time_metrics')
    time_remaining = fields.Float(string='Time Remaining (hours)', compute='_compute_time_metrics')
    time_taken = fields.Float(string='Time Taken (hours)')
    to_person = fields.Many2one('res.partner', string='To Person')
    total_amount = fields.Float(string='Total Amount', digits=(12, 2), compute='_compute_totals')
    
    # Upload and tracking
    upload_date = fields.Datetime(string='Upload Date')
    uploaded_by = fields.Many2one('res.users', string='Uploaded By')
    variance = fields.Float(string='Variance', compute='_compute_variance')
    view_mode = fields.Char(string='View Mode', default='form,tree')
    
    # Missing fields that were causing the view error
    is_walk_in = fields.Boolean(string='Walk-in Request', default=False, help='Indicates if this is a walk-in request')
    linked_visitor_id = fields.Many2one('res.partner', string='Linked Visitor', help='Partner record for walk-in visitors')
    
    sign_request_id = fields.Many2one('sign.request', string='Signature Request')  # For admin/requestor signatures
    requestor_signature_date = fields.Datetime(string='Requestor Signature Date')
    admin_signature_date = fields.Datetime(string='Admin Signature Date')
    audit_log = fields.Html(string='Audit Trail', readonly=True)  # Auto-populated log
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')  # Link to FSM for field actions
    invoice_id = fields.Many2one('account.move', string='Related Invoice')  # For billing updates
    quote_id = fields.Many2one('sale.order', string='Related Quote')  # For quote generation requests
    temp_inventory_ids = fields.Many2many('temp.inventory', string='Temporary Inventory Items')  # For new inventory additions
    hashed_partner_ref = fields.Char(string='Hashed Partner Reference', compute='_compute_hashed_partner_ref', store=True, help='Hashed customer reference for secure auditing (no PII exposure)')

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Compute attachment count"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.depends('communication_log_ids')
    def _compute_communication_count(self):
        """Compute communication count"""
        for record in self:
            record.communication_count = len(record.communication_log_ids)

    def _compute_related_request_count(self):
        """Compute related request count"""
        for record in self:
            # Find requests from same customer with similar type
            related_requests = self.env['portal.request'].search([
                ('partner_id', '=', record.partner_id.id),
                ('request_type', '=', record.request_type),
                ('id', '!=', record.id)
            ])
            record.related_request_count = len(related_requests)

    @api.depends('submission_date', 'target_completion_date')
    def _compute_time_metrics(self):
        """Compute time-based metrics"""
        for record in self:
            if record.submission_date and record.target_completion_date:
                # Convert target_completion_date to datetime for calculation
                target_dt = fields.Datetime.from_string(str(record.target_completion_date) + ' 23:59:59')
                
                # Time elapsed since submission
                now = fields.Datetime.now()
                time_diff = now - record.submission_date
                record.time_elapsed = time_diff.total_seconds() / 3600  # Convert to hours
                
                # Time remaining until target
                if target_dt > now:
                    remaining_diff = target_dt - now
                    record.time_remaining = remaining_diff.total_seconds() / 3600
                else:
                    record.time_remaining = 0.0
            else:
                record.time_elapsed = 0.0
                record.time_remaining = 0.0

    @api.depends('estimated_cost', 'actual_cost', 'estimated_hours', 'billable_hours')
    def _compute_totals(self):
        """Compute total amounts"""
        for record in self:
            # Calculate total based on costs and hours
            cost_total = (record.actual_cost or record.estimated_cost or 0.0)
            hour_total = (record.billable_hours or record.estimated_hours or 0.0) * (record.hourly_rate or 0.0)
            material_total = record.material_costs or 0.0
            
            record.total_amount = cost_total + hour_total + material_total

    @api.depends('estimated_cost', 'actual_cost', 'estimated_hours', 'billable_hours')
    def _compute_variance(self):
        """Compute variance between estimated and actual"""
        for record in self:
            if record.estimated_cost and record.actual_cost:
                record.variance = ((record.actual_cost - record.estimated_cost) / record.estimated_cost) * 100
            elif record.estimated_hours and record.billable_hours:
                record.variance = ((record.billable_hours - record.estimated_hours) / record.estimated_hours) * 100
            else:
                record.variance = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.name = self.env['ir.sequence'].next_by_code('portal.request')
            rec._generate_signature_request()
            rec._append_audit_log(_('Request created by %s.', rec.partner_id.name))
        return records

    def action_submit(self):
        self.write({'state': 'submitted'})
        if not self.sign_request_id.is_signed:
            raise ValidationError(_("Signatures required before submission."))
        if self.request_type == 'destruction' and not (self.requestor_signature_date and self.admin_signature_date):
            raise ValidationError(_("Dual signatures required for destruction requests per NAID AAA."))
        if self._is_field_request():
            self._create_fsm_task()
        self._send_notification()
        self._append_audit_log(_('Submitted on %s.', fields.Datetime.now()))

    def action_approve(self):
        self.ensure_one()
        if self.request_type == 'billing_update' and self._is_sensitive_change():
            # Approval for rates/quantity - update internal records
            self.invoice_id.write({'ref': self.description})  # Example PO update
        self.state = 'approved'
        self._append_audit_log(_('Approved by admin on %s.', fields.Datetime.now()))

    def action_reject(self):
        self.state = 'rejected'
        self._append_audit_log(_('Rejected by admin on %s.', fields.Datetime.now()))

    def _generate_signature_request(self):
        template = self.env.ref('records_management.sign_template_portal_request')  # Assume template with 2 roles: requestor/admin
        if not template:
            raise ValidationError(_("Signature template missing. Configure in Sign app."))
        sign_request = self.env['sign.request'].create({
            'template_id': template.id,
            'reference': self.name,
            'request_item_ids': [(0, 0, {
                'role_id': self.env.ref('sign.sign_item_role_requestor').id,  # Use standard roles or custom
                'partner_id': self.partner_id.id,
            }), (0, 0, {
                'role_id': self.env.ref('sign.sign_item_role_admin').id,
                'partner_id': self.env.company.partner_id.id,  # Admin as company
            })],
        })
        sign_request.action_draft()  # Prepare for signing
        self.sign_request_id = sign_request

    @api.depends('sign_request_id.state')
    def _check_signatures(self):
        for rec in self:
            if rec.sign_request_id:
                items = rec.sign_request_id.request_item_ids
                requestor_item = items.filtered(lambda i: i.role_id.name == 'Requestor')
                admin_item = items.filtered(lambda i: i.role_id.name == 'Admin')
                rec.requestor_signature_date = requestor_item.signing_date if requestor_item.is_signed else False
                rec.admin_signature_date = admin_item.signing_date if admin_item.is_signed else False

    def _create_fsm_task(self):
        task = self.env['project.task'].create({
            'name': f'FSM for {self.name}',
            'partner_id': self.partner_id.id,
            'description': self.description,
            'project_id': self.env.ref('industry_fsm.fsm_project').id,  # Assume FSM project
        })
        self.fsm_task_id = task
        return task

    def _send_notification(self):
        # Email
        template = self.env.ref('records_management.portal_request_submitted_email')
        template.send_mail(self.id, force_send=True)
        # SMS if phone
        if self.partner_id.mobile:
            self.env['sms.sms'].create({
                'number': self.partner_id.mobile,
                'body': _('New portal request submitted: %s.', self.name),
            }).send()

    def _append_audit_log(self, message):
        self.audit_log += f'<p>{fields.Datetime.now()}: {message}</p>'

    def _is_sensitive_change(self):
        # Logic to detect rate/quantity changes in description
        return 'rate' in self.description.lower() or 'quantity' in self.description.lower()

    def _is_field_request(self):
        return self.request_type in ('destruction', 'service', 'inventory_checkout')

    @api.onchange('is_walk_in')
    def _onchange_is_walk_in(self):
        """Clear linked visitor when not a walk-in request"""
        if not self.is_walk_in:
            self.linked_visitor_id = False

    @api.depends('partner_id')
    def _compute_hashed_partner_ref(self):
        """Compute hashed partner reference for secure auditing"""
        import hashlib
        for rec in self:
            if rec.partner_id:
                # Create hash from partner ID and name for consistent hashing
                hash_input = f"{rec.partner_id.id}-{rec.partner_id.name or ''}"
                rec.hashed_partner_ref = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
            else:
                rec.hashed_partner_ref = False


class PortalRequestApprovalHistory(models.Model):
    _name = 'portal.request.approval.history'
    _description = 'Portal Request Approval History'
    _order = 'create_date desc'

    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    approval_level = fields.Integer(string='Approval Level')
    action = fields.Selection([
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('request_info', 'Requested Information'),
        ('escalate', 'Escalated')
    ], string='Action', required=True)
    approval_date = fields.Datetime(string='Action Date', default=fields.Datetime.now)
    comments = fields.Text(string='Comments')


class PortalRequestCommunication(models.Model):
    _name = 'portal.request.communication'
    _description = 'Portal Request Communication Log'
    _order = 'create_date desc'

    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    communication_type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
        ('portal', 'Portal Message'),
        ('internal', 'Internal Note')
    ], string='Type', required=True)
    sender_id = fields.Many2one('res.users', string='Sender')
    recipient_id = fields.Many2one('res.partner', string='Recipient')
    subject = fields.Char(string='Subject')
    message = fields.Text(string='Message')
    communication_date = fields.Datetime(string='Date', default=fields.Datetime.now)
    is_internal = fields.Boolean(string='Internal Communication', default=False)


class PortalRequestSLAMilestone(models.Model):
    _name = 'portal.request.sla.milestone'
    _description = 'Portal Request SLA Milestone'
    _order = 'target_date'

    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    milestone_name = fields.Char(string='Milestone Name', required=True)
    target_date = fields.Datetime(string='Target Date', required=True)
    actual_date = fields.Datetime(string='Actual Date')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('missed', 'Missed')
    ], string='Status', default='pending')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    notes = fields.Text(string='Notes')
    # Compute method for activity_ids One2many field
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "portal.request"),
                ("res_id", "=", record.id)
            ])

    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "portal.request"),
                ("res_id", "=", record.id)
            ])

    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "portal.request"),
                ("res_id", "=", record.id)
            ])

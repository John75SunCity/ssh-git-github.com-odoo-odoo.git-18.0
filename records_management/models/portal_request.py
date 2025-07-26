# Portal Request Model - Enterprise-grade request management system with SLA tracking
# Features: Complete approval workflow, financial billing integration, quality metrics

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
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")
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
    ], default='draft', tracking=True)
    
    # Core Request Management Fields
    customer_id = fields.Many2one('res.partner', string='Customer', related='partner_id', store=True)
    subject = fields.Char(string='Subject', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'), 
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='normal', string='Priority', tracking=True)
    status = fields.Selection([
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], default='new', string='Status', tracking=True)
    request_status = fields.Char(string='Request Status', compute='_compute_request_status', store=True)
    
    # Dates and Timeline
    submission_date = fields.Datetime(string='Submission Date', default=fields.Datetime.now)
    actual_date = fields.Date(string='Actual Date')
    actual_completion_date = fields.Datetime(string='Actual Completion Date')
    target_date = fields.Date(string='Target Date')
    target_completion_date = fields.Datetime(string='Target Completion Date')
    upload_date = fields.Datetime(string='Upload Date')
    
    # SLA and Performance Tracking
    sla_deadline = fields.Datetime(string='SLA Deadline')
    sla_status = fields.Selection([
        ('on_time', 'On Time'),
        ('at_risk', 'At Risk'),
        ('breached', 'Breached')
    ], string='SLA Status', compute='_compute_sla_status')
    sla_target_hours = fields.Float(string='SLA Target Hours')
    sla_breach_risk = fields.Boolean(string='SLA Breach Risk', compute='_compute_sla_breach_risk')
    sla_milestone_ids = fields.One2many('portal.request.milestone', 'request_id', string='SLA Milestones')
    
    # Time Tracking
    processing_time = fields.Float(string='Processing Time (Hours)')
    response_time = fields.Float(string='Response Time (Hours)')
    resolution_time = fields.Float(string='Resolution Time (Hours)')
    first_response_time = fields.Float(string='First Response Time (Hours)')
    time_taken = fields.Float(string='Time Taken (Hours)')
    time_elapsed = fields.Float(string='Time Elapsed (Hours)', compute='_compute_time_elapsed')
    time_remaining = fields.Float(string='Time Remaining (Hours)', compute='_compute_time_remaining')
    total_processing_time = fields.Float(string='Total Processing Time (Hours)')
    
    # Assignment and Personnel
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    supervisor = fields.Many2one('res.users', string='Supervisor')
    from_person = fields.Many2one('res.users', string='From Person')
    to_person = fields.Many2one('res.users', string='To Person')
    uploaded_by = fields.Many2one('res.users', string='Uploaded By', default=lambda self: self.env.user)
    
    # Department and Service Classification  
    department = fields.Many2one('records.department', string='Department')
    service_category = fields.Selection([
        ('storage', 'Storage'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('scanning', 'Scanning'),
        ('consultation', 'Consultation')
    ], string='Service Category')
    
    # Approval Workflow
    requires_approval = fields.Boolean(string='Requires Approval', default=True)
    approval_level = fields.Selection([
        ('supervisor', 'Supervisor'),
        ('manager', 'Manager'),
        ('executive', 'Executive')
    ], string='Approval Level')
    approval_level_required = fields.Selection([
        ('none', 'None'),
        ('basic', 'Basic'),
        ('advanced', 'Advanced'),
        ('executive', 'Executive')
    ], string='Approval Level Required')
    primary_approver = fields.Many2one('res.users', string='Primary Approver')
    secondary_approver = fields.Many2one('res.users', string='Secondary Approver')
    final_approver = fields.Many2one('res.users', string='Final Approver')
    escalation_approver = fields.Many2one('res.users', string='Escalation Approver')
    escalation_contact = fields.Many2one('res.users', string='Escalation Contact')
    approver = fields.Many2one('res.users', string='Approver')
    approval_date = fields.Datetime(string='Approval Date')
    approval_deadline = fields.Datetime(string='Approval Deadline')
    approval_action = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('defer', 'Defer'),
        ('escalate', 'Escalate')
    ], string='Approval Action')
    approval_history_ids = fields.One2many('portal.request.approval', 'request_id', string='Approval History')
    auto_approve_threshold = fields.Float(string='Auto Approve Threshold')
    
    # Financial and Billing
    billable_hours = fields.Float(string='Billable Hours')
    hourly_rate = fields.Float(string='Hourly Rate')
    estimated_cost = fields.Float(string='Estimated Cost')
    actual_cost = fields.Float(string='Actual Cost')
    total_amount = fields.Float(string='Total Amount')
    material_costs = fields.Float(string='Material Costs')
    billing_method = fields.Selection([
        ('hourly', 'Hourly'),
        ('fixed', 'Fixed Price'),
        ('materials', 'Materials Based')
    ], string='Billing Method')
    billing_required = fields.Boolean(string='Billing Required')
    invoice_generated = fields.Boolean(string='Invoice Generated')
    
    # File and Document Management
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    attachment_count = fields.Integer(string='Attachment Count', compute='_compute_attachment_count')
    file_type = fields.Char(string='File Type')
    file_size = fields.Float(string='File Size (MB)')
    
    # Communication and Response
    comments = fields.Text(string='Comments')
    special_instructions = fields.Text(string='Special Instructions')
    response_required = fields.Boolean(string='Response Required', default=True)
    communication_log_ids = fields.One2many('portal.request.communication', 'request_id', string='Communication Log')
    communication_count = fields.Integer(string='Communication Count', compute='_compute_communication_count')
    communication_type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('portal', 'Portal'),
        ('in_person', 'In Person')
    ], string='Communication Type')
    communication_date = fields.Datetime(string='Communication Date')
    
    # Quality and Satisfaction
    customer_satisfaction = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Customer Satisfaction')
    customer_rating = fields.Integer(string='Customer Rating (1-10)')
    overall_satisfaction = fields.Float(string='Overall Satisfaction Score')
    quality_score = fields.Float(string='Quality Score')
    compliance_score = fields.Float(string='Compliance Score')
    customer_complaints = fields.Text(string='Customer Complaints')
    customer_wait_time = fields.Float(string='Customer Wait Time (Minutes)')
    
    # Completion and Efficiency Metrics
    completion_percentage = fields.Float(string='Completion Percentage', compute='_compute_completion_percentage')
    resolution_efficiency = fields.Float(string='Resolution Efficiency', compute='_compute_resolution_efficiency')
    variance = fields.Float(string='Variance', compute='_compute_variance')
    estimated_hours = fields.Float(string='Estimated Hours')
    milestone_name = fields.Char(string='Current Milestone')
    rework_required = fields.Boolean(string='Rework Required')
    
    # Related Request Management
    related_request_count = fields.Integer(string='Related Request Count', compute='_compute_related_request_count')
    
    # Security and Compliance
    confidential = fields.Boolean(string='Confidential')
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Confidentiality Level', default='internal')
    access_restrictions = fields.Text(string='Access Restrictions')
    naid_compliance_required = fields.Boolean(string='NAID Compliance Required')
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required')
    materials_required = fields.Text(string='Materials Required')
    
    # Additional fields to match view requirements
    notes = fields.Text(string='Notes')
    
    # Compute Methods
    @api.depends('status')
    def _compute_request_status(self):
        for record in self:
            record.request_status = record.status or 'new'
    
    @api.depends('sla_deadline')
    def _compute_sla_status(self):
        for record in self:
            if record.sla_deadline:
                now = fields.Datetime.now()
                if now > record.sla_deadline:
                    record.sla_status = 'breached'
                elif (record.sla_deadline - now).total_seconds() < 7200:  # 2 hours
                    record.sla_status = 'at_risk'
                else:
                    record.sla_status = 'on_time'
            else:
                record.sla_status = 'on_time'
    
    @api.depends('sla_deadline')
    def _compute_sla_breach_risk(self):
        for record in self:
            if record.sla_deadline:
                now = fields.Datetime.now()
                record.sla_breach_risk = (record.sla_deadline - now).total_seconds() < 3600  # 1 hour
            else:
                record.sla_breach_risk = False
    
    @api.depends('submission_date')
    def _compute_time_elapsed(self):
        for record in self:
            if record.submission_date:
                now = fields.Datetime.now()
                elapsed = (now - record.submission_date).total_seconds() / 3600
                record.time_elapsed = elapsed
            else:
                record.time_elapsed = 0.0
    
    @api.depends('target_completion_date')
    def _compute_time_remaining(self):
        for record in self:
            if record.target_completion_date:
                now = fields.Datetime.now()
                remaining = (record.target_completion_date - now).total_seconds() / 3600
                record.time_remaining = max(0.0, remaining)
            else:
                record.time_remaining = 0.0
    
    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)
    
    @api.depends('communication_log_ids')
    def _compute_communication_count(self):
        for record in self:
            record.communication_count = len(record.communication_log_ids)
    
    @api.depends('state', 'status')
    def _compute_completion_percentage(self):
        for record in self:
            if record.state == 'draft':
                record.completion_percentage = 0.0
            elif record.state == 'submitted':
                record.completion_percentage = 25.0
            elif record.state == 'approved':
                record.completion_percentage = 75.0
            elif record.state == 'rejected':
                record.completion_percentage = 100.0
            else:
                record.completion_percentage = 50.0
    
    @api.depends('processing_time', 'estimated_hours')
    def _compute_resolution_efficiency(self):
        for record in self:
            if record.estimated_hours and record.processing_time:
                record.resolution_efficiency = (record.estimated_hours / record.processing_time) * 100
            else:
                record.resolution_efficiency = 0.0
    
    @api.depends('actual_cost', 'estimated_cost')
    def _compute_variance(self):
        for record in self:
            if record.estimated_cost and record.actual_cost:
                record.variance = record.actual_cost - record.estimated_cost
            else:
                record.variance = 0.0
    
    @api.depends('partner_id')
    def _compute_related_request_count(self):
        for record in self:
            if record.partner_id:
                count = self.search_count([('partner_id', '=', record.partner_id.id), ('id', '!=', record.id)])
                record.related_request_count = count
            else:
                record.related_request_count = 0


# Related Models for One2many relationships
class PortalRequestMilestone(models.Model):
    _name = 'portal.request.milestone'
    _description = 'Portal Request SLA Milestone'
    
    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    name = fields.Char(string='Milestone Name', required=True)
    target_date = fields.Datetime(string='Target Date')
    completion_date = fields.Datetime(string='Completion Date')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue')
    ], string='Status', default='pending')


class PortalRequestApproval(models.Model):
    _name = 'portal.request.approval'
    _description = 'Portal Request Approval History'
    
    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    approver_id = fields.Many2one('res.users', string='Approver', required=True)
    approval_date = fields.Datetime(string='Approval Date', default=fields.Datetime.now)
    action = fields.Selection([
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('defer', 'Deferred'),
        ('escalate', 'Escalated')
    ], string='Action', required=True)
    comments = fields.Text(string='Comments')


class PortalRequestCommunication(models.Model):
    _name = 'portal.request.communication'
    _description = 'Portal Request Communication Log'
    
    request_id = fields.Many2one('portal.request', string='Request', required=True, ondelete='cascade')
    communication_date = fields.Datetime(string='Date', default=fields.Datetime.now)
    communication_type = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('portal', 'Portal'),
        ('in_person', 'In Person')
    ], string='Type', required=True)
    from_user_id = fields.Many2one('res.users', string='From')
    to_user_id = fields.Many2one('res.users', string='To')
    subject = fields.Char(string='Subject')
    message = fields.Text(string='Message')
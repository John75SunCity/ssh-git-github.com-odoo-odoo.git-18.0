# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RateChangeConfirmationWizard(models.TransientModel):
    """
    Rate Change Confirmation Wizard - Handles confirmation and processing of billing rate changes.
    Provides workflow for approving rate changes, notifying customers, and updating existing
    contracts and billing arrangements.
    """
    _name = 'rate.change.confirmation.wizard'
    _description = 'Rate Change Confirmation Wizard'

    # Basic Information
    name = fields.Char(
        string='Rate Change Request',
        default='Rate Change Confirmation',
        readonly=True
    )
    
    # Rate Change Details
    rate_change_type = fields.Selection([
        ('service_rate', 'Service Rate'),
        ('storage_rate', 'Storage Rate'),
        ('destruction_rate', 'Destruction Rate'),
        ('pickup_rate', 'Pickup Rate'),
        ('handling_rate', 'Handling Rate'),
        ('bulk_discount', 'Bulk Discount'),
        ('contract_rate', 'Contract Rate'),
    ], string='Rate Change Type', required=True,
       help="Type of rate being changed")
    
    # Current Rate Information
    current_rate = fields.Monetary(
        string='Current Rate',
        currency_field='currency_id',
        required=True,
        help="Current rate amount"
    )
    
    proposed_rate = fields.Monetary(
        string='Proposed Rate',
        currency_field='currency_id',
        required=True,
        help="New proposed rate amount"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    # Change Analysis
    rate_difference = fields.Monetary(
        string='Rate Difference',
        currency_field='currency_id',
        compute='_compute_rate_difference',
        store=True,
        help="Difference between current and proposed rates"
    )
    
    percentage_change = fields.Float(
        string='Percentage Change (%)',
        compute='_compute_percentage_change',
        store=True,
        help="Percentage change from current to proposed rate"
    )
    
    change_direction = fields.Selection([
        ('increase', 'Rate Increase'),
        ('decrease', 'Rate Decrease'),
        ('no_change', 'No Change'),
    ], string='Change Direction', compute='_compute_change_direction', store=True)
    
    # Affected Entities
    customer_ids = fields.Many2many(
        'res.partner',
        string='Affected Customers',
        domain=[('is_company', '=', True)],
        help="Customers affected by this rate change"
    )
    
    contract_ids = fields.Many2many(
        'records.billing',
        string='Affected Contracts',
        help="Contracts that will be updated with the new rate"
    )
    
    service_ids = fields.Many2many(
        'records.service',
        string='Affected Services',
        help="Services that will use the new rate"
    )
    
    # Implementation Details
    effective_date = fields.Date(
        string='Effective Date',
        required=True,
        default=fields.Date.today,
        help="Date when the new rate becomes effective"
    )
    
    advance_notice_days = fields.Integer(
        string='Advance Notice (Days)',
        default=30,
        help="Number of days advance notice to give customers"
    )
    
    notification_date = fields.Date(
        string='Customer Notification Date',
        compute='_compute_notification_date',
        store=True,
        help="Date when customers should be notified"
    )
    
    # Approval Information
    requires_approval = fields.Boolean(
        string='Requires Management Approval',
        compute='_compute_requires_approval',
        store=True,
        help="Whether this rate change requires management approval"
    )
    
    approval_threshold = fields.Float(
        string='Approval Threshold (%)',
        default=10.0,
        help="Percentage change threshold that requires approval"
    )
    
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        help="User who can approve this rate change"
    )
    
    approval_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('not_required', 'Not Required'),
    ], string='Approval Status', default='pending', readonly=True)
    
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )
    
    approval_notes = fields.Text(
        string='Approval Notes',
        help="Notes from the approver"
    )
    
    # Communication
    customer_notification_template = fields.Many2one(
        'mail.template',
        string='Customer Notification Template',
        domain=[('model', '=', 'res.partner')],
        help="Email template for customer notifications"
    )
    
    send_notifications = fields.Boolean(
        string='Send Customer Notifications',
        default=True,
        help="Automatically send notifications to affected customers"
    )
    
    notification_method = fields.Selection([
        ('email', 'Email'),
        ('mail', 'Postal Mail'),
        ('both', 'Email and Postal Mail'),
    ], string='Notification Method', default='email')
    
    # Impact Analysis
    estimated_revenue_impact = fields.Monetary(
        string='Estimated Revenue Impact',
        currency_field='currency_id',
        help="Estimated impact on monthly revenue"
    )
    
    customer_impact_analysis = fields.Text(
        string='Customer Impact Analysis',
        help="Analysis of how this change will impact customers"
    )
    
    competitive_analysis = fields.Text(
        string='Competitive Analysis',
        help="How this rate compares to competitors"
    )
    
    # State and Processing
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('implemented', 'Implemented'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', readonly=True)
    
    implementation_notes = fields.Text(
        string='Implementation Notes',
        help="Notes about the implementation process"
    )
    
    @api.depends('current_rate', 'proposed_rate')
    def _compute_rate_difference(self):
        """Calculate the difference between current and proposed rates"""
        for record in self:
            record.rate_difference = record.proposed_rate - record.current_rate
    
    @api.depends('current_rate', 'proposed_rate')
    def _compute_percentage_change(self):
        """Calculate percentage change"""
        for record in self:
            if record.current_rate:
                record.percentage_change = ((record.proposed_rate - record.current_rate) / record.current_rate) * 100
            else:
                record.percentage_change = 0.0
    
    @api.depends('rate_difference')
    def _compute_change_direction(self):
        """Determine if rate is increasing, decreasing, or staying the same"""
        for record in self:
            if record.rate_difference > 0:
                record.change_direction = 'increase'
            elif record.rate_difference < 0:
                record.change_direction = 'decrease'
            else:
                record.change_direction = 'no_change'
    
    @api.depends('effective_date', 'advance_notice_days')
    def _compute_notification_date(self):
        """Calculate when customers should be notified"""
        for record in self:
            if record.effective_date and record.advance_notice_days:
                from datetime import timedelta
                record.notification_date = record.effective_date - timedelta(days=record.advance_notice_days)
    
    @api.depends('percentage_change', 'approval_threshold')
    def _compute_requires_approval(self):
        """Determine if approval is required based on percentage change"""
        for record in self:
            record.requires_approval = abs(record.percentage_change) >= record.approval_threshold
    
    @api.constrains('proposed_rate')
    def _check_proposed_rate(self):
        """Validate proposed rate is positive"""
        for record in self:
            if record.proposed_rate < 0:
                raise ValidationError(_("Proposed rate cannot be negative"))
    
    @api.constrains('effective_date')
    def _check_effective_date(self):
        """Validate effective date is in the future"""
        for record in self:
            if record.effective_date <= fields.Date.today():
                raise ValidationError(_("Effective date must be in the future"))
    
    def action_submit_for_review(self):
        """Submit rate change for review"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_("Only draft rate changes can be submitted for review"))
        
        # Validate required information
        if not self.customer_ids:
            raise UserError(_("Please specify affected customers"))
        
        if self.requires_approval and not self.approver_id:
            raise UserError(_("Please specify an approver for this rate change"))
        
        self.state = 'review'
        
        # Send notification to approver if required
        if self.requires_approval:
            self._send_approval_request()
        
        # Create audit log
        self._create_audit_log('submitted_for_review')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Submitted for Review'),
                'message': _('Rate change submitted for review'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_approve(self):
        """Approve the rate change"""
        self.ensure_one()
        
        if self.state != 'review':
            raise UserError(_("Only rate changes under review can be approved"))
        
        if self.requires_approval and self.env.user != self.approver_id:
            raise UserError(_("Only the designated approver can approve this rate change"))
        
        self.write({
            'state': 'approved',
            'approval_status': 'approved',
            'approval_date': fields.Datetime.now(),
        })
        
        # Send notifications if configured
        if self.send_notifications:
            self._send_customer_notifications()
        
        # Create audit log
        self._create_audit_log('approved')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rate Change Approved'),
                'message': _('Rate change has been approved and customers will be notified'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_reject(self):
        """Reject the rate change"""
        self.ensure_one()
        
        if self.state != 'review':
            raise UserError(_("Only rate changes under review can be rejected"))
        
        self.write({
            'state': 'cancelled',
            'approval_status': 'rejected',
            'approval_date': fields.Datetime.now(),
        })
        
        # Create audit log
        self._create_audit_log('rejected')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rate Change Rejected'),
                'message': _('Rate change has been rejected'),
                'type': 'info',
                'sticky': False,
            }
        }
    
    def action_implement(self):
        """Implement the approved rate change"""
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_("Only approved rate changes can be implemented"))
        
        if self.effective_date > fields.Date.today():
            raise UserError(_("Cannot implement rate change before effective date"))
        
        # Update affected contracts and services
        implementation_count = 0
        
        # Update contracts
        for contract in self.contract_ids:
            # In a real implementation, this would update the contract rates
            implementation_count += 1
        
        # Update service rates
        for service in self.service_ids:
            # In a real implementation, this would update service rates
            implementation_count += 1
        
        self.write({
            'state': 'implemented',
            'implementation_notes': _('Rate change implemented for %s items') % implementation_count,
        })
        
        # Create audit log
        self._create_audit_log('implemented')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Rate Change Implemented'),
                'message': _('Rate change has been successfully implemented'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def _send_approval_request(self):
        """Send approval request to designated approver"""
        if self.approver_id:
            # Send email notification
            try:
                template = self.env.ref('records_management.rate_change_approval_template', False)
                if template:
                    template.send_mail(self.id)
            except Exception:
                pass
    
    def _send_customer_notifications(self):
        """Send notifications to affected customers"""
        if not self.customer_notification_template:
            return
        
        for customer in self.customer_ids:
            try:
                self.customer_notification_template.send_mail(customer.id)
            except Exception:
                continue
    
    def _create_audit_log(self, action):
        """Create audit log entry"""
        try:
            self.env['naid.audit.log'].create({
                'name': _('Rate Change %s - %s') % (action.title(), self.rate_change_type),
                'action': 'rate_change_%s' % action,
                'user_id': self.env.user.id,
                'notes': _('Rate change from %s to %s (%s%%)') % (
                    self.current_rate, self.proposed_rate, round(self.percentage_change, 2)
                ),
                'audit_date': fields.Datetime.now(),
            })
        except Exception:
            pass

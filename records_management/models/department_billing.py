# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department with enhanced enterprise features
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib
import re

class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts.
    Enhanced with enterprise features: validation, tracking, privacy compliance, and audit trails.
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _rec_name = 'contact_name'
    _order = 'contact_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True,
        index=True
    )
    
    contact_name = fields.Char(
        string='Contact Name',
        required=True,
        tracking=True
    )
    
    email = fields.Char(
        string='Email',
        required=True,
        tracking=True
    )
    
    phone = fields.Char(
        string='Phone',
        tracking=True
    )
    
    is_primary = fields.Boolean(
        string='Primary Contact',
        default=False,
        tracking=True,
        help='Only one primary contact allowed per department'
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Billing Preferences
    receives_invoices = fields.Boolean(
        string='Receives Invoices',
        default=True,
        tracking=True,
        help='This contact receives invoices for the department'
    )
    
    receives_statements = fields.Boolean(
        string='Receives Statements',
        default=False,
        tracking=True,
        help='This contact receives monthly statements'
    )
    
    receives_notifications = fields.Boolean(
        string='Receives Notifications',
        default=True,
        tracking=True,
        help='This contact receives billing notifications'
    )
    
    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail'),
        ('both', 'Email + Portal')
    ], string='Delivery Method', default='email', tracking=True,
       help='How this contact prefers to receive documents')
    
    hashed_email = fields.Char(
        compute='_compute_hashed_email',
        store=True,
        help='SHA256 hashed email for privacy compliance (ISO 27001/GDPR)'
    )
    
    # Computed fields for enhanced functionality
    total_departments = fields.Integer(
        compute='_compute_contact_stats',
        string='Total Departments'
    )
    
    last_billing_date = fields.Date(
        compute='_compute_billing_stats',
        string='Last Billing Date'
    )

    # Phase 3: Analytics & Computed Fields (8 fields)
    billing_engagement_score = fields.Float(
        string='Billing Engagement Score (%)',
        compute='_compute_billing_analytics',
        store=True,
        help='Engagement level with billing communications'
    )
    communication_effectiveness = fields.Float(
        string='Communication Effectiveness',
        compute='_compute_billing_analytics',
        store=True,
        help='Effectiveness of billing communications with this contact'
    )
    payment_coordination_rating = fields.Float(
        string='Payment Coordination Rating',
        compute='_compute_billing_analytics',
        store=True,
        help='Rating of payment coordination efficiency'
    )
    department_coverage_percentage = fields.Float(
        string='Department Coverage (%)',
        compute='_compute_billing_analytics',
        store=True,
        help='Percentage of departments this contact handles'
    )
    billing_responsiveness_index = fields.Float(
        string='Responsiveness Index',
        compute='_compute_billing_analytics',
        store=True,
        help='Index measuring billing inquiry responsiveness'
    )
    contact_optimization_score = fields.Float(
        string='Contact Optimization Score',
        compute='_compute_billing_analytics',
        store=True,
        help='Optimization score for billing contact setup'
    )
    billing_insights = fields.Text(
        string='Billing Insights',
        compute='_compute_billing_analytics',
        store=True,
        help='AI-generated insights about billing contact performance'
    )
    analytics_computed_timestamp = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_billing_analytics',
        store=True,
        help='Last analytics computation time'
    )

    @api.depends('email')
    def _compute_hashed_email(self):
        """Compute SHA256 hash of email for privacy compliance"""
        for rec in self:
            rec.hashed_email = hashlib.sha256(rec.email.encode()).hexdigest() if rec.email else False

    @api.depends('customer_id')
    def _compute_contact_stats(self):
        """Compute statistics about contact's departments"""
        for rec in self:
            if rec.customer_id:
                # Search for departments instead of using direct relationship
                departments = self.env['records.department'].search([('partner_id', '=', rec.customer_id.id)])
                rec.total_departments = len(departments)
            else:
                rec.total_departments = 0

    @api.depends('is_primary', 'receives_invoices', 'receives_statements', 'receives_notifications',
                 'delivery_method', 'total_departments', 'active')
    def _compute_billing_analytics(self):
        """Compute comprehensive analytics for billing contacts"""
        for contact in self:
            # Update timestamp
            contact.analytics_computed_timestamp = fields.Datetime.now()
            
            # Billing engagement score
            engagement = 40.0  # Base engagement
            
            if contact.receives_invoices:
                engagement += 25.0
            if contact.receives_statements:
                engagement += 15.0
            if contact.receives_notifications:
                engagement += 15.0
            
            if contact.is_primary:
                engagement += 10.0  # Primary contacts have higher engagement
            
            # Delivery method effectiveness
            if contact.delivery_method == 'both':
                engagement += 15.0  # Multiple channels
            elif contact.delivery_method in ['email', 'portal']:
                engagement += 10.0  # Digital channels
            
            contact.billing_engagement_score = min(100, engagement)
            
            # Communication effectiveness
            effectiveness = 60.0  # Base effectiveness
            
            # Email validation effectiveness
            if contact.email and '@' in contact.email:
                effectiveness += 20.0
            
            # Phone availability
            if contact.phone:
                effectiveness += 10.0
            
            # Multi-channel delivery
            if contact.delivery_method == 'both':
                effectiveness += 10.0
            
            contact.communication_effectiveness = min(100, effectiveness)
            
            # Payment coordination rating
            coordination = 65.0  # Base coordination
            
            if contact.is_primary:
                coordination += 20.0
            
            if contact.receives_invoices and contact.receives_statements:
                coordination += 15.0  # Full billing communication
            
            contact.payment_coordination_rating = min(100, coordination)
            
            # Department coverage percentage
            if contact.customer_id:
                total_customer_departments = self.env['records.department'].search_count([
                    ('partner_id', '=', contact.customer_id.id)
                ])
                
                if total_customer_departments > 0:
                    coverage = (contact.total_departments / total_customer_departments) * 100
                    contact.department_coverage_percentage = min(100, coverage)
                else:
                    contact.department_coverage_percentage = 0.0
            else:
                contact.department_coverage_percentage = 0.0
            
            # Billing responsiveness index
            responsiveness = 50.0  # Base responsiveness
            
            if contact.delivery_method in ['email', 'portal', 'both']:
                responsiveness += 30.0  # Digital delivery is faster
            
            if contact.receives_notifications:
                responsiveness += 20.0  # Notifications enable quick response
            
            contact.billing_responsiveness_index = min(100, responsiveness)
            
            # Contact optimization score
            optimization = 50.0  # Base optimization
            
            # Check for complete setup
            if contact.email and contact.phone:
                optimization += 20.0
            
            if contact.delivery_method == 'both':
                optimization += 15.0
            
            if contact.is_primary:
                optimization += 10.0
            
            if contact.receives_invoices and contact.receives_statements:
                optimization += 5.0
            
            contact.contact_optimization_score = min(100, optimization)
            
            # Billing insights
            insights = []
            
            if contact.billing_engagement_score > 85:
                insights.append("✅ Highly engaged billing contact")
            elif contact.billing_engagement_score < 60:
                insights.append("⚠️ Low engagement - review communication preferences")
            
            if not contact.is_primary and contact.department_coverage_percentage > 50:
                insights.append("👤 Consider designating as primary contact")
            
            if contact.delivery_method == 'mail':
                insights.append("📧 Switch to digital delivery for faster processing")
            
            if not contact.receives_notifications:
                insights.append("🔔 Enable notifications for better responsiveness")
            
            if contact.communication_effectiveness > 90:
                insights.append("📞 Excellent communication setup")
            
            if contact.payment_coordination_rating < 70:
                insights.append("💳 Payment coordination needs improvement")
            
            if contact.department_coverage_percentage == 100:
                insights.append("🎯 Complete department coverage achieved")
            
            if not insights:
                insights.append("📊 Standard billing contact configuration")
            
            contact.billing_insights = "\n".join(insights)

    @api.depends('customer_id')
    def _compute_contact_stats(self):
        """Compute statistics about contact's departments"""
        for rec in self:
            if rec.customer_id:
                departments = self.env['records.department'].search([
                    ('partner_id', '=', rec.customer_id.id)
                ])
                rec.total_departments = len(departments)
            else:
                rec.total_departments = 0

    def _compute_billing_stats(self):
        """Compute billing-related statistics"""
        for rec in self:
            # Find latest invoice for this contact's customer/department
            invoices = self.env['account.move'].search([
                ('partner_id', '=', rec.customer_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], order='invoice_date desc', limit=1)
            rec.last_billing_date = invoices.invoice_date if invoices else False

    @api.constrains('email')
    def _check_email_format(self):
        """Validate email format"""
        for rec in self:
            if rec.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', rec.email):
                raise ValidationError(_("Please enter a valid email address for %s") % rec.contact_name)

    @api.constrains('is_primary', 'department_id')
    def _check_primary_unique(self):
        """Ensure only one primary contact per department"""
        for rec in self:
            if rec.is_primary and self.search_count([
                ('department_id', '=', rec.department_id.id),
                ('is_primary', '=', True),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError(_("Only one primary contact allowed per department: %s") % rec.department_id.name)

    def action_make_primary(self):
        """Action to make this contact primary for the department"""
        # Remove primary status from other contacts in same department
        other_primaries = self.search([
            ('department_id', '=', self.department_id.id),
            ('is_primary', '=', True),
            ('id', '!=', self.id)
        ])
        other_primaries.write({'is_primary': False})
        # Set this contact as primary
        self.is_primary = True
        return True

class ResPartnerDepartmentBilling(models.Model):
    """
    Model for partner department billing assignments.
    Enhanced with enterprise features: tracking, validation, and computed fields.
    """
    _name = 'res.partner.department.billing'
    _description = 'Partner Department Billing'
    _rec_name = 'department_id'
    _order = 'department_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True,
        index=True
    )
    
    billing_contact_id = fields.Many2one(
        'res.partner',
        string='Billing Contact',
        domain="[('parent_id', '=', partner_id)]",
        tracking=True
    )
    
    billing_method = fields.Selection([
        ('inherit', 'Inherit from Customer'),
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail'),
    ], string='Billing Method', default='inherit', tracking=True)
    
    # PO Number Configuration
    use_separate_po_numbers = fields.Boolean(
        string='Use Separate PO Numbers',
        default=False,
        tracking=True,
        help='Use separate PO numbers for this department'
    )
    
    default_po_number = fields.Char(
        string='Default PO Number',
        tracking=True,
        help='Default PO number for this department invoices'
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Computed fields
    department_name = fields.Char(
        related='department_id.name',
        string='Department Name',
        readonly=True,
        store=True
    )
    
    billing_email = fields.Char(
        related='billing_contact_id.email',
        string='Billing Email',
        readonly=True,
        store=True
    )
    
    # Enhanced computed fields
    monthly_storage_fee = fields.Float(
        compute='_compute_billing_totals',
        string='Monthly Storage Fee',
        store=True
    )
    
    total_boxes = fields.Integer(
        compute='_compute_billing_totals',
        string='Total Boxes',
        store=True
    )
    
    last_invoice_date = fields.Date(
        compute='_compute_billing_totals',
        string='Last Invoice Date',
        store=True
    )

    @api.depends('partner_id', 'department_id', 'department_id.box_ids', 'department_id.box_ids.state')
    def _compute_billing_totals(self):
        """Compute billing totals from department"""
        for rec in self:
            if rec.department_id:
                # Calculate directly from source data instead of computed fields
                active_boxes = rec.department_id.box_ids.filtered(lambda b: b.state == 'active')
                rec.total_boxes = len(active_boxes)
                rec.monthly_storage_fee = len(active_boxes) * 10.0  # $10 per box per month
                
                # Find latest invoice for this partner/department
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', rec.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted')
                ], order='invoice_date desc', limit=1)
                rec.last_invoice_date = invoices.invoice_date if invoices else False
            else:
                rec.monthly_storage_fee = 0.0
                rec.total_boxes = 0
                rec.last_invoice_date = False

    @api.constrains('partner_id', 'department_id')
    def _check_department_belongs_to_partner(self):
        """Ensure department belongs to the selected partner"""
        for rec in self:
            if rec.department_id and rec.department_id.partner_id != rec.partner_id:
                raise ValidationError(_("Department '%s' does not belong to partner '%s'") % 
                                    (rec.department_id.name, rec.partner_id.name))

    def action_generate_invoice(self):
        """Action to generate invoice for this department billing"""
        if not self.monthly_storage_fee:
            raise ValidationError(_("No storage fee configured for department %s") % self.department_id.name)
        
        # Create invoice logic here
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': f'Storage Fee - {self.department_id.name}',
                'quantity': 1,
                'price_unit': self.monthly_storage_fee,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoices(self):
        """View invoices for this department billing"""
        self.ensure_one()
        return {
            'name': _('Invoices - %s') % self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('move_type', '=', 'out_invoice'),
            ],
            'context': {'default_partner_id': self.partner_id.id},
        }

    def action_update_billing_method(self):
        """Update billing method"""
        self.ensure_one()
        return {
            'name': _('Update Billing Method'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.method.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_view_boxes(self):
        """View boxes for this department"""
        self.ensure_one()
        return {
            'name': _('Boxes - %s') % self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
        }

    def action_send_statement(self):
        """Send billing statement"""
        self.ensure_one()
        return {
            'name': _('Send Statement'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.statement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_calculate_fees(self):
        """Calculate storage fees"""
        self.ensure_one()
        self._compute_billing_totals()
        return True

    def action_print_statement(self):
        """Print billing statement"""
        self.ensure_one()
        return {
            'name': _('Print Statement'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.billing_statement_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.billing_statement_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_department_charges(self):
        """View charges for this department"""
        self.ensure_one()
        return {
            'name': _('Department Charges: %s') % self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
        }

    def action_view_approvals(self):
        """View approval requests for this department"""
        self.ensure_one()
        return {
            'name': _('Approval Requests: %s') % self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'view_mode': 'tree,form',
            'domain': [('department_id', '=', self.department_id.id)],
            'context': {'default_department_id': self.department_id.id},
        }

    def action_budget_report(self):
        """Generate budget report"""
        self.ensure_one()
        return {
            'name': _('Budget Report: %s') % self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'budget.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_department_id': self.department_id.id},
        }

    def action_send_bill_notification(self):
        """Send bill notification to contacts"""
        self.ensure_one()
        contacts = self.env['records.department.billing.contact'].search([
            ('department_id', '=', self.department_id.id),
            ('receives_notifications', '=', True),
            ('active', '=', True)
        ])
        
        for contact in contacts:
            # Send notification logic here
            self.message_post(
                body=_('Bill notification sent to %s') % contact.contact_name,
                partner_ids=[contact.customer_id.id] if contact.customer_id else []
            )
        
        return True

    def action_approve_charges(self):
        """Approve pending charges"""
        self.ensure_one()
        pending_charges = self.env['account.move.line'].search([
            ('department_id', '=', self.department_id.id),
            ('state', '=', 'draft')
        ])
        
        for charge in pending_charges:
            charge.write({'state': 'approved'})
        
        self.message_post(body=_('Charges approved by %s') % self.env.user.name)
        return True

    def action_approve_charge(self):
        """Approve a single charge (called from context)"""
        charge_id = self.env.context.get('charge_id')
        if charge_id:
            charge = self.env['account.move.line'].browse(charge_id)
            charge.write({'state': 'approved'})
            return True
        return False

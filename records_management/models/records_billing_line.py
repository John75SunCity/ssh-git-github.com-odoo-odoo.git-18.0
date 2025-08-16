# -*- coding: utf-8 -*-

Records Billing Line Management Module

This module provides detailed billing line item tracking for the Records Management:
    pass
System. Each line item represents a specific billable service or product with quantity,
unit pricing, and departmental attribution for granular financial analysis.:
Key Features
- Detailed line item billing tracking
- Department contact association
- Automatic amount calculations
- Integration with advanced billing system
- NAID compliance audit trails

Business Processes
1. Line Item Creation: Automatic numbering and billing configuration association
2. Amount Calculation: Real-time total amount computation based on quantity and unit price
3. Department Attribution: Link billing lines to specific department contacts
4. Billable Service Tracking: Track which services are billable vs non-billable
5. Currency Management: Multi-currency support for international operations""":"
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingLine(models.Model):
    """Records Billing Line"""
    
        Detailed billing line item tracking for granular financial analysis:
    and departmental attribution of billable services and products.

    _name = "records.billing.line"
    _description = "Records Billing Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "config_id, date desc, name"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Line Item Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for this billing line item":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this billing line":
    

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Set to false to hide this record"
    

        # ============================================================================
    # BILLING CONFIGURATION RELATIONSHIPS
        # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Billing configuration this line item belongs to"
    

    billing_id = fields.Many2one(
        "advanced.billing",
        string="Advanced Billing",
        ondelete="cascade",
        help="Reference to advanced billing record"
    

    contact_id = fields.Many2one(
        "records.department.billing.contact",
        string="Department Contact",
        help="Department contact associated with this billing line"
    

        # ============================================================================
    # BILLING DETAILS
        # ============================================================================
    date = fields.Date(
        string="Billing Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        index=True,
        help="Date when this billing line was created"
    

    description = fields.Text(
        string="Description",
        help="Detailed description of the billable service or product"
    

    ,
    service_type = fields.Selection([))
        ("storage", "Storage Services"),
        ("retrieval", "Document Retrieval"),
        ("destruction", "Secure Destruction"),
        ("scanning", "Document Scanning"),
        ("delivery", "Pickup & Delivery"),
        ("consultation", "Consultation Services"),
        ("other", "Other Services"),
    
        help="Type of service being billed"

    # ============================================================================
        # PRICING AND CALCULATIONS
    # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        ,
    digits=(12, 3),
        default=1.0,
        required=True,
        help="Quantity of the service or product"
    

    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field="currency_id",
        required=True,
        help="Price per unit for this service or product":
    

    discount_percentage = fields.Float(
        string="Discount %",
        ,
    digits=(5, 2),
        default=0.0,
        help="Discount percentage applied to this line"
    

    discount_amount = fields.Monetary(
        string="Discount Amount",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,
        help="Calculated discount amount"
    

    subtotal = fields.Monetary(
        string="Subtotal",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,
        help="Subtotal before discount"
    

    amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_amounts",
        store=True,
        help="Final total amount after discount"
    

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    

        # ============================================================================
    # STATUS AND FLAGS
        # ============================================================================
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    
        help='Current status of the billing line'

    billable = fields.Boolean(
        string="Billable",
        default=True,
        tracking=True,
        help="Whether this line item is billable to the customer"
    

    invoiced = fields.Boolean(
        string="Invoiced",
        default=False,
        help="Whether this line has been included in an invoice"
    

        # ============================================================================
    # RELATED INFORMATION
        # ============================================================================
    partner_id = fields.Many2one(
        string="Customer",
        related="config_id.partner_id",
        store=True,
        help="Customer associated with this billing line"
    

    department_id = fields.Many2one(
        string="Department",
        related="contact_id.department_id",
        store=True,
        help="Department associated with this billing line"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')
        

    # ============================================================================
        # COMPUTED FIELDS
    # ============================================================================
    @api.depends("quantity", "unit_price", "discount_percentage")
    def _compute_amounts(self):
        """Compute subtotal, discount amount, and total amount"""
        for record in self:
            record.subtotal = record.quantity * record.unit_price
            record.discount_amount = record.subtotal * (record.discount_percentage / 100)
            record.amount = record.subtotal - record.discount_amount

    # ============================================================================
        # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering and validation"""
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == _("New"):
                vals["name") = self.env["ir.sequence"].next_by_code("records.billing.line") or _("New")
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track important changes"""
        result = super().write(vals)
        
        # Track status changes
        if "state" in vals:
            for record in self:
                record.message_post()
                    body=_("Billing line status changed to %s", vals["state"])
                
        
        return result

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm billing line"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Can only confirm draft billing lines"))
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Billing line confirmed"))

    def action_mark_invoiced(self):
        """Mark billing line as invoiced"""
        self.ensure_one()
        if self.state not in ['confirmed', 'invoiced']:
            raise ValidationError(_("Can only invoice confirmed billing lines"))
        
        self.write({)}
            'state': 'invoiced',
            'invoiced': True
        
        self.message_post(body=_("Billing line marked as invoiced"))

    def action_mark_paid(self):
        """Mark billing line as paid"""
        self.ensure_one()
        if self.state != 'invoiced':
            raise ValidationError(_("Can only mark invoiced lines as paid"))
        
        self.write({'state': 'paid'})
        self.message_post(body=_("Billing line marked as paid"))

    def action_cancel(self):
        """Cancel billing line"""
        self.ensure_one()
        if self.state == 'paid':
            raise ValidationError(_("Cannot cancel paid billing lines"))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Billing line cancelled"))

    def action_reset_to_draft(self):
        """Reset billing line to draft"""
        self.ensure_one()
        if self.state in ['paid', 'invoiced']:
            raise ValidationError(_("Cannot reset invoiced or paid lines to draft"))
        
        self.write({'state': 'draft'})
        self.message_post(body=_("Billing line reset to draft"))

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    def get_line_summary(self):
        """Get billing line summary for reports""":
        self.ensure_one()
        return {}
            'line_name': self.name,
            'service_type': self.service_type,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'discount_percentage': self.discount_percentage,
            'total_amount': self.amount,
            'currency': self.currency_id.name,
            'customer': self.partner_id.name if self.partner_id else '',:
            'department': self.department_id.name if self.department_id else '',:
            'status': self.state,
            'billable': self.billable,
        

    def apply_discount(self, discount_percentage):
        """Apply discount to billing line"""
        self.ensure_one()
        if not (0 <= discount_percentage <= 100):
            raise ValidationError(_("Discount percentage must be between 0 and 100"))
        
        self.write({'discount_percentage': discount_percentage})
        self.message_post()
            body=_("Discount of %s%% applied to billing line", discount_percentage)
        

    @api.model
    def create_from_service(self, config_id, service_data):
        """Create billing line from service data"""
        vals = {}
            'config_id': config_id,
            'service_type': service_data.get('service_type', 'other'),
            'description': service_data.get('description', ''),
            'quantity': service_data.get('quantity', 1.0),
            'unit_price': service_data.get('unit_price', 0.0),
            'date': service_data.get('date', fields.Date.today()),
        
        
        return self.create(vals)

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be positive"))

    @api.constrains('unit_price')
    def _check_unit_price(self):
        """Validate unit price is not negative"""
        for record in self:
            if record.unit_price < 0:
                raise ValidationError(_("Unit price cannot be negative"))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        """Validate discount percentage is within valid range"""
        for record in self:
            if not (0 <= record.discount_percentage <= 100):
                raise ValidationError(_("Discount percentage must be between 0 and 100"))

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = _("%(name)s - %(service)s (%(amount)s)", {)}
                'name': record.name,
                'service': record.service_type or 'Service',
                'amount': f"{record.amount:.2f} {record.currency_id.symbol or ''}"
            
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name, service type, or customer"""
        args = args or []
        domain = []
        
        if name:
            domain = []
                "|", "|", "|",
                ("name", operator, name),
                ("description", operator, name),
                ("service_type", operator, name),
                ("partner_id.name", operator, name),
            
        
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_billing_summary(self, domain=None):
        """Get billing summary statistics"""
        domain = domain or []
        
        lines = self.search(domain)
        
        return {}
            'total_lines': len(lines),
            'total_amount': sum(lines.mapped('amount')),
            'billable_amount': sum(lines.filtered('billable').mapped('amount')),
            'non_billable_amount': sum(lines.filtered(lambda r: not r.billable).mapped('amount')),
            'by_status': {}
                status[0]: {}
                    'count': len(lines.filtered(lambda r: r.state == status[0])),
                    'amount': sum(lines.filtered(lambda r: r.state == status[0]).mapped('amount'))
                
                for status in self._fields['state'].selection:
            
            'by_service_type': self._get_service_type_summary(lines),
        

    def _get_service_type_summary(self, lines):
        """Get summary by service type"""
        summary = {}
        for service_type in self._fields['service_type'].selection:
            type_lines = lines.filtered(lambda r: r.service_type == service_type[0])
            if type_lines:
                summary[service_type[1]] = {}
                    'count': len(type_lines),
                    'amount': sum(type_lines.mapped('amount')),
                    'quantity': sum(type_lines.mapped('quantity')),
                
        return summary

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    @api.model
    def generate_billing_report(self, date_from=None, date_to=None, partner_ids=None):
        """Generate comprehensive billing line report"""
        domain = []
        
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if partner_ids:
            domain.append(('partner_id', 'in', partner_ids))
        
        lines = self.search(domain)
        
        # Compile report data
        report_data = {}
            'period': {'from': date_from, 'to': date_to},
            'summary': self.get_billing_summary(domain),
            'lines': [line.get_line_summary() for line in lines],:
            'partners': self._get_partner_summary(lines),
            'departments': self._get_department_summary(lines),
        
        
        return report_data

    def _get_partner_summary(self, lines):
        """Get summary by partner"""
        partners = lines.mapped('partner_id')
        return {}
            partner.name: {}
                'total_lines': len(lines.filtered(lambda r: r.partner_id == partner)),
                'total_amount': sum(lines.filtered(lambda r: r.partner_id == partner).mapped('amount')),
                'billable_amount': sum(lines.filtered(lambda r: r.partner_id == partner and r.billable).mapped('amount')),
            
            for partner in partners if partner:
        

    def _get_department_summary(self, lines):
        """Get summary by department"""
        departments = lines.mapped('department_id')
        return {}
            dept.name: {}
                'total_lines': len(lines.filtered(lambda r: r.department_id == dept)),
                'total_amount': sum(lines.filtered(lambda r: r.department_id == dept).mapped('amount')),
            
            for dept in departments if dept:
        


    """"))))))))))))))))
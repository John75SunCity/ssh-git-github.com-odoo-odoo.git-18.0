# -*- coding: utf-8 -*-
"""
Advanced Billing Module

See RECORDS_MANAGEMENT_SYSTEM_MANUAL.md - Section 6: Advanced Billing Period Management Module
for comprehensive documentation, business processes, and integration details.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AdvancedBilling(models.Model):
    _name = "advanced.billing"
    _description = "Advanced Billing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", 
        string="Company", 
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users", 
        string="User", 
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # BILLING FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner", 
        string="Customer", 
        required=True,
        tracking=True
    )
    billing_period_id = fields.Many2one(
        "records.advanced.billing.period", 
        string="Billing Period",
        tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency", 
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    invoice_id = fields.Many2one(
        "account.move", 
        string="Invoice",
        tracking=True
    )
    payment_terms = fields.Selection(
        [
            ("immediate", "Immediate Payment"),
            ("net_15", "Net 15 Days"),
            ("net_30", "Net 30 Days"),
            ("net_45", "Net 45 Days"),
            ("net_60", "Net 60 Days"),
            ("custom", "Custom Terms"),
        ],
        string="Payment Terms",
        default="net_30",
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("invoiced", "Invoiced"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    line_ids = fields.One2many(
        "advanced.billing.line", 
        "billing_id", 
        string="Billing Lines"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    total_amount = fields.Monetary(
        string="Total Amount", 
        compute="_compute_total_amount", 
        store=True,
        currency_field="currency_id"
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("line_ids.price_total")
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = sum(record.line_ids.mapped("price_total"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm billing"""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft billing can be confirmed"))
        
        self.write({"state": "confirmed"})
        self.message_post(body=_("Advanced billing confirmed"))

    def action_generate_invoice(self):
        """Generate invoice"""
        self.ensure_one()
        if self.state != "confirmed":
            raise ValidationError(_("Only confirmed billing can be invoiced"))
        
        # Create invoice from billing lines
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': line.product_id.id,
                'name': line.name,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
            }) for line in self.line_ids],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            "state": "invoiced",
            "invoice_id": invoice.id,
        })
        
        self.message_post(body=_("Invoice generated: %s", invoice.name))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        """Mark billing as done"""
        self.ensure_one()
        if self.state != "invoiced":
            raise ValidationError(_("Only invoiced billing can be marked as done"))
        
        self.write({"state": "done"})
        self.message_post(body=_("Advanced billing completed"))

    def action_cancel(self):
        """Cancel billing"""
        self.ensure_one()
        if self.state in ["invoiced", "done"]:
            raise ValidationError(_("Cannot cancel invoiced or completed billing"))
        
        self.write({"state": "cancelled"})
        self.message_post(body=_("Advanced billing cancelled"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("total_amount")
    def _check_total_amount(self):
        for record in self:
            if record.total_amount < 0:
                raise ValidationError(_("Total amount cannot be negative"))


class AdvancedBillingLine(models.Model):
    _name = "advanced.billing.line"
    _description = "Advanced Billing Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Line Description", 
        compute="_compute_name", 
        store=True, 
        index=True
    )
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        "res.company", 
        default=lambda self: self.env.company, 
        required=True
    )
    user_id = fields.Many2one(
        "res.users", 
        default=lambda self: self.env.user, 
        tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # BILLING DETAILS
    # ============================================================================
    billing_id = fields.Many2one(
        "advanced.billing", 
        string="Billing", 
        required=True, 
        ondelete="cascade",
        index=True
    )
    product_id = fields.Many2one(
        "product.product", 
        string="Product",
        tracking=True
    )
    quantity = fields.Float(
        string="Quantity", 
        default=1.0,
        digits='Product Unit of Measure'
    )
    price_unit = fields.Float(
        string="Unit Price",
        digits='Product Price'
    )
    price_total = fields.Float(
        string="Total", 
        compute="_compute_price_total", 
        store=True,
        digits='Product Price'
    )

    # Container tracking for Records Management
    container_type = fields.Selection(
        [
            ('type_01', 'TYPE 01: Standard Box (1.2 CF)'),
            ('type_02', 'TYPE 02: Legal/Banker Box (2.4 CF)'),
            ('type_03', 'TYPE 03: Map Box (0.875 CF)'),
            ('type_04', 'TYPE 04: Odd Size/Temp Box (5.0 CF)'),
            ('type_06', 'TYPE 06: Pathology Box (0.042 CF)'),
        ],
        string="Container Type",
        help="Container type for Records Management billing"
    )
    
    # Service tracking
    service_type = fields.Selection(
        [
            ('storage', 'Storage Service'),
            ('pickup', 'Pickup Service'),
            ('shredding', 'Shredding Service'),
            ('retrieval', 'Document Retrieval'),
            ('destruction', 'Destruction Service'),
        ],
        string="Service Type",
        help="Type of Records Management service"
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("product_id", "quantity", "container_type", "service_type")
    def _compute_name(self):
        for line in self:
            if line.product_id:
                name_parts = [line.product_id.name]
                if line.container_type:
                    container_name = dict(line._fields['container_type'].selection).get(
                        line.container_type, line.container_type
                    )
                    name_parts.append(_("(%s)", container_name))
                if line.service_type:
                    service_name = dict(line._fields['service_type'].selection).get(
                        line.service_type, line.service_type
                    )
                    name_parts.append(_("- %s", service_name))
                line.name = _("%s x %s", " ".join(name_parts), line.quantity)
            else:
                line.name = _("Billing Line %s", line.sequence)

    @api.depends("quantity", "price_unit")
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("quantity", "price_unit")
    def _check_positive_values(self):
        for line in self:
            if line.quantity < 0:
                raise ValidationError(_("Quantity cannot be negative"))
            if line.price_unit < 0:
                raise ValidationError(_("Unit price cannot be negative"))


class RecordsAdvancedBillingPeriod(models.Model):
    _name = "records.advanced.billing.period"
    _description = "Advanced Billing Period"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "start_date desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Period Name", 
        compute="_compute_name", 
        store=True, 
        index=True
    )
    company_id = fields.Many2one(
        "res.company", 
        default=lambda self: self.env.company, 
        required=True
    )
    user_id = fields.Many2one(
        "res.users", 
        default=lambda self: self.env.user, 
        tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # PERIOD DETAILS
    # ============================================================================
    start_date = fields.Date(
        string="Start Date", 
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string="End Date", 
        required=True,
        tracking=True
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("closed", "Closed"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Period type for different billing cycles
    period_type = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
            ('custom', 'Custom Period'),
        ],
        string="Period Type",
        default='monthly',
        tracking=True
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    billing_ids = fields.One2many(
        "advanced.billing", 
        "billing_period_id", 
        string="Billings"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    billing_count = fields.Integer(
        string="Billing Count",
        compute="_compute_billing_count",
        store=True
    )
    
    total_period_amount = fields.Float(
        string="Total Period Amount",
        compute="_compute_total_period_amount",
        store=True
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("start_date", "end_date", "period_type")
    def _compute_name(self):
        for period in self:
            if period.start_date and period.end_date:
                period.name = _("Billing Period %s - %s", 
                              period.start_date, 
                              period.end_date)
            else:
                period.name = _("Billing Period %s", period.id or 'New')

    @api.depends("billing_ids")
    def _compute_billing_count(self):
        for period in self:
            period.billing_count = len(period.billing_ids)

    @api.depends("billing_ids.total_amount")
    def _compute_total_period_amount(self):
        for period in self:
            period.total_period_amount = sum(period.billing_ids.mapped("total_amount"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("start_date", "end_date")
    def _check_date_range(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date >= record.end_date:
                    raise ValidationError(_("Start date must be before end date"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_generate_storage_lines(self):
        """Generate Storage Lines - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_generate_storage_lines_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_generate_service_lines(self):
        """Generate Service Lines - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_generate_service_lines_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_activate_period(self):
        """Activate billing period"""
        self.ensure_one()
        if self.state != "draft":
            raise ValidationError(_("Only draft periods can be activated"))
        
        self.write({"state": "active"})
        self.message_post(body=_("Billing period activated"))

    def action_close_period(self):
        """Close billing period"""
        self.ensure_one()
        if self.state != "active":
            raise ValidationError(_("Only active periods can be closed"))
        
        self.write({"state": "closed"})
        self.message_post(body=_("Billing period closed"))

    def action_view_billings(self):
        """View period billings"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Period Billings - %s', self.name),
            'res_model': 'advanced.billing',
            'view_mode': 'tree,form',
            'domain': [('billing_period_id', '=', self.id)],
            'context': {'default_billing_period_id': self.id},
        }

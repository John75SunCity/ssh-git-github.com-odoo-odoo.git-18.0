# -*- coding: utf-8 -*-
"""
Bin Issue Record Model

Permanent record of bin issues for tracking, analytics, and compliance.
This model was moved from wizard file to proper models directory.
"""

from odoo import models, fields, _
from odoo.exceptions import UserError


class BinIssueRecord(models.Model):
    """
    Permanent record of bin issues for tracking, analytics, and compliance.
    """

    _name = 'bin.issue.record'
    _description = 'Bin Issue Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================
    name = fields.Char(string="Issue Reference", required=True, readonly=True)

    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Bin",
        required=True,
        readonly=True,
        index=True
    )

    issue_type = fields.Selection([
        ('damaged_customer_fault', 'Damaged - Customer Fault'),
        ('damaged_company_fault', 'Damaged - Company/Wear & Tear'),
        ('missing_label', 'Missing Label'),
        ('bad_barcode', 'Unreadable Barcode'),
        ('maintenance_required', 'General Maintenance Required'),
        ('lost_stolen', 'Lost or Stolen'),
        ('other', 'Other Issue'),
    ], string="Issue Type", required=True, readonly=True)

    issue_severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string="Severity", required=True, readonly=True)

    # ============================================================================
    # ISSUE DETAILS
    # ============================================================================
    description = fields.Text(string="Description", readonly=True)

    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer Location",
        readonly=True
    )

    location_id = fields.Many2one(
        comodel_name='records.location',
        string="Specific Location",
        readonly=True
    )

    # ============================================================================
    # TRACKING & RESOLUTION
    # ============================================================================
    work_order_id = fields.Many2one(
        comodel_name='project.task',
        string="Work Order",
        readonly=True
    )

    reported_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Reported By",
        required=True,
        readonly=True
    )

    report_date = fields.Datetime(
        string="Report Date",
        required=True,
        readonly=True
    )

    resolution_date = fields.Datetime(
        string="Resolution Date",
        tracking=True
    )

    resolution_status = fields.Selection([
        ('reported', 'Reported'),
        ('assigned', 'Assigned to Technician'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], string="Resolution Status", default='reported', tracking=True)

    # ============================================================================
    # BILLING & FAULT
    # ============================================================================
    customer_fault = fields.Boolean(string="Customer Fault", readonly=True)

    billing_amount = fields.Monetary(
        string="Billing Amount",
        currency_field='currency_id',
        readonly=True
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True
    )

    billed = fields.Boolean(string="Billed to Customer", tracking=True)
    payment_received = fields.Boolean(string="Payment Received", tracking=True)

    # ============================================================================
    # LOCATION DATA
    # ============================================================================
    gps_latitude = fields.Float(string="GPS Latitude", digits=(10, 7), readonly=True)
    gps_longitude = fields.Float(string="GPS Longitude", digits=(10, 7), readonly=True)

    # ============================================================================
    # RELATIONS
    # ============================================================================
    photo_ids = fields.One2many(
        comodel_name='mobile.photo',
        inverse_name='bin_issue_id',
        string="Issue Photos",
        readonly=True
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_bin(self):
        """View the related bin."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bin: %s') % self.bin_id.barcode,
            'res_model': 'shredding.service.bin',
            'res_id': self.bin_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_work_order(self):
        """View the related work order."""
        self.ensure_one()
        if not self.work_order_id:
            raise UserError(_("No work order associated with this issue."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order: %s') % self.work_order_id.name,
            'res_model': 'project.task',
            'res_id': self.work_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_mark_resolved(self):
        """Mark issue as resolved."""
        self.ensure_one()
        self.write({
            'resolution_status': 'resolved',
            'resolution_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Issue marked as resolved by %s") % self.env.user.name)

    def action_mark_billed(self):
        """Mark customer as billed."""
        self.ensure_one()
        if not self.customer_fault or self.billing_amount <= 0:
            raise UserError(_("Cannot mark as billed - no customer billing required for this issue."))

        self.write({'billed': True})
        self.message_post(body=_("Customer billed %s %s for bin issue") % (self.billing_amount, self.currency_id.symbol))

    def action_mark_paid(self):
        """Mark payment as received."""
        self.ensure_one()
        if not self.billed:
            raise UserError(_("Cannot mark as paid - customer has not been billed yet."))

        self.write({'payment_received': True})
        self.message_post(body=_("Payment received for bin issue billing"))

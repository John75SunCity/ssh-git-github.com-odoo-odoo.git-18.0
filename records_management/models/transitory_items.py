# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import UserError




class TransitoryItem(models.Model):
    _name = 'transitory.item'
    _description = 'Transitory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for the transitory item"
    )

    # Partner Relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this transitory item"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Active status of the item record"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    notes = fields.Text(
        string='Notes',
        help="Additional notes or comments about this item"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name for this item record"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name')
    def _compute_display_name(self):
        """Compute display name for the transitory item"""
        for record in self:
            record.display_name = record.name or _('New Transitory Item')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the transitory item"""

        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft items can be confirmed"))

        self.write({'state': 'confirmed'})
        self.message_post(body=_("Transitory item confirmed"))

    def action_complete(self):
        """Mark the transitory item as done"""

        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed items can be completed"))

        self.write({'state': 'done'})
        self.message_post(body=_("Transitory item completed"))

    def action_cancel(self):
        """Cancel the transitory item"""

        self.ensure_one()
        if self.state in ('done', 'cancelled'):
            raise UserError(_("Cannot cancel items that are already done or cancelled"))

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Transitory item cancelled"))

    def action_reset_to_draft(self):
        """Reset the transitory item to draft state"""

        self.ensure_one()
        if self.state == 'draft':
            raise UserError(_("Item is already in draft state"))

        self.write({'state': 'draft'})
        self.message_post(body=_("Transitory item reset to draft"))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_item_summary(self):
        """Get item summary for reporting"""
        self.ensure_one()
        return {
            'name': self.name,
            'state': self.state,
            'partner': self.partner_id.name if self.partner_id else None,
            'user': self.user_id.name if self.user_id else None,
            'notes': self.notes,
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_items_by_state(self, state):
        """Get transitory items filtered by state"""
        return self.search([('state', '=', state), ('active', '=', True)])

    def toggle_active(self):
        """Toggle active state of the item"""
        for record in self:
            record.active = not record.active
            if not record.active:
                record.message_post(body=_("Item deactivated"))
            else:
                record.message_post(body=_("Item reactivated"))

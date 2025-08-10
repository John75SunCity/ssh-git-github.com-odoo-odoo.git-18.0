# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockLotAttribute(models.Model):
    """Stock Lot Attribute Management"""

    _name = "stock.lot.attribute"
    _description = "Stock Lot Attribute"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Attribute Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the lot attribute",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this attribute",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the attribute"
    )

    # ============================================================================
    # ATTRIBUTE CONFIGURATION
    # ============================================================================
    attribute_type = fields.Selection(
        [
            ("text", "Text"),
            ("number", "Number"),
            ("date", "Date"),
            ("boolean", "Boolean"),
            ("selection", "Selection"),
        ],
        string="Attribute Type",
        required=True,
        default="text",
        help="Type of attribute value",
    )
    description = fields.Text(
        string="Description", help="Detailed description of this attribute"
    )
    required = fields.Boolean(
        string="Required", default=False, help="Whether this attribute is mandatory"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order sequence"
    )

    # ============================================================================
    # SELECTION OPTIONS (for selection type attributes)
    # ============================================================================
    selection_option_ids = fields.One2many(
        "stock.lot.attribute.option",
        "attribute_id",
        string="Selection Options",
        help="Available options for selection type attributes",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        tracking=True,
        help="Current state of the attribute",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    lot_attribute_value_ids = fields.One2many(
        "stock.lot.attribute.value",
        "attribute_id",
        string="Attribute Values",
        help="Values assigned to lots for this attribute",
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
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the attribute"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft attributes can be confirmed."))
        self.write({"state": "confirmed"})
        self.message_post(body=_("Attribute confirmed"))

    def action_archive(self):
        """Archive the attribute"""
        self.ensure_one()
        self.write({"state": "archived", "active": False})
        self.message_post(body=_("Attribute archived"))

    def action_activate(self):
        """Activate archived attribute"""
        self.ensure_one()
        self.write({"state": "confirmed", "active": True})
        self.message_post(body=_("Attribute activated"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_attribute_summary(self):
        """Get summary information for this attribute"""
        self.ensure_one()
        return {
            "name": self.name,
            "type": self.attribute_type,
            "required": self.required,
            "state": self.state,
            "value_count": len(self.lot_attribute_value_ids),
        }

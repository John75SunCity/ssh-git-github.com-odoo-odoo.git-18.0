# -*- coding: utf-8 -*-
"""
Shredding Picklist Item Model

Individual items on shredding picklists for destruction tracking.
"""

from odoo import models, fields, api, _


class ShreddingPicklistItem(models.Model):
    """Shredding Picklist Item"""

    _name = "shredding.picklist.item"
    _description = "Shredding Picklist Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "picklist_id, sequence, container_id"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Description",
        required=True,
        tracking=True
    )

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    picklist_id = fields.Many2one(
        "shredding.picklist",
        string="Picklist",
        required=True,
        ondelete="cascade",
        index=True
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container",
        required=True
    )

    # ============================================================================
    # ITEM DETAILS
    # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True
    )

    weight_kg = fields.Float(
        string="Weight (kg)",
        help="Weight in kilograms"
    )

    # ============================================================================
    # STATUS TRACKING
    # ============================================================================
    status = fields.Selection([
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('shredded', 'Shredded'),
        ('certified', 'Certified')
    ], string='Status', default='pending', required=True, tracking=True)

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")  
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

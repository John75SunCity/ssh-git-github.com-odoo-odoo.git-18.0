# -*- coding: utf-8 -*-
from odoo import models, fields


class ShreddingService(models.Model):
    """FSM integration extension for the core shredding.service model.

    Note: We extend the existing records_management model rather than inheriting
    from a non-existent `fsm.order`. All FSM-specific links should be added here
    as additional fields/methods while preserving the base behavior.
    """

    # Extend existing model defined in records_management
    _inherit = 'shredding.service'

    # Example FSM-related flag (safe additive field)
    is_certified_destruction = fields.Boolean(
        string="Certified Destruction",
        default=True,
        help="Indicates whether this shredding service typically includes NAID-certified destruction.",
    )

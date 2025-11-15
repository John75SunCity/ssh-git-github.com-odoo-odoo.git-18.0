# -*- coding: utf-8 -*-
"""
Saved Search Presets Model

Allows users to save frequently used search criteria for quick access.
Supports physical inventory search across containers, file folders, and documents.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

from odoo import models, fields, api
import json


class RecordsSavedSearch(models.Model):
    """User-defined saved search presets for physical inventory"""

    _name = 'records.saved.search'
    _description = 'Saved Inventory Search Preset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================

    name = fields.Char(
        string='Search Name',
        required=True,
        help="Name for this saved search preset"
    )

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        help="User who created this saved search"
    )

    filters = fields.Text(
        string='Filter Criteria',
        required=True,
        help="JSON-encoded search filter criteria"
    )

    is_default = fields.Boolean(
        string='Default Search',
        default=False,
        help="Use this search as default when opening inventory"
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    create_date = fields.Datetime(
        string='Created On',
        readonly=True
    )

    last_used = fields.Datetime(
        string='Last Used',
        readonly=True,
        help="Last time this search was executed"
    )

    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True,
        help="Number of times this search has been used"
    )

    # ============================================================================
    # METHODS
    # ============================================================================

    @api.model
    def get_filters_dict(self):
        """
        Parse JSON filters into Python dictionary
        
        Returns:
            dict: Filter criteria as dictionary
        """
        self.ensure_one()
        try:
            return json.loads(self.filters)
        except (json.JSONDecodeError, TypeError):
            return {}

    def execute_search(self):
        """
        Execute this saved search and return results
        
        Updates usage tracking (last_used, usage_count)
        """
        self.ensure_one()

        # Update usage tracking
        self.write({
            'last_used': fields.Datetime.now(),
            'usage_count': self.usage_count + 1,
        })

        # Get filter criteria
        filters = self.get_filters_dict()

        # Return URL with filters applied
        base_url = '/my/inventory/advanced_search'
        params = '&'.join([f"{k}={v}" for k, v in filters.items()])

        return {
            'type': 'ir.actions.act_url',
            'url': f"{base_url}?{params}",
            'target': 'self',
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure only one default search per user"""
        for vals in vals_list:
            if vals.get('is_default'):
                # Unset other default searches for this user
                self.search([
                    ('user_id', '=', vals.get('user_id', self.env.user.id)),
                    ('is_default', '=', True)
                ]).write({'is_default': False})

        return super().create(vals_list)

    def write(self, vals):
        """Ensure only one default search per user"""
        if vals.get('is_default'):
            # Unset other default searches for this user
            for record in self:
                self.search([
                    ('user_id', '=', record.user_id.id),
                    ('is_default', '=', True),
                    ('id', '!=', record.id)
                ]).write({'is_default': False})

        return super().write(vals)

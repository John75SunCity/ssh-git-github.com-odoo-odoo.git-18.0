# -*- coding: utf-8 -*-
"""
Cross-Department Sharing Rule Module

This module manages access rules created for cross-department sharing.
It tracks temporary access permissions and handles their automatic expiration.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields


class CrossDepartmentSharingRule(models.Model):
    """
    Cross-Department Sharing Rule Model

    Tracks access rules created for cross-department sharing.
    Used for managing and revoking temporary access permissions.
    """

    _name = "cross.department.sharing.rule"
    _description = "Cross-Department Sharing Access Rules"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _table = "cross_department_sharing_rule"

    sharing_id = fields.Many2one("cross.department.sharing", string="Sharing Record", required=True, ondelete="cascade")
    rule_id = fields.Many2one("ir.rule", string="Access Rule", required=True, ondelete="cascade")
    expires_at = fields.Datetime(string="Expires At", help="When this access rule should be automatically removed")

    _sql_constraints = [
        (
            "unique_sharing_rule",
            "unique(sharing_id, rule_id)",
            "Each sharing record can only have one rule per access rule.",
        ),
    ]

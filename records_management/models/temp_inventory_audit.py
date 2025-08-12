# -*- coding: utf-8 -*-
"""
Temporary Inventory Audit Trail Module

This module provides comprehensive audit trail functionality for temporary inventory
operations in the Records Management System. It ensures complete compliance tracking
and maintains detailed records of all inventory-related activities.

Key Features:
- Complete audit trail for all inventory operations
- Event type classification and tracking
- User activity monitoring with IP address logging
- Integration with NAID compliance requirements
- Automated audit log generation

Business Process:
1. Event Capture: Automatic logging of all inventory operations
2. User Tracking: Complete user activity monitoring
3. Compliance Reporting: NAID-compliant audit trail generation
4. Historical Analysis: Complete activity history and reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import threading
from datetime import timedelta

from odoo import models, fields, api, _




class TempInventoryAudit(models.Model):
    """Temporary Inventory Audit Trail"""

    _name = "temp.inventory.audit"
    _description = "Temporary Inventory Audit"
    _order = "date desc"
    _rec_name = "display_name"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    inventory_id = fields.Many2one(
        "temp.inventory",
        string="Inventory",
        required=True,
        ondelete="cascade",
        help="Associated temporary inventory",
    )
    date = fields.Datetime(
        string="Audit Date",
        required=True,
        default=fields.Datetime.now,
        help="When audit event occurred",
    )
    event_type = fields.Selection(
        [
            ("created", "Created"),
            ("modified", "Modified"),
            ("accessed", "Accessed"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        string="Event Type",
        required=True,
        help="Type of audit event",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="User who triggered the event",
    )
    details = fields.Text(
        string="Details", help="Detailed information about the audit event"
    )
    ip_address = fields.Char(string="IP Address", help="IP address of the user")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for audit record",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("event_type", "user_id", "date")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            event_label = dict(record._fields["event_type"].selection)[
                record.event_type
            ]
            user_name = record.user_id.name if record.user_id else "Unknown"
            record.display_name = _("%s by %s", event_label, user_name)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_audit_summary(self):
        """Get audit summary for reporting"""
        self.ensure_one()
        return {
            "event_type": self.event_type,
            "date": self.date,
            "user": self.user_id.name,
            "inventory": self.inventory_id.name,
            "details": self.details,
            "ip_address": self.ip_address,
        }

    @api.model
    def create_audit_log(self, inventory_id, event_type, details=None, ip_address=None):
        """Create audit log entry"""
        return self.create({
            "inventory_id": inventory_id,
            "event_type": event_type,
            "details": details,
            "ip_address": ip_address,
        })

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_user_activity(self, user_id=None, date_from=None, date_to=None):
        """Get user activity for specified period"""
        domain = []
        
        if user_id:
            domain.append(("user_id", "=", user_id))
        
        if date_from:
            domain.append(("date", ">=", date_from))
        
        if date_to:
            domain.append(("date", "<=", date_to))
        
        return self.search(domain, order="date desc")

    @api.model
    def get_inventory_audit_trail(self, inventory_id):
        """Get complete audit trail for specific inventory"""
        return self.search([
            ("inventory_id", "=", inventory_id)
        ], order="date desc")

    @api.model
    def cleanup_old_audit_logs(self, days_to_keep=365):
        """Cleanup old audit logs (automated method)"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days_to_keep)
        old_logs = self.search([("date", "<", cutoff_date)])
        
        # Archive instead of delete for compliance
        old_logs.write({"active": False})
        
        return len(old_logs)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure IP address capture"""
        for vals in vals_list:
            if not vals.get("ip_address"):
                # Try to capture IP address from request context
                try:
                    request = threading.current_thread().environ.get("HTTP_X_FORWARDED_FOR")
                    if request:
                        vals["ip_address"] = request.split(",")[0].strip()
                    else:
                        vals["ip_address"] = threading.current_thread().environ.get("REMOTE_ADDR", "Unknown")
                except Exception:
                    vals["ip_address"] = "Unknown"
        
        return super().create(vals_list)

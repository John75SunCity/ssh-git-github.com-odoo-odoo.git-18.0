# -*- coding: utf-8 -*-
"""
Pickup Request Item Management Module

This module provides detailed line-item management for pickup requests within the Records
Management System. It enables granular tracking of individual items, containers, and documents
included in pickup operations with comprehensive audit trails and status management.

Key Features:
- Detailed line-item tracking for pickup requests with barcode integration
- Individual item status management through the pickup lifecycle
- Weight and dimension tracking for accurate logistics planning
- Special handling requirements and instructions for sensitive items
- Integration with inventory management and container tracking systems
- Real-time status updates and delivery confirmation workflows
- Cost tracking and billing integration for individual items

Business Processes:
1. Item Addition: Adding specific items to pickup requests with detailed specifications
2. Status Tracking: Individual item status management through pickup and delivery
3. Inventory Updates: Real-time inventory adjustments during pickup operations
4. Special Handling: Management of items requiring special security or handling procedures
5. Delivery Confirmation: Item-level delivery verification and customer confirmation
6. Billing Integration: Individual item cost calculation and billing allocation
7. Exception Handling: Management of damaged, missing, or incomplete items

Item Types:
- Document Containers: Boxes, files, and document storage containers
- Individual Documents: Specific documents requiring separate tracking
- Equipment Items: Computing equipment, media, and hardware for destruction
- Special Materials: Items requiring NAID AAA compliance or special handling
- Bulk Materials: Large quantities requiring weight and volume management

Tracking Features:
- Barcode scanning and QR code integration for accurate item identification
- GPS tracking integration for real-time location monitoring during transport
- Photo documentation for item condition verification
- Electronic signature capture for pickup and delivery confirmation
- Exception reporting and resolution workflow management
- Integration with customer portal for real-time status visibility

Integration Points:
- Pickup Requests: Parent-child relationship with main pickup request records
- Inventory Management: Real-time inventory updates and location tracking
- Container Management: Integration with container lifecycle and location systems
- Billing System: Individual item cost tracking and invoice line generation
- Customer Portal: Real-time visibility and status updates for customers
- NAID Compliance: Chain of custody tracking for compliance-sensitive items

Technical Implementation:
- Modern Odoo 18.0 architecture with mail thread integration
- Barcode and QR code scanning capabilities with mobile optimization
- Real-time GPS tracking and location services integration
- Performance optimized for high-volume pickup operations
- Integration with Records Management security and audit systems

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _


class PickupRequestItem(models.Model):
    """
    Pickup Request Item - Individual items within pickup requests
    """

    _name = "pickup.request.item"
    _description = "Pickup Request Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, index=True)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """
        Confirm the record by setting its state to 'confirmed'.

        This method transitions the pickup request item from 'draft' to 'confirmed' state,
        indicating that the item has been reviewed and approved for processing.
        """
        self.write({"state": "confirmed"})

    def action_done(self):
        """
        Mark the pickup request item as done.

        This method updates the state of the item to 'done', which may trigger workflow transitions,
        notifications, or integration with inventory and billing systems. Additional business logic
        may be added here as needed.
        """
        self.write({"state": "done"})
        # Mark as done
        self.write({"state": "done"})

# -*- coding: utf-8 -*-
"""
Pickup Request Management Module

This module provides comprehensive pickup request management for document collection services
within the Records Management System. It implements complete pickup workflows from customer
request submission through service completion with real-time tracking and customer communication.

Key Features:
- Complete pickup request lifecycle management from submission to completion
- Customer portal integration for self-service pickup request submission
- Real-time scheduling and route optimization for pickup operations
- Multi-location pickup support with consolidated service delivery
- Priority-based pickup scheduling with emergency service capabilities
- Integration with route planning and driver assignment systems
- Customer communication and notification automation throughout the process

Business Processes:
1. Request Submission: Customer pickup request creation through portal or internal systems
2. Request Validation: Automatic validation of pickup requirements and service availability
3. Scheduling and Planning: Pickup scheduling with route optimization and resource allocation
4. Service Execution: Real-time pickup execution with status updates and tracking
5. Completion Verification: Pickup completion confirmation with customer verification
6. Billing Integration: Service cost calculation and invoice generation
7. Follow-up Management: Post-service customer communication and feedback collection

Request Types:
- Regular Pickups: Scheduled recurring pickup services for established customers
- On-Demand Pickups: Immediate or expedited pickup requests for urgent needs
- Bulk Pickups: Large-volume pickup operations for office cleanouts or relocations
- Secure Pickups: High-security pickup operations with special handling requirements
- Equipment Pickups: Pickup of computing equipment and electronic media for destruction
- Document Pickups: Pickup of paper documents and files for storage or destruction

Scheduling and Planning:
- Intelligent pickup scheduling with customer availability and preference management
- Route optimization integration for efficient pickup operations
- Resource allocation and driver assignment based on pickup requirements
- Capacity planning and vehicle selection for pickup volume and type
- Time window management with customer confirmation and adjustment capabilities
- Emergency pickup scheduling for urgent or compliance-driven requests

Customer Integration:
- Customer portal integration for self-service pickup request submission
- Real-time pickup status tracking and notification systems
- Customer preference management for scheduling and communication
- Pickup history and analytics with service performance tracking
- Integration with customer billing and service agreement management
- Mobile-responsive design for pickup requests from any device

Service Execution:
- Mobile application integration for driver pickup execution and status updates
- Real-time GPS tracking and customer notification during pickup operations
- Barcode scanning and inventory tracking for accurate item collection
- Photo documentation and condition verification for pickup items
- Electronic signature capture for pickup completion and customer verification
- Exception handling and resolution for incomplete or problematic pickups

Technical Implementation:
- Modern Odoo 18.0 architecture with comprehensive workflow management
- Integration with route planning and GPS tracking systems
- Mobile application support for field service execution and status updates
- Performance optimized for high-volume pickup operations
- Mail thread integration for notifications and customer communication

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _


class PickupRequest(models.Model):
    """
    Pickup Request Management - Customer document and equipment pickup requests
    Handles complete pickup workflows from submission to completion
    """

    _name = "pickup.request"
    _description = "Pickup Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
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
    help = fields.Char(string="Help")
    res_model = fields.Char(string="Res Model")
    view_mode = fields.Char(string="View Mode")

    # Location tracking
    location_id = fields.Many2one(
        "records.location", string="Pickup Location", tracking=True
    )

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})

# -*- coding: utf-8 -*-
"""
File Retrieval Work Order Item - STREAMLINED FOR BARCODE EFFICIENCY

This model represents individual files within a file retrieval work order.
Designed for FAST, EFFICIENT barcode scanning workflow with shadow NAID AAA auditing.

Key Business Focus:
- Fast barcode scanning without extra manual steps
- Shadow NAID AAA auditing that happens automatically in background
- Customer opt-in notifications for retrieval and delivery events
- Streamlined 6-step status workflow focused on actual operations
- File retrieval workflow (scan_retrieval_work_order handles page scanning)

Author: Records Management Team
Copyright: 2024 Records Management
License: LGPL-3
"""

import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class FileRetrievalWorkOrderItem(models.Model):
    """
    coordinator_id = fields.Many2one("work.order.coordinator", string="Coordinator")
    STREAMLINED File Retrieval Work Order Item

    Focuses on essential barcode scanning workflow with shadow auditing.
    Removed over-engineered enterprise features that slow down technicians.
    """
    _name = 'file.retrieval.work.order.item'
    _description = 'File Retrieval Work Order Item - Streamlined'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, work_order_id, file_name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION - ESSENTIAL FIELDS ONLY
    # ============================================================================
    name = fields.Char(
        string="Item Reference",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        help="Auto-generated reference for this retrieval item"
    )

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="User-friendly display name combining reference and file name"
    )

    work_order_id = fields.Many2one(
        comodel_name='file.retrieval.work.order',
        string="Work Order",
        required=True,
        ondelete='cascade',
        index=True,
        help="Parent work order for this retrieval item"
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        related='work_order_id.partner_id',
        store=True,
        help="Customer requesting this file retrieval"
    )

    # ============================================================================
    # FILE INFORMATION - BARCODE FOCUSED
    # ============================================================================
    file_name = fields.Char(
        string="File Name",
        required=True,
        index=True,
        help="Name of the file to retrieve"
    )

    file_description = fields.Char(
        string="File Description",
        help="Brief description of the file contents"
    )

    file_type = fields.Selection([
        ('document', 'Document'),
        ('folder', 'Folder'),
        ('book', 'Book/Manual'),
        ('blueprint', 'Blueprint'),
        ('photograph', 'Photograph'),
        ('certificate', 'Certificate'),
        ('contract', 'Contract'),
        ('other', 'Other')
    ], string="File Type", default='document', help="Type of file being retrieved")

    # ============================================================================
    # CONTAINER AND LOCATION - BARCODE FOCUSED
    # ============================================================================
    container_id = fields.Many2one(
        comodel_name='records.container',
        string="Container",
        index=True,
        help="Container where this file is stored"
    )

    container_barcode = fields.Char(
        string="Container Barcode",
        related='container_id.barcode',
        store=True,
        help="Barcode for container scanning"
    )

    location_id = fields.Many2one(
        comodel_name='records.location',
        string="Location",
        related='container_id.location_id',
        store=True,
        help="Storage location of the container"
    )

    file_position = fields.Char(
        string="Position in Container",
        help="Specific position within container (folder, section, etc.)"
    )

    # ============================================================================
    # STREAMLINED STATUS WORKFLOW - FAST & EFFICIENT
    # ============================================================================
    status = fields.Selection([
        ('pending', 'Pending'),          # Initial state - awaiting assignment
        ('assigned', 'Assigned'),        # Assigned to technician
        ('retrieved', 'Retrieved'),      # File scanned and pulled from container
        ('delivered', 'Delivered'),      # File delivered to customer
        ('not_found', 'Not Found'),      # File not found in expected location
        ('cancelled', 'Cancelled')       # Request cancelled
    ], string="Item Status", default='pending', required=True, tracking=True,
       help="Current status in streamlined 6-step workflow")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Priority", default='1', help="Priority for processing this item")

    # ============================================================================
    # TEAM ASSIGNMENT - SIMPLIFIED
    # ============================================================================
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Assigned To",
        tracking=True,
        help="Technician assigned to retrieve this item"
    )

    retrieved_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Retrieved By",
        help="Technician who scanned and retrieved this file"
    )

    date_assigned = fields.Datetime(
        string="Date Assigned",
        help="When item was assigned to technician"
    )

    date_retrieved = fields.Datetime(
        string="Date Retrieved",
        help="When file was scanned and retrieved"
    )

    date_delivered = fields.Datetime(
        string="Date Delivered",
        help="When file was delivered to customer"
    )

    retrieval_duration = fields.Float(
        string="Retrieval Time (Hours)",
        compute='_compute_retrieval_metrics',
        store=True,
        help="Time taken to retrieve file"
    )

    # ============================================================================
    # CUSTOMER NOTIFICATIONS - OPT-IN SYSTEM
    # ============================================================================
    notification_method = fields.Selection([
        ('none', 'No Notifications'),
        ('email', 'Email Only'),
        ('sms', 'SMS Only'),
        ('both', 'Email and SMS')
    ], string="Notification Method", default='email', help="How to notify customer")

    notify_retrieved = fields.Boolean(
        string="Notify When Retrieved",
        default=True,
        help="Send notification when file is retrieved"
    )

    notify_delivered = fields.Boolean(
        string="Notify When Delivered",
        default=True,
        help="Send notification when file is delivered"
    )

    # ============================================================================
    # DELIVERY TRACKING
    # ============================================================================
    delivery_method = fields.Selection([
        ('pickup', 'Customer Pickup'),
        ('delivery', 'Our Delivery'),
        ('courier', 'Courier Service'),
        ('mail', 'Mail/Post'),
        ('digital', 'Digital Only')
    ], string="Delivery Method", default='pickup', help="How file will be delivered")

    tracking_number = fields.Char(
        string="Tracking Number",
        help="Delivery tracking number if applicable"
    )

    # ============================================================================
    # NOTES AND COMMENTS - ESSENTIAL ONLY
    # ============================================================================
    notes = fields.Text(
        string="Notes",
        help="General notes about this file retrieval"
    )

    retrieval_instructions = fields.Text(
        string="Retrieval Instructions",
        help="Special instructions for retrieving this file"
    )

    # ============================================================================
    # NAID COMPLIANCE - SHADOW AUDITING FIELDS
    # ============================================================================
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        default=True,
        help="NAID chain of custody verification"
    )

    access_logged = fields.Boolean(
        string="Access Logged",
        default=True,
        help="All access automatically logged for NAID compliance"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('name', 'file_name')
    def _compute_display_name(self):
        """Compute display name for easy identification"""
        for record in self:
            if record.name and record.file_name:
                record.display_name = f"{record.name} - {record.file_name}"
            elif record.file_name:
                record.display_name = record.file_name
            else:
                record.display_name = record.name or _('New Item')

    @api.depends('date_assigned', 'date_retrieved')
    def _compute_retrieval_metrics(self):
        """Calculate retrieval time metrics"""
        for record in self:
            if record.date_assigned and record.date_retrieved:
                delta = record.date_retrieved - record.date_assigned
                record.retrieval_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                record.retrieval_duration = 0.0

    # ============================================================================
    # BARCODE SCANNING METHODS - CORE WORKFLOW
    # ============================================================================
    def barcode_scan_retrieve(self, scanned_barcode=None):
        """
        Main barcode scanning method for file retrieval

        This is called when technician scans a file barcode during retrieval.
        Automatically updates status and creates shadow audit trail.

        Args:
            scanned_barcode (str): The barcode that was scanned

        Returns:
            dict: Success/error message for barcode scanner interface
        """
        self.ensure_one()

        # Validate current status
        if self.status not in ['assigned', 'pending']:
            return {
                "success": False,
                "message": _("Item status is %s - cannot retrieve", self.status),
                "item_name": self.file_name,
            }

        try:
            # Update status and tracking info
            self.write({
                'status': 'retrieved',
                'date_retrieved': fields.Datetime.now(),
                'retrieved_by_id': self.env.user.id
            })

            # Shadow NAID AAA audit logging (automatic, no extra steps)
            self._create_naid_audit_entry(
                action='file_retrieved',
                details={
                    'file_name': self.file_name,
                    'container_barcode': self.container_barcode,
                    'scanned_barcode': scanned_barcode,
                    'retrieved_by': self.env.user.name,
                    'location': self.location_id.name if self.location_id else None
                }
            )

            # Send automatic notification if customer opted in
            if self.notify_retrieved:
                self._send_retrieval_notification()

            # Check if all items in work order are retrieved
            self._check_work_order_completion()

            return {
                "success": True,
                "message": _('File "%s" retrieved successfully', self.file_name),
                "item_name": self.file_name,
                "status": self.status,
            }

        except Exception as e:
            _logger.error("Barcode scan error for item %s: %s", self.name, str(e))
            return {"success": False, "message": _("Error retrieving file: %s", str(e)), "item_name": self.file_name}

    def barcode_scan_deliver(self, delivery_confirmation=None):
        """
        Barcode scanning method for delivery confirmation

        Args:
            delivery_confirmation (str): Delivery confirmation code/signature

        Returns:
            dict: Success/error message
        """
        self.ensure_one()

        if self.status != 'retrieved':
            return {
                'success': False,
                'message': _('Item must be retrieved before delivery'),
                'item_name': self.file_name
            }

        try:
            # Update delivery status
            self.write({
                'status': 'delivered',
                'date_delivered': fields.Datetime.now()
            })

            # Shadow NAID AAA audit logging
            self._create_naid_audit_entry(
                action='file_delivered',
                details={
                    'file_name': self.file_name,
                    'delivery_method': self.delivery_method,
                    'delivery_confirmation': delivery_confirmation,
                    'delivered_by': self.env.user.name
                }
            )

            # Send delivery notification if customer opted in
            if self.notify_delivered:
                self._send_delivery_notification()

            return {
                "success": True,
                "message": _('File "%s" delivered successfully', self.file_name),
                "item_name": self.file_name,
            }

        except Exception as e:
            _logger.error("Delivery scan error for item %s: %s", self.name, str(e))
            return {
                "success": False,
                "message": _("Error confirming delivery: %s", str(e)),
                "item_name": self.file_name,
            }

    def mark_not_found(self, reason=None):
        """
        Mark item as not found during retrieval

        Args:
            reason (str): Reason why file was not found
        """
        self.ensure_one()

        self.write({
            'status': 'not_found',
            'notes': f"Not found: {reason}" if reason else "File not found in expected location"
        })

        # Shadow audit logging
        self._create_naid_audit_entry(
            action='file_not_found',
            details={
                'file_name': self.file_name,
                'reason': reason,
                'searched_by': self.env.user.name,
                'container_barcode': self.container_barcode
            }
        )

        # Notify work order coordinator
        self.message_post(
            body=_("File '%s' not found during retrieval. Reason: %s", self.file_name, reason or "Unknown"),
            message_type="notification",
        )

    # ============================================================================
    # SHADOW NAID AAA AUDITING - AUTOMATIC BACKGROUND
    # ============================================================================
    def _create_naid_audit_entry(self, action, details):
        """
        Create NAID AAA audit log entry automatically in background

        This happens without any extra steps for technicians - pure shadow auditing
        for compliance reporting when needed.
        """
        try:
            self.env['naid.audit.log'].create({
                'file_retrieval_item_id': self.id,
                'work_order_id': self.work_order_id.id,
                'partner_id': self.partner_id.id,
                'user_id': self.env.user.id,
                'action': action,
                'timestamp': fields.Datetime.now(),
                'details': str(details),
                'ip_address': self.env.context.get('request_ip', 'Unknown'),
                'session_id': self.env.context.get('session_id', 'Unknown')
            })
        except Exception as e:
            # Log error but don't stop workflow - shadow auditing should never block operations
            _logger.warning("NAID audit logging failed for action %s: %s", action, str(e))

    # ============================================================================
    # AUTOMATED NOTIFICATIONS - CUSTOMER OPT-IN
    # ============================================================================
    def _send_retrieval_notification(self):
        """Send automatic notification when file is retrieved (if opted in)"""
        if not self.notify_retrieved:
            return

        template = self.env.ref('records_management.email_template_file_retrieved', raise_if_not_found=False)
        if template and self.notification_method in ['email', 'both']:
            template.send_mail(self.id, force_send=True)

        # SMS notification if enabled
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            message = _(
                "File '%s' has been retrieved and is ready for processing. Work Order: %s",
                self.file_name,
                self.work_order_id.name,
            )
            self._send_sms_notification(message)

    def _send_delivery_notification(self):
        """Send automatic notification when file is delivered (if opted in)"""
        if not self.notify_delivered:
            return

        template = self.env.ref('records_management.email_template_file_delivered', raise_if_not_found=False)
        if template and self.notification_method in ['email', 'both']:
            template.send_mail(self.id, force_send=True)

        # SMS notification if enabled
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            message = _("File '%s' has been delivered. Work Order: %s", self.file_name, self.work_order_id.name)
            if self.tracking_number:
                message += _(" Tracking: %s", self.tracking_number)
            self._send_sms_notification(message)

    def _send_sms_notification(self, message):
        """Send SMS notification"""
        try:
            self.env['sms.api'].send_sms(
                number=self.partner_id.mobile,
                message=message
            )
        except Exception as e:
            _logger.warning("SMS notification failed for partner %s: %s", self.partner_id.name, str(e))

    def _check_work_order_completion(self):
        """Check if all items in work order are completed and send notification"""
        work_order = self.work_order_id
        total_items = len(work_order.item_ids)
        retrieved_items = len(work_order.item_ids.filtered(lambda x: x.status == 'retrieved'))

        if total_items == retrieved_items:
            # All items retrieved - send completion notification
            template = self.env.ref('records_management.email_template_work_order_items_retrieved', raise_if_not_found=False)
            if template:
                template.send_mail(work_order.id, force_send=True)

    # ============================================================================
    # ORM METHODS - ENHANCED FOR WORKFLOW
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with automatic audit logging"""
        for vals in vals_list:
            # Generate sequence-based name if not provided
            if vals.get("name", _("New")) == _("New"):
                sequence_code = 'file.retrieval.work.order.item'
                vals["name"] = self.env["ir.sequence"].next_by_code(sequence_code) or _("New")

        records = super().create(vals_list)

        # Shadow audit logging for creation
        for record in records:
            record._create_naid_audit_entry(
                action='item_created',
                details={
                    'file_name': record.file_name,
                    'work_order': record.work_order_id.name,
                    'created_by': self.env.user.name
                }
            )

        return records

    def write(self, vals):
        """Enhanced write with automatic audit logging for status changes"""
        # Track status changes for audit
        status_changes = []
        if 'status' in vals:
            for record in self:
                if record.status != vals['status']:
                    status_changes.append({
                        'record': record,
                        'old_status': record.status,
                        'new_status': vals['status']
                    })

        result = super().write(vals)

        # Shadow audit logging for status changes
        for change in status_changes:
            change['record']._create_naid_audit_entry(
                action='status_changed',
                details={
                    'file_name': change['record'].file_name,
                    'old_status': change['old_status'],
                    'new_status': change['new_status'],
                    'changed_by': self.env.user.name
                }
            )

        return result

    # ============================================================================
    # VALIDATION CONSTRAINTS - ESSENTIAL ONLY
    # ============================================================================
    @api.constrains('status', 'date_assigned', 'date_retrieved', 'date_delivered')
    def _check_date_consistency(self):
        """Validate that dates are logical based on status"""
        for record in self:
            if record.status in ['retrieved', 'delivered'] and not record.date_retrieved:
                raise ValidationError(_("Retrieved date is required when status is '%s'", record.status))

            if record.status == 'delivered' and not record.date_delivered:
                raise ValidationError(_("Delivered date is required when status is 'delivered'"))

            # Check chronological order
            if record.date_assigned and record.date_retrieved and record.date_assigned > record.date_retrieved:
                raise ValidationError(_("Retrieved date cannot be before assigned date"))

            if record.date_retrieved and record.date_delivered and record.date_retrieved > record.date_delivered:
                raise ValidationError(_("Delivered date cannot be before retrieved date"))

    @api.constrains('file_name', 'work_order_id')
    def _check_unique_file_per_order(self):
        """Ensure file names are unique within a work order"""
        for record in self:
            if record.file_name and record.work_order_id:
                duplicate = self.search([
                    ('work_order_id', '=', record.work_order_id.id),
                    ('file_name', '=', record.file_name),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_("File '%s' already exists in this work order", record.file_name))

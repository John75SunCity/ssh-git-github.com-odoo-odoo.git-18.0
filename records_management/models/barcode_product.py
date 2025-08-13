# -*- coding: utf-8 -*-
"""
Barcode Product Management Module

Intelligent barcode generation and validation system for Records Management.
Handles automatic product categorization, barcode format validation, and
integration with container specifications.

Features:
- Intelligent barcode classification (5,6,7,10,14,15 digit patterns)
- Container type integration with business specifications
- Automatic product categorization based on barcode length
- NAID compliance tracking and audit trails
- Real-time validation and error prevention

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BarcodeProduct(models.Model):
    """
    Barcode Product Management with intelligent classification system.

    This model handles the complete lifecycle of barcode-enabled products
    with automatic categorization based on barcode length patterns used
    in the Records Management business operations.
    """

    _name = "barcode.product"
    _description = "Barcode Product Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Product Name",
        required=True,
        tracking=True,
        index=True,
        help="Descriptive name for the barcode product",
    )
    code = fields.Char(
        string="Product Code",
        index=True,
        tracking=True,
        help="Internal reference code for the product",
    )
    barcode = fields.Char(
        string="Barcode",
        required=True,
        index=True,
        tracking=True,
        help="Actual barcode value - automatically classified by length",
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the product and its use",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for display purposes",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this product is active in the system",
    )

    # ============================================================================
    # BUSINESS CLASSIFICATION FIELDS
    # ============================================================================
    product_category = fields.Selection(
        [
            ("location", "Location Assignment"),
            ("container_box", "Container Box"),
            ("permanent_folder", "Permanent File Folder"),
            ("temp_folder", "Temporary File Folder"),
            ("shred_item", "Shred Bin Item"),
            ("equipment", "Equipment/Asset"),
            ("other", "Other"),
        ],
        string="Product Category",
        compute="_compute_product_category",
        store=True,
        help="Automatically determined based on barcode length",
    )

    barcode_length = fields.Integer(
        string="Barcode Length",
        compute="_compute_barcode_length",
        store=True,
        help="Length of the barcode for classification",
    )

    container_type = fields.Selection(
        [
            ("type_01", "TYPE 01 - Standard Box (1.2 CF)"),
            ("type_02", "TYPE 02 - Legal/Banker Box (2.4 CF)"),
            ("type_03", "TYPE 03 - Map Box (0.875 CF)"),
            ("type_04", "TYPE 04 - Odd Size/Temp Box (5.0 CF)"),
            ("type_06", "TYPE 06 - Pathology Box (0.042 CF)"),
        ],
        string="Container Type",
        help="Container type if this is a container product",
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # BUSINESS INTEGRATION FIELDS
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Assigned Location",
        help="Location assigned to this barcode (for location barcodes)",
    )
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Container related to this barcode (for container barcodes)",
    )

    # Usage tracking
    scan_count = fields.Integer(
        string="Scan Count",
        default=0,
        help="Number of times this barcode has been scanned",
    )
    last_scanned = fields.Datetime(
        string="Last Scanned", help="Date and time of last scan"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        domain="[('res_model', '=', 'barcode.product')]",
        string="Activities",
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        domain="[('res_model', '=', 'barcode.product')]",
        string="Followers",
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        domain="[('res_model', '=', 'barcode.product')]",
        string="Messages",
    )
    storage_box_id = fields.Many2one(
        "barcode.storage.box", string="Storage Box"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("barcode")
    def _compute_barcode_length(self):
        """Compute barcode length for classification"""
        for record in self:
            record.barcode_length = (
                len(record.barcode.strip()) if record.barcode else 0
            )

    @api.depends("barcode_length")
    def _compute_product_category(self):
        """
        Intelligent barcode classification based on business rules.

        Classification Rules:
        - 5 or 15 digits: Location barcodes
        - 6 digits: Container boxes (file storage)
        - 7 digits: File folders (permanent)
        - 10 digits: Shred bin items
        - 14 digits: Temporary file folders (portal-created)
        """
        for record in self:
            length = record.barcode_length

            if length in [5, 15]:
                record.product_category = "location"
            elif length == 6:
                record.product_category = "container_box"
            elif length == 7:
                record.product_category = "permanent_folder"
            elif length == 10:
                record.product_category = "shred_item"
            elif length == 14:
                record.product_category = "temp_folder"
            else:
                record.product_category = "other"

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_process_barcode(self):
        """
        Process barcode according to business rules and create appropriate records.

        This method implements the intelligent barcode classification system
        that automatically creates the correct type of record based on barcode length.
        """
        self.ensure_one()

        if not self.barcode:
            raise UserError(_("Please enter a barcode before processing"))

        # Update scan tracking
        self.write(
            {
                "scan_count": self.scan_count + 1,
                "last_scanned": fields.Datetime.now(),
            }
        )

        # Process based on category
        if self.product_category == "location":
            return self._process_location_barcode()
        elif self.product_category == "container_box":
            return self._process_container_barcode()
        elif self.product_category == "permanent_folder":
            return self._process_permanent_folder_barcode()
        elif self.product_category == "temp_folder":
            return self._process_temp_folder_barcode()
        elif self.product_category == "shred_item":
            return self._process_shred_item_barcode()
        else:
            raise UserError(
                _(
                    "Barcode category '%s' is not supported for automatic processing",
                    self.product_category,
                )
            )

    def action_view_related_records(self):
        """View records related to this barcode"""
        self.ensure_one()

        if self.product_category == "container_box" and self.container_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Related Container"),
                "res_model": "records.container",
                "res_id": self.container_id.id,
                "view_mode": "form",
                "target": "current",
            }
        elif self.product_category == "location" and self.location_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Related Location"),
                "res_model": "records.location",
                "res_id": self.location_id.id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            return self._get_related_records_action()

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _process_location_barcode(self):
        """Process location barcode (5 or 15 digits)"""
        location = self.env["records.location"].search(
            [("barcode", "=", self.barcode)], limit=1
        )

        if not location:
            # Create new location
            location = self.env["records.location"].create(
                {
                    "name": _("Location %s", self.barcode),
                    "barcode": self.barcode,
                    "location_type": "warehouse",
                }
            )

        self.location_id = location.id
        self.message_post(
            body=_("Location barcode processed: %s", location.name)
        )

        return self._return_location_action(location)

    def _process_container_barcode(self):
        """Process container barcode (6 digits)"""
        container = self.env["records.container"].search(
            [("barcode", "=", self.barcode)], limit=1
        )

        if not container:
            # Create new container with default specifications
            container = self.env["records.container"].create(
                {
                    "name": self.barcode,
                    "barcode": self.barcode,
                    "container_type": "type_01",  # Default to most common type
                    "state": "draft",
                }
            )

        self.container_id = container.id
        self.message_post(
            body=_("Container barcode processed: %s", container.name)
        )

        return self._return_container_action(container)

    def _process_permanent_folder_barcode(self):
        """Process permanent folder barcode (7 digits)"""
        # Create document folder record
        folder = self.env["records.document.folder"].create(
            {
                "name": _("Folder %s", self.barcode),
                "barcode": self.barcode,
                "folder_type": "permanent",
                "state": "active",
            }
        )

        self.message_post(body=_("Permanent folder created: %s", folder.name))

        return {
            "type": "ir.actions.act_window",
            "name": _("Document Folder"),
            "res_model": "records.document.folder",
            "res_id": folder.id,
            "view_mode": "form",
            "target": "current",
        }

    def _process_temp_folder_barcode(self):
        """Process temporary folder barcode (14 digits)"""
        # Create temporary document folder
        folder = self.env["records.document.folder"].create(
            {
                "name": _("Temp Folder %s", self.barcode),
                "barcode": self.barcode,
                "folder_type": "temporary",
                "state": "active",
                "auto_expire_date": fields.Date.add(
                    fields.Date.today(), days=90
                ),
            }
        )

        self.message_post(
            body=_(
                "Temporary folder created: %s (expires in 90 days)",
                folder.name,
            )
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Temporary Document Folder"),
            "res_model": "records.document.folder",
            "res_id": folder.id,
            "view_mode": "form",
            "target": "current",
        }

    def _process_shred_item_barcode(self):
        """Process shred bin item barcode (10 digits)"""
        # Create shred bin item
        shred_item = self.env["shred.bin.item"].create(
            {
                "name": _("Shred Item %s", self.barcode),
                "barcode": self.barcode,
                "state": "pending",
                "estimated_weight": 1.0,  # Default weight
            }
        )

        self.message_post(
            body=_("Shred bin item created: %s", shred_item.name)
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shred Bin Item"),
            "res_model": "shred.bin.item",
            "res_id": shred_item.id,
            "view_mode": "form",
            "target": "current",
        }

    def _get_related_records_action(self):
        """Get action for viewing all related records"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Barcode Usage History"),
            "res_model": "barcode.scan.history",
            "domain": [("barcode", "=", self.barcode)],
            "view_mode": "tree,form",
            "target": "current",
        }

    def _return_location_action(self, location):
        """Return action to view location"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Location"),
            "res_model": "records.location",
            "res_id": location.id,
            "view_mode": "form",
            "target": "current",
        }

    def _return_container_action(self, container):
        """Return action to view container"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Container"),
            "res_model": "records.container",
            "res_id": container.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("barcode")
    def _check_barcode_format(self):
        """Validate barcode format and length"""
        for record in self:
            if not record.barcode:
                continue

            barcode = record.barcode.strip()
            length = len(barcode)

            # Check for valid barcode lengths
            valid_lengths = [5, 6, 7, 10, 14, 15]
            if length not in valid_lengths:
                raise ValidationError(
                    _(
                        "Invalid barcode length: %d. Valid lengths are: %s",
                        length,
                        ", ".join(map(str, valid_lengths)),
                    )
                )

            # Check for numeric-only barcodes
            if not barcode.isdigit():
                raise ValidationError(
                    _("Barcode must contain only numeric digits: %s", barcode)
                )

    @api.constrains("barcode")
    def _check_barcode_uniqueness(self):
        """Ensure barcode uniqueness"""
        for record in self:
            if record.barcode:
                existing = self.search(
                    [("barcode", "=", record.barcode), ("id", "!=", record.id)]
                )
                if existing:
                    raise ValidationError(
                        _(
                            "Barcode %s already exists in product: %s",
                            record.barcode,
                            existing.name,
                        )
                    )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle barcode processing"""
        records = super().create(vals_list)

        # Log creation for audit trail
        for record in records:
            record.message_post(
                body=_(
                    "Barcode product created with category: %s",
                    record.product_category,
                )
            )

        return records

    def write(self, vals):
        """Override write to track changes"""
        result = super().write(vals)

        # Log important changes
        if "barcode" in vals:
            for record in self:
                record.message_post(
                    body=_(
                        "Barcode updated to: %s (Category: %s)",
                        record.barcode,
                        record.product_category,
                    )
                )

        return result

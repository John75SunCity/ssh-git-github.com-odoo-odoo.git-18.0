# -*- coding: utf-8 -*-
"""
Barcode Product Management Module

Manages barcode "products" which are templates for generating physical barcodes.
This model includes intelligent classification based on barcode length and
integrates with standard business container specifications.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class BarcodeProduct(models.Model):
    """
    Barcode Product Management

    Serves as a template for different types of barcodes used within the
    Records Management system. It defines properties, behavior, and validation
    for barcodes used for locations, containers, folders, and more.
    """
    _name = 'barcode.product'
    _description = 'Barcode Product Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # BARCODE DETAILS & CLASSIFICATION
    # ============================================================================
    barcode = fields.Char(
        string='Barcode',
        required=True,
        copy=False,
        help="The unique barcode value."
    )
    barcode_type = fields.Selection([
        ('manual', 'Manual'),
        ('generated', 'Generated'),
        ('auto', 'Auto-Detected')
    ], string='Barcode Type', default='manual', required=True)

    product_category = fields.Selection([
        ('location', 'Location'),
        ('container_box', 'Container Box'),
        ('file_folder', 'File Folder'),
        ('shred_bin', 'Shred Bin'),
        ('temp_folder', 'Temp Folder'),
        ('other', 'Other')
    ], string='Product Category', compute='_compute_product_category', store=True)

    barcode_pattern = fields.Char(
        string='Barcode Pattern',
        compute='_compute_barcode_pattern',
        store=True,
        help="Automatically detected pattern of the barcode (e.g., numeric, length)."
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS (Based on Business Rules)
    # ============================================================================
    container_type = fields.Selection([
        ('type_01', 'Standard Box (1.2 CF)'),
        ('type_02', 'Legal/Banker Box (2.4 CF)'),
        ('type_03', 'Map Box (0.875 CF)'),
        ('type_04', 'Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'Pathology Box (0.042 CF)')
    ], string='Container Type', help="Select if this barcode represents a container.")

    volume_cf = fields.Float(
        string='Volume (Cubic Feet)',
        compute='_compute_specifications',
        store=True,
        digits=(12, 3)
    )
    weight_lbs = fields.Float(
        string='Average Weight (lbs)',
        compute='_compute_specifications',
        store=True,
        digits='Stock Weight'
    )
    dimensions = fields.Char(
        string='Dimensions',
        compute='_compute_specifications',
        store=True
    )

    # ============================================================================
    # VALIDATION & USAGE TRACKING
    # ============================================================================
    is_valid = fields.Boolean(
        string='Is Valid',
        compute='_compute_is_valid',
        store=True,
        help="Indicates if the barcode passes all business validation rules."
    )
    validation_message = fields.Text(
        string='Validation Message',
        compute='_compute_is_valid',
        store=True
    )
    usage_count = fields.Integer(string='Usage Count', readonly=True, default=0)
    last_used_date = fields.Datetime(string='Last Used Date', readonly=True)

    # ============================================================================
    # RELATED RECORDS
    # ============================================================================
    location_id = fields.Many2one('records.location', string='Related Location', readonly=True)
    container_id = fields.Many2one('records.container', string='Related Container', readonly=True)
    created_records_count = fields.Integer(
        string='Created Records',
        compute='_compute_created_records_count',
        store=True
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('barcode')
    def _compute_barcode_pattern(self):
        """Analyze barcode pattern for classification and display."""
        for record in self:
            if record.barcode:
                barcode_clean = record.barcode.strip()
                length = len(barcode_clean)
                pattern_parts = []

                if barcode_clean.isdigit():
                    pattern_parts.append("Numeric")
                elif barcode_clean.isalpha():
                    pattern_parts.append("Alpha")
                else:
                    pattern_parts.append("Mixed")

                pattern_parts.append(_("Length: %s") % length)
                record.barcode_pattern = " - ".join(pattern_parts)
            else:
                record.barcode_pattern = ""

    @api.depends('barcode')
    def _compute_product_category(self):
        """Auto-classify product based on barcode length according to business rules."""
        for record in self:
            if not record.barcode:
                record.product_category = "other"
                continue

            length = len(record.barcode.strip())
            if length in [5, 15]:
                record.product_category = "location"
            elif length == 6:
                record.product_category = "container_box"
            elif length == 7:
                record.product_category = "file_folder"
            elif length == 10:
                record.product_category = "shred_bin"
            elif length == 14:
                record.product_category = "temp_folder"
            else:
                record.product_category = "other"

    @api.depends('product_category', 'container_type')
    def _compute_specifications(self):
        """Compute product specifications based on the selected container type."""
        CONTAINER_SPECS = {
            'type_01': {'volume': 1.2, 'weight': 35, 'dims': '12" x 15" x 10"'},
            'type_02': {'volume': 2.4, 'weight': 65, 'dims': '24" x 15" x 10"'},
            'type_03': {'volume': 0.875, 'weight': 35, 'dims': '42" x 6" x 6"'},
            'type_04': {'volume': 5.0, 'weight': 75, 'dims': 'Variable'},
            'type_06': {'volume': 0.042, 'weight': 40, 'dims': '12" x 6" x 10"'},
        }
        for record in self:
            if record.product_category == "container_box" and record.container_type:
                specs = CONTAINER_SPECS.get(record.container_type, {})
                record.volume_cf = specs.get('volume', 0.0)
                record.weight_lbs = specs.get('weight', 0.0)
                record.dimensions = specs.get('dims', '')
            else:
                record.volume_cf = 0.0
                record.weight_lbs = 0.0
                record.dimensions = ''

    @api.depends('barcode', 'product_category', 'container_type')
    def _compute_is_valid(self):
        """Validate barcode according to a comprehensive set of business rules."""
        for record in self:
            messages = []
            if not record.barcode:
                record.is_valid = False
                record.validation_message = _("Barcode is required.")
                continue

            barcode = record.barcode.strip()
            length = len(barcode)

            valid_lengths = [5, 6, 7, 10, 14, 15]
            if length not in valid_lengths:
                messages.append(_("Invalid length: %s (expected one of: %s)") % (length, ', '.join(map(str, valid_lengths))))

            if not re.match(r'^[A-Za-z0-9-]+$', barcode):
                messages.append(_("Invalid characters found. Only letters, numbers, and hyphens are allowed."))

            if record.product_category == "container_box" and not record.container_type:
                messages.append(_("A container type is required for container box barcodes."))

            existing = self.search([('barcode', '=', barcode), ('id', '!=', record.id or 0)])
            if existing:
                messages.append(_("This barcode already exists for product: %s") % existing.name)

            record.is_valid = not messages
            record.validation_message = '; '.join(messages) if messages else _("Barcode is valid.")

    @api.depends('location_id', 'container_id')
    def _compute_created_records_count(self):
        """Count how many primary records have been created from this barcode."""
        for record in self:
            count = 0
            if record.container_id:
                count += 1
            if record.location_id:
                count += 1
            record.created_records_count = count

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Auto-populate fields when barcode changes."""
        if self.barcode:
            self.barcode = self.barcode.strip().upper()
            if self.product_category == "container_box" and not self.container_type:
                self.container_type = "type_01" # Default to most common type

    @api.onchange('product_category')
    def _onchange_product_category(self):
        """Clear incompatible fields when category changes."""
        if self.product_category != "container_box":
            self.container_type = False
            self.container_id = False
        if self.product_category != "location":
            self.location_id = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate_barcode(self):
        """Manually trigger barcode validation and show a notification."""
        self.ensure_one()
        self.is_valid = self._compute_is_valid() # Recompute
        if self.is_valid:
            message = _("Barcode validation successful.")
            message_type = "success"
        else:
            message = _("Barcode validation failed: %s") % self.validation_message
            message_type = "warning"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Validation Result"),
                "message": message,
                "type": message_type,
                "sticky": False,
            }
        }

    def action_create_related_record(self):
        """Create a related record (e.g., container, location) based on the product category."""
        self.ensure_one()
        if not self.is_valid:
            raise UserError(_("Cannot create a record from an invalid barcode. Please resolve validation issues first."))

        if self.product_category == "container_box":
            return self._create_container_record()
        elif self.product_category == "location":
            return self._create_location_record()
        else:
            raise UserError(_("Record creation is not supported for this category: %s") % self.product_category)

    def action_activate(self):
        """Activate the barcode product."""
        self.write({"state": "active"})
        for record in self:
            record.message_post(body=_("Barcode product activated."))

    def action_archive(self):
        """Archive the barcode product."""
        self.write({"state": "archived", "active": False})
        for record in self:
            record.message_post(body=_("Barcode product archived."))

    # ============================================================================
    # UTILITY & PRIVATE METHODS
    # ============================================================================
    def _create_container_record(self):
        """Private method to create a records.container from the barcode."""
        self.ensure_one()
        if not self.container_type:
            raise UserError(_("A container type must be specified before creating a container record."))

        container_vals = {
            "name": _("Container %s") % self.barcode,
            "barcode": self.barcode,
            "container_type": self.container_type,
            "created_from_barcode_id": self.id,
        }
        container = self.env["records.container"].create(container_vals)
        self.container_id = container.id
        self._increment_usage()

        return {
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "res_id": container.id,
            "view_mode": "form",
            "target": "current",
            "name": _("Newly Created Container"),
        }

    def _create_location_record(self):
        """Private method to create a records.location from the barcode."""
        self.ensure_one()
        location_vals = {
            "name": _("Location %s") % self.barcode,
            "location_code": self.barcode,
            "created_from_barcode_id": self.id,
        }
        location = self.env["records.location"].create(location_vals)
        self.location_id = location.id
        self._increment_usage()

        return {
            "type": "ir.actions.act_window",
            "res_model": "records.location",
            "res_id": location.id,
            "view_mode": "form",
            "target": "current",
            "name": _("Newly Created Location"),
        }

    def _increment_usage(self):
        """Increment usage counter and log the event."""
        self.ensure_one()
        self.write({
            "usage_count": self.usage_count + 1,
            "last_used_date": fields.Datetime.now(),
            "state": "used"
        })
    self.message_post(body=_("Barcode used (Total uses: %s)") % self.usage_count)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('barcode')
    def _check_barcode_uniqueness(self):
        """Ensure barcode is unique across all products."""
        for record in self:
            if record.barcode:
                domain = [('barcode', '=', record.barcode), ('id', '!=', record.id)]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("Barcode '%s' must be unique.") % record.barcode)

    @api.constrains('barcode', 'product_category')
    def _check_barcode_category_consistency(self):
        """Validate that the barcode length matches the expected category based on business rules."""
        LENGTH_CATEGORY_MAP = {
            5: "location", 6: "container_box", 7: "file_folder",
            10: "shred_bin", 14: "temp_folder", 15: "location"
        }
        for record in self:
            if record.barcode and record.product_category:
                length = len(record.barcode.strip())
                expected_category = LENGTH_CATEGORY_MAP.get(length)
                if expected_category and record.product_category != expected_category:
                    raise ValidationError(
                        _("Barcode length %s suggests category '%s', but category '%s' is selected. Please correct the category or barcode.")
                        % (length, expected_category, record.product_category)
                    )


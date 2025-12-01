# -*- coding: utf-8 -*-
# pylint: disable=all
"""
Barcode Product Management Module

Manages barcode "products" which are templates for generating physical barcodes.
This model includes intelligent classification based on barcode length and
integrates with standard business container specifications.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

import re
from collections import Counter  # Added for efficient counting
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

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
        string='Product Manager',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # CORE PRODUCT & PHYSICAL SPECIFICATION FIELDS (Referenced in Views)
    # ============================================================================
    box_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
        ('xl', 'Extra Large')
    ], string='Box Size', help='Physical classification used for pricing and volume analytics.')
    capacity = fields.Float(string='Capacity (cu.ft)', help='Storage capacity in cubic feet (used in analytics).')
    weight_limit = fields.Float(string='Weight Limit (lbs)', help='Maximum recommended weight in pounds.')
    material_type = fields.Char(string='Material Type', help='Primary material composition (e.g., Corrugated).')
    color = fields.Char(string='Color', help='Color or identifying visual attribute.')

    # ============================================================================
    # BARCODE STRUCTURE EXTENSIONS
    # ============================================================================
    barcode_length = fields.Integer(string='Barcode Length', compute='_compute_barcode_length', store=True)
    barcode_prefix = fields.Char(string='Barcode Prefix')
    barcode_suffix = fields.Char(string='Barcode Suffix')
    check_digit_required = fields.Boolean(string='Check Digit Required', default=False)
    auto_generate = fields.Boolean(string='Auto Generate', default=False, help='Automatically generate next barcode on related operations.')

    # ============================================================================
    # PRICING & RATE CONFIGURATION (Monetary fields reference company currency)
    # ============================================================================
    currency_id = fields.Many2one(comodel_name='res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    storage_rate = fields.Monetary(string='Storage Rate', currency_field='currency_id', help='Monthly storage rate applied to this product.')
    shred_rate = fields.Monetary(string='Shred Rate', currency_field='currency_id', help='Shredding service rate per unit / bin.')
    setup_fee = fields.Monetary(string='Setup Fee', currency_field='currency_id')
    rush_service_rate = fields.Monetary(string='Rush Service Rate', currency_field='currency_id')
    volume_discount_threshold = fields.Integer(string='Volume Discount Threshold')
    volume_discount_rate = fields.Float(string='Volume Discount Rate (%)', help='Percentage discount applied after threshold is reached.')

    # ============================================================================
    # ANALYTICS & PERFORMANCE METRICS
    # ============================================================================
    monthly_volume = fields.Integer(string='Monthly Volume', help='Units processed or generated per month.')
    monthly_revenue = fields.Monetary(string='Monthly Revenue', currency_field='currency_id', compute='_compute_monthly_revenue', store=True)
    average_storage_duration = fields.Float(string='Avg. Storage Duration (days)', help='Average number of days items remain stored.', digits=(12, 2))
    utilization_rate = fields.Float(string='Utilization Rate (%)', compute='_compute_utilization_rate', store=True, digits=(12, 2))
    profit_margin = fields.Float(string='Profit Margin (%)', compute='_compute_profit_margin', store=True, digits=(12, 2))

    # ============================================================================
    # CONTAINER CONFIGURATION (Referenced on storage_config page)
    # ============================================================================
    climate_controlled = fields.Boolean(string='Climate Controlled')
    fireproof_rating = fields.Char(string='Fireproof Rating')
    security_level = fields.Selection([
        ('standard', 'Standard'),
        ('high', 'High'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='standard')
    stackable = fields.Boolean(string='Stackable')
    max_stack_height = fields.Integer(string='Max Stack Height')
    suitable_document_type_ids = fields.Many2many(
        'records.document.type',
        'barcode_product_document_type_rel',
        'product_id',
        'doc_type_id',
        string='Suitable Document Types'
    )
    max_file_folders = fields.Integer(string='Max File Folders')
    recommended_retention_years = fields.Integer(string='Recommended Retention (Years)')
    access_frequency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Access Frequency', default='medium')

    # ============================================================================
    # SHRED BIN CONFIGURATION (Referenced on shred_config page)
    # ============================================================================
    shred_security_level = fields.Selection([
        ('p1', 'P-1 (Basic)'),
        ('p3', 'P-3 (Confidential)'),
        ('p5', 'P-5 (High Security)'),
        ('p7', 'P-7 (Top Secret)')
    ], string='Shred Security Level')
    naid_compliant = fields.Boolean(string='NAID Compliant')
    witness_destruction = fields.Boolean(string='Witness Destruction')
    certificate_provided = fields.Boolean(string='Certificate Provided')
    pickup_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('on_demand', 'On Demand')
    ], string='Pickup Frequency')
    bin_volume = fields.Float(string='Bin Volume (cu.ft)', digits=(12, 2))
    lockable = fields.Boolean(string='Lockable')
    mobile = fields.Boolean(string='Mobile / Wheeled')
    indoor_outdoor = fields.Selection([
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('both', 'Indoor/Outdoor')
    ], string='Indoor/Outdoor')
    weight_capacity = fields.Float(string='Weight Capacity (lbs)', digits=(12, 2))

    # ============================================================================
    # BARCODE GENERATION CONFIGURATION
    # ============================================================================
    next_sequence_number = fields.Integer(string='Next Sequence Number', default=1)
    last_generated_barcode = fields.Char(string='Last Generated Barcode', readonly=True)
    total_generated = fields.Integer(string='Total Generated', readonly=True)
    generation_batch_size = fields.Integer(string='Batch Size', default=50)
    validate_format = fields.Boolean(string='Validate Format', default=True)
    validate_uniqueness = fields.Boolean(string='Validate Uniqueness', default=True)
    validate_check_digit = fields.Boolean(string='Validate Check Digit', default=False)
    allowed_characters = fields.Char(string='Allowed Characters', help='Restrict allowed characters (regex char class). Empty for any.')

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
        string="Average Weight (lbs)", compute="_compute_specifications", store=True, digits=(12, 3)
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
    location_id = fields.Many2one(comodel_name='stock.location', string='Related Location', readonly=True)
    container_id = fields.Many2one(comodel_name='records.container', string='Related Container', readonly=True)
    created_records_count = fields.Integer(
        string='Created Records',
        compute='_compute_created_records_count',
        store=True
    )
    # Customer location relationship (referenced in views)
    customer_location_id = fields.Many2one(
        'stock.location',
        string='Customer Location',
        help='Location context used when generating or assigning barcodes to physical assets.'
    )

    # Batch identifier surfaced in views; reflects the most recent related generation history batch
    batch_id = fields.Char(
        string='Latest Batch ID',
        compute='_compute_batch_id',
        store=True,
        help='Automatically populated with the most recent batch identifier from generation history.'
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities", domain=lambda self: [("res_model", "=", self._name)]
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", domain=lambda self: [("res_model", "=", self._name)]
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", domain=lambda self: [("model", "=", self._name)]
    )

    # ============================================================================
    # RELATIONSHIPS (to be reflected back in views)
    # ============================================================================
    # Primary (singular) storage box assignment referenced in some views. This complements
    # the existing storage_box_ids One2many (all linked boxes). Keeping both allows a
    # designated "primary" box while still listing all related boxes.
    storage_box_id = fields.Many2one(
        'records.storage.box',
        string='Primary Storage Box',
        help='Designated primary storage box linked to this barcode product.',
        tracking=True,
        ondelete='set null',
        index=True,
    )
    storage_box_ids = fields.One2many('records.storage.box', 'product_id', string='Storage Boxes', help='Storage boxes linked directly to this barcode product.')
    shred_bin_ids = fields.One2many('shred.bin', 'product_id', string='Shred Bins', help='Shred bins linked directly to this barcode product.')
    pricing_tier_ids = fields.One2many('barcode.pricing.tier', 'product_id', string='Pricing Tiers')
    seasonal_pricing_ids = fields.One2many('barcode.seasonal.pricing', 'product_id', string='Seasonal Pricing Rules')
    generation_history_ids = fields.One2many('barcode.generation.history', 'product_id', string='Generation History')

    storage_box_count = fields.Integer(string='Storage Box Count', compute='_compute_counts', store=True)
    shred_bin_count = fields.Integer(string='Shred Bin Count', compute='_compute_counts', store=True)

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

                    pattern_parts.append(_("Length:"))
                    pattern_parts.append(str(length))
                record.barcode_pattern = " - ".join(pattern_parts)
            else:
                record.barcode_pattern = ""

    @api.depends('barcode')
    def _compute_barcode_length(self):
        """Compute and store barcode length as integer for analytics and grouping."""
        for record in self:
            record.barcode_length = len(record.barcode.strip()) if record.barcode else 0

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
        # Build a counter for barcodes in the current batch to check for duplicates efficiently
        barcode_counts = Counter(record.barcode for record in self if record.barcode)

        # Batch uniqueness check: Collect all barcodes and query existing ones once
        all_barcodes = {record.barcode for record in self if record.barcode}
        existing_barcodes = set()
        if all_barcodes:
            existing_records = self.search(
                [("barcode", "in", list(all_barcodes)), ("id", "not in", [r.id for r in self if r.id])]
            )
            existing_barcodes = {rec.barcode for rec in existing_records}

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
                messages.append(_("Invalid barcode length"))

            if not re.match(r'^[A-Za-z0-9-]+$', barcode):
                messages.append(_("Invalid characters found. Only letters, numbers, and hyphens are allowed."))

            if record.product_category == "container_box" and not record.container_type:
                messages.append(_("A container type is required for container box barcodes."))

            # Optimized uniqueness check: Use batched results for global duplicates
            if barcode_counts.get(barcode, 0) > 1:
                messages.append(_("This barcode already exists in the current batch."))
            elif barcode in existing_barcodes:
                messages.append(_("This barcode already exists for another product."))

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

    @api.depends('generation_history_ids', 'generation_history_ids.batch_id', 'generation_history_ids.generation_date')
    def _compute_batch_id(self):
        """Derive latest batch identifier from related generation history records.

        Selection logic:
        - Pick history record with the most recent generation_date.
        - Fall back to highest ID if dates missing.
        - Leave blank if no related history or no batch_id values.
        """
        for record in self:
            latest = False
            # Filter only histories that actually have a batch id value
            histories = record.generation_history_ids.filtered(lambda h: h.batch_id)
            if histories:
                # Prefer proper generation_date ordering; fallback to id
                histories_sorted = histories.sorted(lambda h: (h.generation_date or fields.Datetime.from_string('1970-01-01'), h.id), reverse=True)
                latest = histories_sorted[0]
            record.batch_id = latest.batch_id if latest else False

    @api.depends('storage_box_ids', 'shred_bin_ids')
    def _compute_counts(self):
        """Compute related object counters for stat buttons."""
        for record in self:
            record.storage_box_count = len(record.storage_box_ids)
            record.shred_bin_count = len(record.shred_bin_ids)

    @api.depends('storage_rate', 'shred_rate', 'monthly_volume')
    def _compute_monthly_revenue(self):
        """Estimate monthly revenue using storage + shred components.
        Placeholder: Adjust later to include negotiated rates and seasonal multipliers.
        """
        for record in self:
            base_storage = (record.storage_rate or 0.0)
            shred_component = (record.shred_rate or 0.0) * (record.monthly_volume or 0)
            record.monthly_revenue = base_storage + shred_component

    @api.depends('capacity', 'monthly_volume')
    def _compute_utilization_rate(self):
        for record in self:
            if record.capacity and record.capacity > 0:
                record.utilization_rate = min(100.0, (record.monthly_volume or 0) / record.capacity * 100.0)
            else:
                record.utilization_rate = 0.0

    @api.depends('monthly_revenue', 'storage_rate', 'shred_rate')
    def _compute_profit_margin(self):
        for record in self:
            # Simplistic placeholder: treat storage_rate + shred_rate as revenue baseline, assume 60% cost
            total_rate_baseline = (record.storage_rate or 0.0) + (record.shred_rate or 0.0)
            if total_rate_baseline > 0:
                assumed_cost = total_rate_baseline * 0.6
                margin = (total_rate_baseline - assumed_cost) / total_rate_baseline * 100.0
                record.profit_margin = margin
            else:
                record.profit_margin = 0.0


    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Auto-populate fields when barcode changes."""
        if self.barcode:
            self.barcode = self.barcode.strip()  # Strip leading/trailing whitespace from barcode
            if self.product_category == "container_box" and not self.container_type:
                self.container_type = "type_01"  # Default to most common type

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
        self._compute_is_valid()  # Recompute
        if self.is_valid:
            message = _("Barcode validation successful.")
            message_type = "success"
        else:
            message = _("Barcode validation failed")
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
            raise UserError(_("Record creation not supported for this category"))

    def action_activate(self):
        """Activate the barcode product."""
        self.ensure_one()  # Added as per Odoo standard
        self.write({"state": "active"})
        for record in self:
            record.message_post(body=_("Barcode product activated."))

    def action_archive(self):
        """Archive the barcode product."""
        self.ensure_one()  # Added as per Odoo standard
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
            "name": _("Container") + f" {self.barcode}",
            "barcode": self.barcode,
            "container_type_id": self._get_container_type_id(),
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
        """Private method to create a stock.location (records location) from the barcode."""
        self.ensure_one()
        location_vals = {
            "name": _("Location") + f" {self.barcode}",
            "location_code": self.barcode,
            "created_from_barcode_id": self.id,
        }
        location = self.env["stock.location"].create(location_vals)
        self.location_id = location.id
        self._increment_usage()

        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.location",
            "res_id": location.id,
            "view_mode": "form",
            "target": "current",
            "name": _("Newly Created Location"),
        }

    def _get_container_type_id(self):
        """Convert container_type selection to container type ID."""
        self.ensure_one()
        if not self.container_type:
            return False

        # Map selection values to container type names
        type_mapping = {
            "type_01": "Standard Box",
            "type_02": "Legal/Banker Box",
            "type_03": "Map Box",
            "type_04": "Odd Size/Temp Box",
            "type_06": "Pathology Box",
        }

        type_name = type_mapping.get(self.container_type)
        if type_name:
            container_type = self.env["records.container.type"].search([("name", "=", type_name)], limit=1)
            return container_type.id if container_type else False

        return False

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
                    raise ValidationError(_("Barcode must be unique."))

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
                        _("Barcode length suggests a different category. Please correct the category or barcode." )
                    )

    # ============================================================================
    # MISSING ACTION METHODS FOR VIEW COMPATIBILITY
    # ============================================================================
    def action_deactivate(self):
        """Deactivate the barcode product."""
        self.ensure_one()
        self.write({"active": False})
        self.message_post(body=_("Barcode product deactivated."))

    def action_update_pricing(self):
        """Update pricing for the barcode product."""
        self.ensure_one()
        # Placeholder for pricing update logic
        self.message_post(body=_("Pricing update initiated."))

    def action_generate_barcodes(self):
        """Generate barcodes for the product."""
        self.ensure_one()
        # Placeholder for barcode generation logic
        self.message_post(body=_("Barcode generation initiated."))

    def action_view_storage_boxes(self):
        """View related storage boxes."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Storage Boxes",
            "res_model": "records.storage.box",
            "view_mode": "list,form",
            "domain": [("product_id", "=", self.id)],
        }

    def action_view_shred_bins(self):
        """View related shred bins."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Shred Bins",
            "res_model": "shred.bin",
            "view_mode": "list,form",
            "domain": [("product_id", "=", self.id)],
        }

    def action_view_revenue(self):
        """View revenue analytics."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Revenue Analytics",
            "res_model": "barcode.product",
            "view_mode": "graph,pivot",
            "res_id": self.id,
        }

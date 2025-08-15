# -*- coding: utf-8 -*-
"""
Barcode Product Management Module

Intelligent barcode generation and validation system with automatic product
classification based on barcode patterns for Records Management operations.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import re
import logging

_logger = logging.getLogger(__name__)


class BarcodeProduct(models.Model):
    """Intelligent barcode generation and validation system"""

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
        index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Whether this product is active in the system"
    )

    # ============================================================================
    # BARCODE FIELDS
    # ============================================================================
    barcode = fields.Char(
        string="Barcode",
        required=True,
        index=True,
        tracking=True,
        help="Generated or manually entered barcode"
    )
    barcode_type = fields.Selection([
        ("auto", "Auto Generated"),
        ("manual", "Manual Entry"),
        ("imported", "Imported"),
    ], string="Barcode Type", default="auto", tracking=True)
    
    barcode_pattern = fields.Char(
        string="Barcode Pattern",
        compute="_compute_barcode_pattern",
        store=True,
        help="Pattern analysis of the barcode structure"
    )

    # ============================================================================
    # SEQUENCE AND ORDERING
    # ============================================================================
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for display purposes"
    )

    # ============================================================================
    # BUSINESS CLASSIFICATION FIELDS
    # ============================================================================
    product_category = fields.Selection([
        ("location", "Location Assignment"),
        ("container_box", "Container Box"),
        ("permanent_folder", "Permanent File Folder"),
        ("temp_folder", "Temporary File Folder"),
        ("shred_item", "Shred Bin Item"),
        ("equipment", "Equipment/Asset"),
        ("other", "Other"),
    ], string="Product Category",
       compute="_compute_product_category",
       store=True,
       help="Automatically determined based on barcode length")

    container_type = fields.Selection([
        ("type_01", "Standard Box (1.2 CF)"),
        ("type_02", "Legal/Banker Box (2.4 CF)"),
        ("type_03", "Map Box (0.875 CF)"),
        ("type_04", "Odd Size/Temp Box (5.0 CF)"),
        ("type_06", "Pathology Box (0.042 CF)"),
    ], string="Container Type", help="Type when product_category is container_box")

    # ============================================================================
    # PRODUCT SPECIFICATIONS
    # ============================================================================
    volume_cf = fields.Float(
        string="Volume (Cubic Feet)",
        digits=(8, 3),
        compute="_compute_specifications",
        store=True,
        help="Volume in cubic feet based on container type"
    )
    weight_lbs = fields.Float(
        string="Weight (lbs)",
        digits=(8, 1),
        compute="_compute_specifications",
        store=True,
        help="Standard weight in pounds"
    )
    dimensions = fields.Char(
        string="Dimensions",
        compute="_compute_specifications",
        store=True,
        help="Standard dimensions (LxWxH)"
    )

    # ============================================================================
    # LOCATION AND RELATIONSHIPS
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Assigned Location",
        help="Location where this product is assigned"
    )
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Container record if applicable"
    )

    storage_box_id = fields.Many2one(
        "barcode.storage.box",
        string="Storage Box",
        help="Associated storage box for this barcode product",
        ondelete="set null"
    )

    # ============================================================================
    # VALIDATION AND STATUS
    # ============================================================================
    is_valid = fields.Boolean(
        string="Valid Barcode",
        compute="_compute_is_valid",
        store=True,
        help="Whether the barcode passes validation rules"
    )
    validation_message = fields.Text(
        string="Validation Message",
        compute="_compute_is_valid",
        store=True,
        help="Details about barcode validation status"
    )

    # ============================================================================
    # USAGE TRACKING
    # ============================================================================
    usage_count = fields.Integer(
        string="Usage Count",
        default=0,
        help="Number of times this barcode has been used"
    )
    last_used_date = fields.Datetime(
        string="Last Used Date",
        help="When this barcode was last scanned/used"
    )
    created_records_count = fields.Integer(
        string="Created Records",
        compute="_compute_created_records_count",
        help="Number of records created from this barcode"
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('used', 'Used'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("barcode")
    def _compute_barcode_pattern(self):
        """Analyze barcode pattern"""
        for record in self:
            if record.barcode:
                length = len(record.barcode.strip())
                pattern_parts = []
                
                # Analyze pattern
                if record.barcode.isdigit():
                    pattern_parts.append("numeric")
                elif record.barcode.isalpha():
                    pattern_parts.append("alpha")
                else:
                    pattern_parts.append("mixed")
                
                pattern_parts.append(_("Length: %s", length))
                record.barcode_pattern = " - ".join(pattern_parts)
            else:
                record.barcode_pattern = ""

    @api.depends("barcode")
    def _compute_product_category(self):
        """Auto-classify product based on barcode length"""
        for record in self:
            if not record.barcode:
                record.product_category = "other"
                continue
                
            length = len(record.barcode.strip())
            
            # Business classification rules
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

    @api.depends("product_category", "container_type")
    def _compute_specifications(self):
        """Compute product specifications based on type"""
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

    @api.depends("barcode", "product_category")
    def _compute_is_valid(self):
        """Validate barcode according to business rules"""
        for record in self:
            if not record.barcode:
                record.is_valid = False
                record.validation_message = _("Barcode is required")
                continue
            
            barcode = record.barcode.strip()
            length = len(barcode)
            messages = []
            
            # Length validation
            valid_lengths = [5, 6, 7, 10, 14, 15]
            if length not in valid_lengths:
                messages.append(_("Invalid length: %s (expected: %s)", length, ', '.join(map(str, valid_lengths))))
            
            # Character validation
            if not re.match(r'^[A-Za-z0-9-]+$', barcode):
                messages.append(_("Invalid characters (only letters, numbers, and hyphens allowed)"))
            
            # Category-specific validation
            if record.product_category == "container_box" and not record.container_type:
                messages.append(_("Container type required for container boxes"))
            
            # Uniqueness check
            existing = self.search([
                ('barcode', '=', barcode),
                ('id', '!=', record.id)
            ], limit=1)
            if existing:
                messages.append(_("Barcode already exists: %s", existing.name))
            
            record.is_valid = len(messages) == 0
            record.validation_message = '; '.join(messages) if messages else _("Valid barcode")

    @api.depends("container_id", "location_id")
    def _compute_created_records_count(self):
        """Count records created from this barcode"""
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
    @api.onchange("barcode")
    def _onchange_barcode(self):
        """Auto-populate fields when barcode changes"""
        if self.barcode:
            # Clean the barcode
            self.barcode = self.barcode.strip().upper()
            
            # Auto-set container type for container boxes
            if self.product_category == "container_box" and not self.container_type:
                # Default to most common type
                self.container_type = "type_01"

    @api.onchange("product_category")
    def _onchange_product_category(self):
        """Clear incompatible fields when category changes"""
        if self.product_category != "container_box":
            self.container_type = False
            self.container_id = False
        if self.product_category != "location":
            self.location_id = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate_barcode(self):
        """Manually validate barcode"""
        self.ensure_one()
        self._compute_is_valid()
        
        if self.is_valid:
            message = _("Barcode validation successful")
            message_type = "success"
        else:
            message = _("Barcode validation failed: %s", self.validation_message)
            message_type = "warning"
        
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "message": message,
                "type": message_type,
                "sticky": False,
            },
        }

    def action_create_related_record(self):
        """Create related record based on product category"""
        self.ensure_one()
        
        if not self.is_valid:
            raise UserError(_("Cannot create record from invalid barcode"))
        
        if self.product_category == "container_box":
            return self._create_container_record()
        elif self.product_category == "location":
            return self._create_location_record()
        else:
            raise UserError(_("Cannot create record for category: %s", self.product_category))

    def action_get_related_records(self):
        """View related records created from this barcode"""
        self.ensure_one()
        
        records = []
        if self.container_id:
            records.append(self.container_id)
        if self.location_id:
            records.append(self.location_id)
        
        if not records:
            raise UserError(_("No related records found"))
        
        # Return action to view related records
        if len(records) == 1:
            record = records[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": record._name,
                "res_id": record.id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            # Multiple records - show list view
            return {
                "type": "ir.actions.act_window",
                "name": _("Related Records for %s", self.name),
                "view_mode": "tree,form",
                "target": "current",
            }

    def action_increment_usage(self):
        """Increment usage counter"""
        for record in self:
            record.write({
                "usage_count": record.usage_count + 1,
                "last_used_date": fields.Datetime.now(),
                "state": "used"
            })
            record.message_post(body=_("Barcode used (total uses: %s)", record.usage_count))

    def action_activate(self):
        """Activate barcode product"""
        for record in self:
            record.write({"state": "active"})
            record.message_post(body=_("Barcode product activated"))

    def action_archive(self):
        """Archive barcode product"""
        for record in self:
            record.write({"state": "archived", "active": False})
            record.message_post(body=_("Barcode product archived"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def _create_container_record(self):
        """Create container record from barcode"""
        self.ensure_one()
        
        if not self.container_type:
            raise UserError(_("Container type must be specified"))
        
        container_vals = {
            "name": _("Container %s", self.barcode),
            "barcode": self.barcode,
            "container_type": self.container_type,
            "created_from_barcode_id": self.id,
        }
        
        container = self.env["records.container"].create(container_vals)
        self.container_id = container.id
        self.action_increment_usage()
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "res_id": container.id,
            "view_mode": "form",
            "target": "current",
        }

    def _create_location_record(self):
        """Create location record from barcode"""
        self.ensure_one()
        
        location_vals = {
            "name": _("Location %s", self.barcode),
            "location_code": self.barcode,
            "created_from_barcode_id": self.id,
        }
        
        location = self.env["records.location"].create(location_vals)
        self.location_id = location.id
        self.action_increment_usage()
        
        return {
            "type": "ir.actions.act_window",
            "res_model": "records.location", 
            "res_id": location.id,
            "view_mode": "form",
            "target": "current",
        }

    @api.model
    def generate_barcode(self, category, sequence_code=None):
        """Generate new barcode for given category"""
        if not sequence_code:
            sequence_code = "barcode.product.%s" % category
        
        # Try to get sequence, create if doesn't exist
        sequence = self.env["ir.sequence"].search([("code", "=", sequence_code)], limit=1)
        if not sequence:
            sequence = self.env["ir.sequence"].create({
                "name": _("Barcode %s", category.title()),
                "code": sequence_code,
                "prefix": category.upper()[0:2],
                "padding": 4,
                "number_increment": 1,
            })
        
        return sequence.next_by_code(sequence_code)

    @api.model
    def auto_classify_and_create(self, barcode):
        """Auto-classify barcode and create appropriate records"""
        # Check if barcode already exists
        existing = self.search([("barcode", "=", barcode)], limit=1)
        if existing:
            existing.action_increment_usage()
            return existing
        
        # Create new barcode product
        product = self.create({
            "name": _("Auto Product %s", barcode),
            "barcode": barcode,
            "barcode_type": "auto",
        })
        
        # Auto-create related record if applicable
        if product.product_category in ["container_box", "location"]:
            try:
                product.action_create_related_record()
            except Exception as e:
                _logger.warning("Could not auto-create related record: %s", str(e))
        
        return product

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("barcode")
    def _check_barcode_uniqueness(self):
        """Ensure barcode uniqueness"""
        for record in self:
            if record.barcode:
                existing = self.search([
                    ("barcode", "=", record.barcode),
                    ("id", "!=", record.id)
                ], limit=1)
                if existing:
                    raise ValidationError(
                        _("Barcode %s already exists in %s", record.barcode, existing.name)
                    )

    @api.constrains("barcode", "product_category")
    def _check_barcode_category_consistency(self):
        """Validate barcode length matches expected category"""
        LENGTH_CATEGORY_MAP = {
            5: "location", 6: "container_box", 7: "permanent_folder",
            10: "shred_item", 14: "temp_folder", 15: "location"
        }
        
        for record in self:
            if record.barcode and record.product_category:
                length = len(record.barcode.strip())
                expected_category = LENGTH_CATEGORY_MAP.get(length)
                
                if expected_category and record.product_category != expected_category:
                    raise ValidationError(
                        _("Barcode length %s suggests category '%s' but '%s' is selected", 
                          length, expected_category, record.product_category)
                    )

    # ============================================================================
    # SEARCH METHODS
    # ============================================================================
    @api.model
    def search_by_pattern(self, pattern):
        """Search barcodes by pattern"""
        if not pattern:
            return self.browse()
        
        return self.search([
            "|", "|",
            ("barcode", "ilike", pattern),
            ("name", "ilike", pattern),
            ("barcode_pattern", "ilike", pattern)
        ])

    @api.model
    def get_category_statistics(self):
        """Get statistics by product category"""
        categories = self.read_group(
            [("active", "=", True)],
            ["product_category"],
            ["product_category"]
        )
        
        return {
            cat["product_category"]: cat["product_category_count"] 
            for cat in categories
        }
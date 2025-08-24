# -*- coding: utf-8 -*-
"""
Enhanced Barcode Product Management Model

Manages barcode "products" which are templates for generating physical barcodes.
This model includes intelligent classification based on barcode length and
integrates with standard business container specifications.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class BarcodeModelsEnhanced(models.Model):
    """
    Enhanced Barcode Product Management

    This model serves as a template for different types of barcodes used
    within the Records Management system. It defines the properties and
    behavior of barcodes used for locations, containers, folders, and more.
    """
    _name = 'barcode.models.enhanced'
    _description = 'Enhanced Barcode Product Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(string='Name', required=True, tracking=True, index=True)
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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # BARCODE & PRODUCT DETAILS
    # ============================================================================
    barcode = fields.Char(
        string='Sample Barcode',
        help="A sample barcode used to determine the type and format."
    )
    barcode_type = fields.Selection([
        ('location', 'Location'),
        ('container', 'Container'),
        ('folder', 'File Folder (Permanent)'),
        ('shred_bin', 'Shred Bin'),
        ('temp_folder', 'Temp Folder (Portal)'),
        ('custom', 'Custom')
    ], string='Barcode Type', compute='_compute_barcode_type', store=True)
    product_category = fields.Selection([
        ('storage', 'Storage'),
        ('service', 'Service'),
        ('consumable', 'Consumable')
    ], string='Product Category', default='storage', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Related Product',
        help="The master product associated with this barcode type."
    )
    description = fields.Text(string='Description')
    notes = fields.Text(string='Internal Notes')

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
        compute='_compute_container_specifications',
        store=True,
        digits=(12, 3)
    )
    average_weight_lbs = fields.Float(
        string='Average Weight (lbs)',
        compute='_compute_container_specifications',
        store=True,
        digits='Stock Weight'
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('barcode')
    def _compute_barcode_type(self):
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
            if not record.barcode:
                record.barcode_type = 'custom'
                continue

            length = len(record.barcode.strip())
            record.barcode_type = self._get_barcode_type_from_length(length)

    @api.depends('container_type')
    def _compute_container_specifications(self):
        """Set container specifications based on the selected container type."""
        specs = {
            'type_01': {'volume': 1.2, 'weight': 35},
            'type_02': {'volume': 2.4, 'weight': 65},
            'type_03': {'volume': 0.875, 'weight': 35},
            'type_04': {'volume': 5.0, 'weight': 75},
            'type_06': {'volume': 0.042, 'weight': 40},
        }
        for record in self:
            spec = specs.get(record.container_type)
            if spec:
                record.volume_cf = spec['volume']
                record.average_weight_lbs = spec['weight']
            else:
                record.volume_cf = 0.0
                record.average_weight_lbs = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the barcode product."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft records can be activated."))
        self.write({'state': 'active'})
        self.message_post(body=_("Barcode product activated."))

    def action_archive(self):
        """Archive the barcode product and its related product.product."""
        self.ensure_one()
        if self.product_id:
            self.product_id.action_archive()
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Barcode product archived."))

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    @api.constrains('barcode')
    def _validate_barcode_format(self):
        """Validate barcode format to ensure it contains only digits."""
        for record in self:
            if record.barcode and not record.barcode.isdigit():
                raise ValidationError(_("Barcode must contain only numbers."))

    @api.model
    def create_from_scan(self, barcode):
        """
        Find an existing barcode model or create a new one from a scan.
        This is a utility method that could be called from other parts of the system.
        """
        if not barcode or not barcode.strip().isdigit():
            raise UserError(_("Scanned barcode is invalid."))

        barcode_len = len(barcode.strip())
        barcode_type = self._get_barcode_type_from_length(barcode_len)

        existing = self.search([('barcode_type', '=', barcode_type)], limit=1)
        if existing:
            return existing

        return self.create({
            'name': _("Scanned Barcode Type: %s") % barcode_type,
            'barcode': barcode,
            'state': 'active',
        })

    @api.model
    def _get_barcode_type_from_length(self, length):
        """Helper method to get barcode type from length."""
        if length in [5, 15]:
            return 'location'
        if length == 6:
            return 'container'
        if length == 7:
            return 'folder'
        if length == 10:
            return 'shred_bin'
        if length == 14:
            return 'temp_folder'
        return 'custom'

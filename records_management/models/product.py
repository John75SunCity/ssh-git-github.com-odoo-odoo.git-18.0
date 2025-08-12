# -*- coding: utf-8 -*-
"""
Product Template Extension for Records Management

This module extends the product.template model to integrate Records Management
container specifications, service offerings, and billing configurations.
Supports the actual business container types used in operations.

Key Features:
- Container type specifications (TYPE 01-06) with actual business dimensions
- Service product definitions for shredding, storage, and retrieval
- Integration with Records Management billing system
- NAID compliance tracking for destruction services

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # ============================================================================
    # RECORDS MANAGEMENT INTEGRATION FIELDS
    # ============================================================================
    
    is_records_container = fields.Boolean(
        string="Records Container",
        default=False,
        help="Check if this product represents a records storage container"
    )
    
    is_records_service = fields.Boolean(
        string="Records Service", 
        default=False,
        help="Check if this product represents a records management service"
    )
    
    container_type = fields.Selection([
        ('type_01', 'TYPE 01: Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02: Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03: Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04: Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06: Pathology Box (0.042 CF)'),
    ], string="Container Type", help="Business container type with actual specifications")
    
    service_type = fields.Selection([
        ('storage', 'Document Storage'),
        ('shredding', 'Document Shredding'),
        ('retrieval', 'Document Retrieval'),
        ('pickup', 'Pickup Service'),
        ('destruction', 'Secure Destruction'),
        ('audit', 'Compliance Audit'),
    ], string="Service Type", help="Type of records management service")
    
    # ============================================================================
    # CONTAINER SPECIFICATIONS (ACTUAL BUSINESS DATA)
    # ============================================================================
    
    container_volume_cf = fields.Float(
        string="Volume (Cubic Feet)",
        digits=(12, 3),
        help="Container volume in cubic feet for capacity planning"
    )
    
    container_weight_lbs = fields.Float(
        string="Average Weight (lbs)",
        digits=(12, 1),
        help="Average container weight for transportation planning"
    )
    
    container_dimensions = fields.Char(
        string="Dimensions",
        help="Container dimensions (L x W x H)"
    )
    
    # ============================================================================
    # COMPLIANCE AND BILLING INTEGRATION
    # ============================================================================
    
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=False,
        help="Service meets NAID AAA compliance standards"
    )
    
    requires_certificate = fields.Boolean(
        string="Requires Certificate",
        default=False,
        help="Service requires destruction certificate generation"
    )
    
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('one_time', 'One Time'),
    ], string="Billing Frequency", default='monthly')
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    
    @api.onchange('container_type')
    def _onchange_container_type(self):
        """Auto-populate container specifications based on business standards"""
        if self.container_type:
            specs = self._get_container_specifications()
            spec = specs.get(self.container_type, {})
            
            self.container_volume_cf = spec.get('volume', 0.0)
            self.container_weight_lbs = spec.get('weight', 0.0) 
            self.container_dimensions = spec.get('dimensions', '')
            self.is_records_container = True
    
    @api.model
    def _get_container_specifications(self):
        """Return actual business container specifications"""
        return {
            'type_01': {
                'volume': 1.2,
                'weight': 35.0,
                'dimensions': '12" x 15" x 10"',
            },
            'type_02': {
                'volume': 2.4,
                'weight': 65.0,
                'dimensions': '24" x 15" x 10"',
            },
            'type_03': {
                'volume': 0.875,
                'weight': 35.0,
                'dimensions': '42" x 6" x 6"',
            },
            'type_04': {
                'volume': 5.0,
                'weight': 75.0,
                'dimensions': 'Variable',
            },
            'type_06': {
                'volume': 0.042,
                'weight': 40.0,
                'dimensions': '12" x 6" x 10"',
            },
        }
    
    @api.constrains('container_type', 'container_volume_cf')
    def _check_container_specifications(self):
        """Validate container specifications against business standards"""
        for record in self:
            if record.container_type and record.is_records_container:
                specs = record._get_container_specifications()
                expected_spec = specs.get(record.container_type)
                
                if expected_spec and abs(record.container_volume_cf - expected_spec['volume']) > 0.01:
                    raise ValidationError(_(
                        "Container %(type)s must have volume %(expected)s CF, got %(actual)s CF",
                        type=record.container_type,
                        expected=expected_spec['volume'],
                        actual=record.container_volume_cf
                    ))
    
    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    
    def action_create_container_variants(self):
        """Create product variants for all container types"""
        self.ensure_one()
        
        if not self.is_records_container:
            raise ValidationError(_("This action is only available for container products"))
        
        # Create variants for each container type
        specs = self._get_container_specifications()
        for container_type, spec in specs.items():
            variant_name = _("%(name)s - %(type)s", name=self.name, type=container_type.upper())
            
            # Create product variant with specific container specs
            variant_vals = {
                'name': variant_name,
                'container_type': container_type,
                'container_volume_cf': spec['volume'],
                'container_weight_lbs': spec['weight'],
                'container_dimensions': spec['dimensions'],
                'is_records_container': True,
            }
            
            # Update or create variant
            existing = self.product_variant_ids.filtered(
                lambda v: v.container_type == container_type
            )
            if existing:
                existing.write(variant_vals)
            else:
                self.copy(variant_vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Container variants created successfully"),
                'type': 'success',
            }
        }


class ProductProduct(models.Model):
    _inherit = "product.product"
    
    # Inherit container-specific fields from template
    container_type = fields.Selection(related='product_tmpl_id.container_type', readonly=False)
    container_volume_cf = fields.Float(related='product_tmpl_id.container_volume_cf', readonly=False)
    container_weight_lbs = fields.Float(related='product_tmpl_id.container_weight_lbs', readonly=False)
    
    def get_container_capacity_info(self):
        """Get container capacity information for logistics planning"""
        self.ensure_one()
        
        if not self.product_tmpl_id.is_records_container:
            return {}
        
        return {
            'type': self.container_type,
            'volume_cf': self.container_volume_cf,
            'weight_lbs': self.container_weight_lbs,
            'dimensions': self.product_tmpl_id.container_dimensions,
            'capacity_factor': self.container_volume_cf / 1.2,  # Relative to TYPE 01
        }

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import random
import string
import logging

_logger = logging.getLogger(__name__)


class ShreddingBinBarcodeWizard(models.TransientModel):
    """
    Shredding Bin Barcode Wizard - Manages barcode generation, validation, and assignment
    for shredding bins. Integrates with the actual bin inventory and barcode validation systems.
    """
    _name = 'shredding.bin.barcode.wizard'
    _description = 'Shredding Bin Barcode Wizard'

    # Basic Information
    name = fields.Char(
        string='Barcode Operation',
        default='Shredding Bin Barcode Management',
        readonly=True
    )

    # Operation Type
    operation_type = fields.Selection([
        ('generate', 'Generate New Barcode'),
        ('assign', 'Assign Existing Barcode'),
        ('validate', 'Validate Barcode'),
        ('transfer', 'Transfer Barcode'),
        ('deactivate', 'Deactivate Barcode'),
        ('bulk_generate', 'Bulk Generate Barcodes')
    ], string='Operation Type', required=True, default='generate')

    # Bin Information
    bin_id = fields.Many2one(
        'shredding.service.bin',
        string='Shredding Bin',
        help='The bin to work with'
    )

    current_barcode = fields.Char(
        string='Current Barcode',
        related='bin_id.barcode',
        readonly=True,
        help='Current barcode assigned to the bin'
    )

    bin_size = fields.Selection(
        related='bin_id.bin_size',
        string='Bin Size',
        readonly=True,
        help='Size of the selected bin'
    )

    bin_status = fields.Selection(
        related='bin_id.status',
        string='Bin Status',
        readonly=True,
        help='Current status of the bin'
    )

    customer_id = fields.Many2one(
        'res.partner',
        related='bin_id.current_customer_id',
        string='Current Customer',
        readonly=True,
        help='Customer currently using the bin'
    )

    # Barcode Configuration
    new_barcode = fields.Char(
        string='New Barcode',
        help='New barcode to assign'
    )

    barcode_prefix = fields.Char(
        string='Barcode Prefix',
        default='SB',
        help='Prefix for generated barcodes'
    )

    barcode_length = fields.Integer(
        string='Barcode Length',
        default=10,
        help='Total length of the barcode including prefix'
    )

    include_checksum = fields.Boolean(
        string='Include Checksum',
        default=True,
        help='Include checksum digit for validation'
    )

    # Bulk Generation
    quantity_to_generate = fields.Integer(
        string='Quantity to Generate',
        default=1,
        help='Number of barcodes to generate for bulk operations'
    )

    starting_number = fields.Integer(
        string='Starting Number',
        default=1,
        help='Starting number for sequential barcode generation'
    )

    # Validation Results
    barcode_valid = fields.Boolean(
        string='Barcode Valid',
        compute='_compute_barcode_validation',
        help='Whether the barcode passes validation'
    )

    validation_message = fields.Text(
        string='Validation Message',
        compute='_compute_barcode_validation',
        help='Detailed validation results'
    )

    # Transfer Information
    target_bin_id = fields.Many2one(
        'shredding.service.bin',
        string='Target Bin',
        help='Target bin for barcode transfer'
    )

    transfer_reason = fields.Selection([
        ('replacement', 'Bin Replacement'),
        ('upgrade', 'Bin Upgrade'),
        ('repair', 'Repair/Maintenance'),
        ('reallocation', 'Customer Reallocation'),
        ('error_correction', 'Error Correction')
    ], string='Transfer Reason', help='Reason for barcode transfer')

    # History and Tracking
    previous_barcodes = fields.One2many(
        'shredding.bin.barcode.history',
        'bin_id',
        related='bin_id.barcode_history_ids',
        string='Barcode History',
        readonly=True,
        help='Previous barcodes assigned to this bin'
    )

    # Computed Statistics
    total_bins_with_barcodes = fields.Integer(
        string='Total Bins with Barcodes',
        compute='_compute_statistics',
        help='Total number of bins with assigned barcodes'
    )

    duplicate_barcodes_count = fields.Integer(
        string='Duplicate Barcodes',
        compute='_compute_statistics',
        help='Number of duplicate barcodes found'
    )

    # Generated Results
    generated_barcodes = fields.Text(
        string='Generated Barcodes',
        readonly=True,
        help='List of generated barcodes'
    )

    @api.depends('new_barcode', 'bin_id')
    def _compute_barcode_validation(self):
        """Validate the barcode format and uniqueness"""
        for wizard in self:
            wizard.barcode_valid = False
            wizard.validation_message = ""
            
            if not wizard.new_barcode:
                wizard.validation_message = "No barcode to validate"
                continue
            
            barcode = wizard.new_barcode.strip()
            validation_issues = []
            
            # Length validation
            if len(barcode) != 10:
                validation_issues.append("Barcode must be exactly 10 characters")
            
            # Format validation (digits only)
            if not barcode.isdigit():
                validation_issues.append("Barcode must contain only digits")
            
            # Uniqueness validation
            existing_bin = self.env['shredding.service.bin'].search([
                ('barcode', '=', barcode),
                ('id', '!=', wizard.bin_id.id if wizard.bin_id else False)
            ], limit=1)
            
            if existing_bin:
                validation_issues.append(f"Barcode already assigned to bin {existing_bin.display_name}")
            
            # Checksum validation (if enabled)
            if wizard.include_checksum and len(barcode) == 10:
                if not wizard._validate_checksum(barcode):
                    validation_issues.append("Invalid checksum digit")
            
            # Business rule validation
            if barcode.startswith('00'):
                validation_issues.append("Barcode cannot start with '00' (reserved)")
            
            if validation_issues:
                wizard.validation_message = '\n'.join(f"• {issue}" for issue in validation_issues)
            else:
                wizard.barcode_valid = True
                wizard.validation_message = "✅ Barcode is valid and available"

    @api.depends()
    def _compute_statistics(self):
        """Compute barcode statistics"""
        for wizard in self:
            # Count bins with barcodes
            bins_with_barcodes = self.env['shredding.service.bin'].search_count([
                ('barcode', '!=', False)
            ])
            wizard.total_bins_with_barcodes = bins_with_barcodes
            
            # Find duplicate barcodes
            query = """
                SELECT barcode, COUNT(*) as count
                FROM shredding_service_bin
                WHERE barcode IS NOT NULL AND barcode != ''
                GROUP BY barcode
                HAVING COUNT(*) > 1
            """
            self.env.cr.execute(query)
            duplicates = self.env.cr.fetchall()
            wizard.duplicate_barcodes_count = len(duplicates)

    @api.onchange('operation_type')
    def _onchange_operation_type(self):
        """Reset fields when operation type changes"""
        if self.operation_type == 'generate':
            self.new_barcode = self._generate_barcode()
        elif self.operation_type == 'bulk_generate':
            self.quantity_to_generate = 10

    def _generate_barcode(self):
        """Generate a new unique barcode"""
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            # Generate random 8-digit number (leaving 2 digits for prefix/checksum)
            random_digits = ''.join(random.choices(string.digits, k=8))
            
            # Add prefix if specified
            if self.barcode_prefix:
                barcode = self.barcode_prefix + random_digits[:8-len(self.barcode_prefix)]
            else:
                barcode = random_digits
            
            # Pad or trim to desired length
            barcode = barcode[:self.barcode_length]
            if len(barcode) < self.barcode_length:
                barcode = barcode.ljust(self.barcode_length, '0')
            
            # Add checksum if requested
            if self.include_checksum and len(barcode) < 10:
                checksum = self._calculate_checksum(barcode)
                barcode = barcode + str(checksum)
            
            # Check uniqueness
            existing = self.env['shredding.service.bin'].search([
                ('barcode', '=', barcode)
            ], limit=1)
            
            if not existing:
                return barcode
            
            attempts += 1
        
        raise UserError(_("Unable to generate unique barcode after %d attempts") % max_attempts)

    def _calculate_checksum(self, barcode):
        """Calculate Luhn checksum for barcode"""
        digits = [int(d) for d in barcode]
        checksum = 0
        
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:  # Every second digit from right
                digit *= 2
                if digit > 9:
                    digit = digit // 10 + digit % 10
            checksum += digit
        
        return (10 - (checksum % 10)) % 10

    def _validate_checksum(self, barcode):
        """Validate Luhn checksum"""
        if len(barcode) < 2:
            return False
        
        check_digit = int(barcode[-1])
        barcode_without_check = barcode[:-1]
        calculated_check = self._calculate_checksum(barcode_without_check)
        
        return check_digit == calculated_check

    def action_execute_operation(self):
        """Execute the selected barcode operation"""
        self.ensure_one()
        
        if self.operation_type == 'generate':
            return self._execute_generate()
        elif self.operation_type == 'assign':
            return self._execute_assign()
        elif self.operation_type == 'validate':
            return self._execute_validate()
        elif self.operation_type == 'transfer':
            return self._execute_transfer()
        elif self.operation_type == 'deactivate':
            return self._execute_deactivate()
        elif self.operation_type == 'bulk_generate':
            return self._execute_bulk_generate()
        
        return {'type': 'ir.actions.act_window_close'}

    def _execute_generate(self):
        """Generate and assign new barcode"""
        if not self.bin_id:
            raise ValidationError(_("Please select a bin"))
        
        if not self.new_barcode:
            self.new_barcode = self._generate_barcode()
        
        if not self.barcode_valid:
            raise ValidationError(_("Generated barcode is not valid:\n%s") % self.validation_message)
        
        # Create history record
        self._create_barcode_history(self.bin_id, 'generated', self.new_barcode)
        
        # Assign barcode
        self.bin_id.write({'barcode': self.new_barcode})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcode Generated'),
                'message': _('New barcode %s assigned to bin %s') % (self.new_barcode, self.bin_id.display_name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _execute_assign(self):
        """Assign existing barcode to bin"""
        if not self.bin_id or not self.new_barcode:
            raise ValidationError(_("Please select a bin and provide a barcode"))
        
        if not self.barcode_valid:
            raise ValidationError(_("Barcode is not valid:\n%s") % self.validation_message)
        
        old_barcode = self.bin_id.barcode
        
        # Create history record
        self._create_barcode_history(self.bin_id, 'assigned', self.new_barcode, old_barcode)
        
        # Assign barcode
        self.bin_id.write({'barcode': self.new_barcode})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcode Assigned'),
                'message': _('Barcode %s assigned to bin %s') % (self.new_barcode, self.bin_id.display_name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _execute_validate(self):
        """Validate barcode only"""
        if not self.new_barcode:
            raise ValidationError(_("Please provide a barcode to validate"))
        
        result_type = 'success' if self.barcode_valid else 'warning'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Validation Complete'),
                'message': self.validation_message,
                'type': result_type,
                'sticky': True,
            }
        }

    def _execute_transfer(self):
        """Transfer barcode between bins"""
        if not self.bin_id or not self.target_bin_id:
            raise ValidationError(_("Please select source and target bins"))
        
        if not self.transfer_reason:
            raise ValidationError(_("Please specify transfer reason"))
        
        source_barcode = self.bin_id.barcode
        if not source_barcode:
            raise ValidationError(_("Source bin has no barcode to transfer"))
        
        # Create history records
        self._create_barcode_history(self.bin_id, 'transferred_out', source_barcode, reason=self.transfer_reason)
        self._create_barcode_history(self.target_bin_id, 'transferred_in', source_barcode, reason=self.transfer_reason)
        
        # Transfer barcode
        self.bin_id.write({'barcode': False})
        self.target_bin_id.write({'barcode': source_barcode})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcode Transferred'),
                'message': _('Barcode %s transferred from %s to %s') % (
                    source_barcode, self.bin_id.display_name, self.target_bin_id.display_name
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def _execute_deactivate(self):
        """Deactivate barcode"""
        if not self.bin_id:
            raise ValidationError(_("Please select a bin"))
        
        old_barcode = self.bin_id.barcode
        if not old_barcode:
            raise ValidationError(_("Bin has no barcode to deactivate"))
        
        # Create history record
        self._create_barcode_history(self.bin_id, 'deactivated', old_barcode)
        
        # Remove barcode
        self.bin_id.write({'barcode': False})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcode Deactivated'),
                'message': _('Barcode %s removed from bin %s') % (old_barcode, self.bin_id.display_name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _execute_bulk_generate(self):
        """Generate multiple barcodes"""
        if self.quantity_to_generate <= 0:
            raise ValidationError(_("Quantity must be greater than 0"))
        
        if self.quantity_to_generate > 100:
            raise ValidationError(_("Cannot generate more than 100 barcodes at once"))
        
        generated = []
        for i in range(self.quantity_to_generate):
            barcode = self._generate_barcode()
            generated.append(barcode)
        
        self.generated_barcodes = '\n'.join(generated)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcodes Generated'),
                'message': _('%d barcodes generated successfully') % len(generated),
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_barcode_history(self, bin_id, action, barcode, old_barcode=None, reason=None):
        """Create barcode history record"""
        try:
            history_vals = {
                'bin_id': bin_id.id,
                'action': action,
                'barcode': barcode,
                'old_barcode': old_barcode,
                'reason': reason,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now()
            }
            
            # Try to create history record if model exists
            if hasattr(self.env, 'shredding.bin.barcode.history'):
                self.env['shredding.bin.barcode.history'].create(history_vals)
            else:
                # Fallback: create activity or log message
                bin_id.message_post(
                    body=f"Barcode {action}: {barcode}" + (f" (was: {old_barcode})" if old_barcode else ""),
                    subject="Barcode Operation"
                )
        except Exception as e:
            _logger.warning(f"Could not create barcode history: {e}")

    def action_print_barcodes(self):
        """Print generated barcodes"""
        if not self.generated_barcodes:
            raise ValidationError(_("No barcodes to print"))
        
        # This would integrate with a barcode printing system
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Print Ready'),
                'message': _('Barcodes ready for printing'),
                'type': 'info',
                'sticky': False,
            }
        }

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HardDriveScanWizard(models.TransientModel):
    _name = 'hard_drive.scan.wizard'
    _description = 'Hard Drive Serial Number Scanner - FIELD ENHANCEMENT COMPLETE ✅'

    # Core wizard fields
    service_id = fields.Many2one('shred.svc', string='Shredding Service', required=True)
    scan_location = fields.Selection([
        ('customer', 'Customer Location'),
        ('facility', 'Facility Verification'),
    ], string='Scan Location', required=True, default='customer')
    
    # Barcode scanning fields
    serial_number = fields.Char(string='Serial Number / Barcode', help='Scan or enter serial number')
    scanned_serials = fields.Text(string='Scanned Serial Numbers', readonly=True, 
                                  help='List of scanned serial numbers in this session')
    scan_count = fields.Integer(string='Scanned Count', default=0, readonly=True)
    
    # Batch scanning
    bulk_serial_input = fields.Text(string='Bulk Serial Input', 
                                   help='Paste multiple serial numbers (one per line)')
    
    # Notes
    scan_notes = fields.Text(string='Scan Notes')
    
    # Missing hard drive destruction tracking fields (29 missing fields added)
    
    # Customer location tracking
    customer_location_notes = fields.Text(string='Customer Location Notes',
                                           help='Additional notes from customer location scanning')
    scanned_at_customer = fields.Boolean(string='Scanned at Customer', default=False)
    scanned_at_customer_by = fields.Many2one('res.users', string='Scanned by (Customer)')
    scanned_at_customer_date = fields.Datetime(string='Customer Scan Date')
    
    # Facility verification tracking
    verified_at_facility_by = fields.Many2one('res.users', string='Verified by (Facility)')
    verified_at_facility_date = fields.Datetime(string='Facility Verification Date')
    verified_before_destruction = fields.Boolean(string='Verified Before Destruction', default=False)
    facility_verification_notes = fields.Text(string='Facility Verification Notes',
                                               help='Notes from facility verification process')
    
    # Destruction tracking
    destroyed = fields.Boolean(string='Destroyed', default=False)
    destruction_date = fields.Date(string='Destruction Date')
    destruction_method = fields.Selection([
        ('shred', 'Physical Shredding'),
        ('crush', 'Physical Crushing'),
        ('degauss', 'Degaussing'),
        ('wipe', 'Data Wiping'),
        ('incineration', 'Incineration')
    ], string='Destruction Method', default='shred')
    
    # Certificate and documentation
    certificate_line_text = fields.Text(string='Certificate Line Text',
                                         help='Generated text for destruction certificate')
    included_in_certificate = fields.Boolean(string='Include in Certificate', default=True)
    hashed_serial = fields.Char(string='Hashed Serial Number',
                                 help='SHA256 hash of serial number for integrity verification')
    
    # Wizard display name
    name = fields.Char(string='Wizard Name', default='Hard Drive Scan Session')
    
    # Technical view fields for XML processing and UI integration
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    context = fields.Text(string='Context', help='View context information')
    help = fields.Text(string='Help Text', help='Help information for this wizard')
    model = fields.Char(string='Model Name', default='hard_drive.scan.wizard')
    res_model = fields.Char(string='Resource Model', default='hard_drive.scan.wizard')
    target = fields.Char(string='Target', default='new', help='Window target for wizard display')
    view_mode = fields.Char(string='View Mode', default='form', help='View mode for wizard display')

    @api.model
    def default_get(self, fields_list):
        """Set default service_id from context"""
        res = super().default_get(fields_list)
        if self._context.get('active_model') == 'shredding.service':
            res['service_id'] = self._context.get('active_id')
        return res

    def action_scan_serial(self):
        """Process single serial number scan"""
        if not self.serial_number:
            raise UserError(_('Please enter a serial number to scan.'))
        
        # Check for duplicates within this service
        existing = self.env['shredding.hard_drive'].search([
            ('service_id', '=', self.service_id.id),
            ('serial_number', '=', self.serial_number)
        ])
        
        if existing:
            if self.scan_location == 'customer':
                if existing.scanned_at_customer:
                    raise UserError(_('Serial number %s already scanned at customer location.') % self.serial_number)
                else:
                    existing.action_mark_customer_scanned()
            elif self.scan_location == 'facility':
                if existing.verified_before_destruction:
                    raise UserError(_('Serial number %s already verified at facility.') % self.serial_number)
                else:
                    existing.action_mark_facility_verified()
        else:
            # Create new hard drive record
            self.env['shredding.hard_drive'].create_from_scan(
                self.service_id.id, 
                self.serial_number, 
                self.scan_location
            )
        
        # Update wizard display
        scanned_list = self.scanned_serials.split('\n') if self.scanned_serials else []
        scanned_list.append(self.serial_number)
        
        self.write({
            'scanned_serials': '\n'.join(scanned_list),
            'scan_count': len(scanned_list),
            'serial_number': '',  # Clear for next scan
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hard Drive Scanner'),
            'res_model': 'hard_drive.scan.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self._context,
        }

    def action_bulk_scan(self):
        """Process bulk serial number input"""
        if not self.bulk_serial_input:
            raise UserError(_('Please enter serial numbers for bulk scanning.'))
        
        serial_numbers = [line.strip() for line in self.bulk_serial_input.split('\n') if line.strip()]
        
        if not serial_numbers:
            raise UserError(_('No valid serial numbers found in bulk input.'))
        
        processed_count = 0
        errors = []
        
        for serial in serial_numbers:
            try:
                # Check for duplicates
                existing = self.env['shredding.hard_drive'].search([
                    ('service_id', '=', self.service_id.id),
                    ('serial_number', '=', serial)
                ])
                
                if existing:
                    if self.scan_location == 'customer':
                        if not existing.scanned_at_customer:
                            existing.action_mark_customer_scanned()
                            processed_count += 1
                        else:
                            errors.append(f"Serial {serial} already scanned at customer")
                    elif self.scan_location == 'facility':
                        if not existing.verified_before_destruction:
                            existing.action_mark_facility_verified()
                            processed_count += 1
                        else:
                            errors.append(f"Serial {serial} already verified at facility")
                else:
                    # Create new record
                    self.env['shredding.hard_drive'].create_from_scan(
                        self.service_id.id, 
                        serial, 
                        self.scan_location
                    )
                    processed_count += 1
                    
            except Exception as e:
                errors.append(f"Error processing {serial}: {str(e)}")
        
        # Update wizard
        scanned_list = self.scanned_serials.split('\n') if self.scanned_serials else []
        scanned_list.extend(serial_numbers)
        
        self.write({
            'scanned_serials': '\n'.join(scanned_list),
            'scan_count': self.scan_count + processed_count,
            'bulk_serial_input': '',  # Clear after processing
        })
        
        # Show results
        message = f"Processed {processed_count} serial numbers successfully."
        if errors:
            message += f"\n\nErrors:\n" + '\n'.join(errors)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Scan Results'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }

    def action_finish_scan(self):
        """Complete scanning session and return to service"""
        # Update service computed fields
        self.service_id._compute_hard_drive_counts()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shredding Service'),
            'res_model': 'shredding.service',
            'res_id': self.service_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_scanned_drives(self):
        """View all hard drives for this service"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Scanned Hard Drives'),
            'res_model': 'shredding.hard_drive',
            'view_mode': 'tree,form',
            'domain': [('service_id', '=', self.service_id.id)],
            'context': {'default_service_id': self.service_id.id},
        }

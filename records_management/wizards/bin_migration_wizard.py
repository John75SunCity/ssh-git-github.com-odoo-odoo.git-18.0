# -*- coding: utf-8 -*-
"""
Bin Migration Wizard

Migrates bins from barcode.storage.box to shredding.service.bin
to consolidate duplicate bin inventory systems.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BinMigrationWizard(models.TransientModel):
    """Wizard to migrate bins from barcode.storage.box to shredding.service.bin."""
    
    _name = 'bin.migration.wizard'
    _description = 'Migrate Bins to Shredding Service Bins'

    # Source selection
    source_model = fields.Selection([
        ('barcode.storage.box', 'Barcode Storage Box (Bin Barcode Inventory)'),
        ('shred.bin', 'Shred Bin (Customer Shred Bins)'),
    ], string="Migrate From", required=True, default='barcode.storage.box')
    
    # Preview counts
    source_count = fields.Integer(string="Source Records", compute='_compute_counts')
    existing_count = fields.Integer(string="Existing Service Bins", compute='_compute_counts')
    
    # Options
    skip_duplicates = fields.Boolean(
        string="Skip Duplicates",
        default=True,
        help="Skip records where barcode already exists in shredding.service.bin"
    )
    
    archive_source = fields.Boolean(
        string="Archive Source Records After Migration",
        default=True,
        help="Set source records to inactive after successful migration"
    )
    
    default_bin_size = fields.Selection([
        ('23', '23 Gallon Shredinator'),
        ('32g', '32 Gallon Bin'),
        ('32c', '32 Gallon Console'),
        ('64', '64 Gallon Bin'),
        ('96', '96 Gallon Bin'),
    ], string="Default Bin Size", default='32g',
       help="Bin size to use when source record doesn't specify")
    
    # Results
    migrated_count = fields.Integer(string="Migrated", readonly=True)
    skipped_count = fields.Integer(string="Skipped (Duplicates)", readonly=True)
    error_count = fields.Integer(string="Errors", readonly=True)
    migration_log = fields.Text(string="Migration Log", readonly=True)

    @api.depends('source_model')
    def _compute_counts(self):
        """Compute record counts for preview."""
        for wizard in self:
            if wizard.source_model:
                wizard.source_count = self.env[wizard.source_model].search_count([])
            else:
                wizard.source_count = 0
            wizard.existing_count = self.env['shredding.service.bin'].search_count([])

    def _map_bin_size(self, source_record):
        """Map source bin size to shredding.service.bin bin_size selection."""
        # Try to get bin_size from source
        if hasattr(source_record, 'bin_size') and source_record.bin_size:
            return source_record.bin_size
        
        # Try container_type mapping (from barcode.storage.box)
        if hasattr(source_record, 'container_type') and source_record.container_type:
            mapping = {
                'type_01': '23',   # Small boxes map to 23 gallon
                'type_02': '32g',  # Standard to 32 gallon
                'type_03': '32c',  # Console type
                'type_04': '64',   # Large to 64 gallon
                'type_06': '96',   # XL to 96 gallon
            }
            return mapping.get(source_record.container_type, self.default_bin_size)
        
        return self.default_bin_size

    def action_preview(self):
        """Refresh counts and show preview."""
        self._compute_counts()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_migrate(self):
        """Execute the migration."""
        self.ensure_one()
        
        if not self.source_model:
            raise UserError(_("Please select a source model to migrate from."))
        
        SourceModel = self.env[self.source_model]
        TargetModel = self.env['shredding.service.bin']
        
        source_records = SourceModel.search([('active', 'in', [True, False])])
        
        migrated = 0
        skipped = 0
        errors = 0
        log_lines = []
        
        for record in source_records:
            try:
                barcode = record.barcode if hasattr(record, 'barcode') else None
                
                if not barcode:
                    log_lines.append(_("SKIP: Record %s has no barcode") % record.id)
                    skipped += 1
                    continue
                
                # Check for duplicates
                if self.skip_duplicates:
                    existing = TargetModel.search([('barcode', '=', barcode)], limit=1)
                    if existing:
                        log_lines.append(_("SKIP: Barcode %s already exists") % barcode)
                        skipped += 1
                        continue
                
                # Prepare values for new record
                vals = {
                    'barcode': barcode,
                    'bin_size': self._map_bin_size(record),
                    'status': 'available',
                    'manual_size_override': True,  # Since we're setting size manually
                }
                
                # Map optional fields
                if hasattr(record, 'name') and record.name:
                    vals['name'] = record.name
                    
                if hasattr(record, 'partner_id') and record.partner_id:
                    vals['current_customer_id'] = record.partner_id.id
                    
                if hasattr(record, 'location_id') and record.location_id:
                    vals['location_id'] = record.location_id.id
                
                # Create the service bin
                TargetModel.create(vals)
                migrated += 1
                log_lines.append(_("OK: Migrated barcode %s") % barcode)
                
                # Archive source if requested
                if self.archive_source and hasattr(record, 'active'):
                    record.active = False
                    
            except Exception as e:
                errors += 1
                log_lines.append(_("ERROR: Record %s - %s") % (record.id, str(e)))
        
        # Update wizard with results
        self.write({
            'migrated_count': migrated,
            'skipped_count': skipped,
            'error_count': errors,
            'migration_log': '\n'.join(log_lines[-100:]),  # Last 100 lines
        })
        
        # Return updated wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'migration_complete': True},
        }

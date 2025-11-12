# -*- coding: utf-8 -*-
"""
Container Indexing Wizard

Combines Index Container + Add Files functionality into a single workflow:
1. Index container (assign barcode, create stock tracking)  
2. Bulk add files to container with details grid
3. Set container to active status

This replaces separate "Index Container" and "Add Files" buttons with
a unified "Index Container & Add Files" wizard.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ContainerIndexingWizardFile(models.TransientModel):
    _name = 'container.indexing.wizard.file'
    _description = 'File Entry for Container Indexing'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        comodel_name='container.indexing.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(string='#', default=1)
    
    # File details
    name = fields.Char(
        string='File Name',
        help='Name/identifier for this file folder'
    )
    
    description = fields.Text(
        string='Description',
        help='Brief description of file contents'
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        help='Customer that owns this file (defaults to container customer)'
    )
    
    file_category = fields.Selection([
        ('personnel', 'Personnel Files'),
        ('financial', 'Financial Records'),
        ('legal', 'Legal Documents'),
        ('medical', 'Medical Records'),
        ('tax', 'Tax Documents'),
        ('contracts', 'Contracts'),
        ('correspondence', 'Correspondence'),
        ('other', 'Other'),
    ], string='Category', default='other')
    
    received_date = fields.Date(
        string='Received Date',
        default=fields.Date.context_today,
        help='Date file was received from customer'
    )
    
    barcode = fields.Char(
        string='Physical Barcode',
        help='Scan or enter physical barcode if pre-assigned'
    )
    
    # Display computed temp barcode (read-only)
    temp_barcode_preview = fields.Char(
        string='Temp Barcode',
        compute='_compute_temp_barcode_preview',
        help='Preview of auto-generated temporary barcode'
    )
    
    @api.depends('wizard_id.container_id', 'wizard_id.barcode', 'sequence', 'name')
    def _compute_temp_barcode_preview(self):
        """Show preview of what temp barcode will be generated"""
        for record in self:
            if record.wizard_id.container_id and record.name:
                # Use the same logic as in file creation
                container_barcode = (record.wizard_id.container_id.barcode or 
                                   record.wizard_id.barcode or 'TEMP')
                preview = f"{container_barcode}-FILE{record.sequence:02d}"
                record.temp_barcode_preview = preview
            else:
                record.temp_barcode_preview = ""


class ContainerIndexingWizard(models.TransientModel):
    _name = 'container.indexing.wizard'
    _description = 'Container Indexing & File Addition Wizard'

    # Container being indexed
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        required=True,
        readonly=True
    )
    
    # Container details (display only)
    container_name = fields.Char(related='container_id.name', readonly=True)
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        related='container_id.partner_id', 
        readonly=True
    )
    
    # Barcode assignment (if not already assigned)
    barcode = fields.Char(
        string='Physical Barcode',
        help='Scan or enter barcode from pre-printed sheet'
    )
    
    # Files to add to container
    file_ids = fields.One2many(
        comodel_name='container.indexing.wizard.file',
        inverse_name='wizard_id',
        string='Files to Add'
    )
    
    # Options
    auto_generate_temp_barcodes = fields.Boolean(
        string='Auto-generate Temporary Barcodes',
        default=True,
        help='Automatically generate temporary barcodes for files without physical barcodes'
    )
    
    @api.model
    def default_get(self, fields):
        """Set default values from container context"""
        res = super().default_get(fields)
        
        container_id = self.env.context.get('active_id')
        if container_id:
            container = self.env['records.container'].browse(container_id)
            res.update({
                'container_id': container_id,
                'barcode': container.barcode,  # Pre-fill if already assigned
            })
            
            # Load existing files or add default empty slots
            if not res.get('file_ids'):
                if container.file_ids:
                    # Load existing files from container for editing
                    res['file_ids'] = [
                        (0, 0, {
                            'sequence': i+1,
                            'name': file.name,
                            'description': file.description,
                            'partner_id': file.partner_id.id,
                            'file_category': file.file_category,
                            'received_date': file.received_date,
                            'barcode': file.barcode,
                        }) for i, file in enumerate(container.file_ids)
                    ]
                else:
                    # Add default empty file slots for new data entry
                    res['file_ids'] = [
                        (0, 0, {'sequence': i, 'partner_id': container.partner_id.id}) 
                        for i in range(1, 11)  # 10 empty file slots to start
                    ]
        
        return res
    
    def action_index_container(self):
        """
        Execute the container indexing workflow:
        1. Validate and assign barcode to container
        2. Create files with details from grid
        3. Index container (create stock tracking)
        4. Set container status to active
        """
        self.ensure_one()
        
        container = self.container_id
        
        # Step 1: Validate container state
        if container.state != 'draft':
            raise UserError(_(
                "Container %s is already indexed (status: %s). "
                "Only draft containers can be indexed."
            ) % (container.name, container.state))
        
        # Step 2: Assign barcode if provided
        if self.barcode and self.barcode != container.barcode:
            container.barcode = self.barcode
        
        if not container.barcode:
            raise UserError(_(
                "Physical barcode is required to index container. "
                "Please scan or enter the barcode from your pre-printed sheet."
            ))
        
        # Step 3: Create files from wizard grid
        created_files = self._create_files_from_grid()
        
        # Step 4: Index container (create stock quant, set active)
        self._complete_container_indexing(container, created_files)
        
        # Step 5: Show success message and return to container
        message = _(
            'Container %s indexed successfully!\n'
            'Created %d files with temporary barcodes.\n'
            'Physical Barcode: %s'
        ) % (container.name, len(created_files), container.barcode)
        
        # Post success message
        container.message_post(body=message)
        
        # Return to container form view to show the created files
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'res_id': container.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'active_tab': 'files'}  # Open Files tab by default
        }
    
    def _create_files_from_grid(self):
        """Create records.file objects from wizard grid data"""
        files_created = []
        
        for file_line in self.file_ids.filtered(lambda f: f.name):  # Only create files with names
            # Generate temp barcode if no physical barcode assigned and auto-generate is enabled
            temp_barcode = None
            if not file_line.barcode and self.auto_generate_temp_barcodes:
                container_barcode = self.container_id.barcode or self.barcode or 'TEMP'
                temp_barcode = f"{container_barcode}-FILE{file_line.sequence:02d}"
            
            file_vals = {
                'name': file_line.name,
                'description': file_line.description,
                'container_id': self.container_id.id,
                'partner_id': file_line.partner_id.id or self.container_id.partner_id.id,
                'file_category': file_line.file_category,
                'received_date': file_line.received_date,
                'barcode': file_line.barcode,  # Physical barcode if assigned
                'temp_barcode': temp_barcode,  # Generated temp barcode
            }
            
            file_record = self.env['records.file'].create(file_vals)
            files_created.append(file_record)
        
        return files_created
    

    def _complete_container_indexing(self, container, created_files):
        """Complete the container indexing process"""
        # Create stock quant if not exists
        if not container.quant_id:
            container._create_stock_quant()

        # Update container state
        container.write({
            'state': 'active',
        })

        # Post message
        files_msg = ""
        if created_files:
            files_msg = _(" and %d files created") % len(created_files)
        
        container.message_post(
            body=_("Container indexed with barcode %s%s") % (container.barcode, files_msg)
        )

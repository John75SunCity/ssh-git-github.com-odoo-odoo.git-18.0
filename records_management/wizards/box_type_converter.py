# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBoxTypeConverter(models.TransientModel):
    _name = 'records.box.type.converter'
    _description = 'Bulk Box Type Converter'

    # Core conversion fields
    name = fields.Char(string='Converter Name', compute='_compute_name', store=True)
    box_ids = fields.Many2many(
        'records.box',
        string='Boxes to Convert',
        required=True,
        help='Select the boxes you want to convert to a different type'
    )
    current_type = fields.Char(
        string='Current Type',
        readonly=True,
        help='Current box type code (if all selected boxes have the same type)'
    )
    new_box_type_code = fields.Selection([
        ('01', '01 - Standard File Box ($0.32/month)'),
        ('03', '03 - Map File Box ($0.50/month)'),
        ('04', '04 - Oversize File Box ($1.25/month)'),
        ('06', '06 - Specialty Box ($2.00/month)'),
    ], string='New Box Type', required=True,
        help='Select the new box type for all selected boxes')
    
    # Missing fields identified by field analysis
    reason = fields.Text(
        string='Conversion Reason',
        help='Optional: Explain why these boxes are being converted'
    )
    
    summary_line = fields.Html(
        string='Summary',
        compute='_compute_summary_line',
        help='Summary of the conversion operation'
    )
    
    update_location = fields.Boolean(
        string='Auto-relocate boxes',
        default=True,
        help='Automatically move boxes to appropriate location type based on new box type'
    )
    
    # Technical fields for view compatibility and integration
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    model = fields.Char(string='Model Name', default='records.box.type.converter')
    res_model = fields.Char(string='Resource Model', default='records.box.type.converter')
    context = fields.Text(string='Context', help='Evaluation context for the wizard')
    target = fields.Char(string='Target', default='new')
    view_mode = fields.Char(string='View Mode', default='form')
    help = fields.Text(string='Help Text', help='User guidance and help information')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    
    # Analytics and tracking fields
    conversion_count = fields.Integer(string='Conversion Count', compute='_compute_conversion_count')
    cost_impact = fields.Float(string='Cost Impact', compute='_compute_cost_impact')
    efficiency_score = fields.Float(string='Efficiency Score', compute='_compute_efficiency_score')
    
    # Workflow state
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preview', 'Preview'),
        ('confirmed', 'Confirmed'),
        ('done', 'Completed')
    ], string='State', default='draft')
    
    # Audit fields
    created_by = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user)
    conversion_date = fields.Datetime(string='Conversion Date')
    validated_by = fields.Many2one('res.users', string='Validated By')
    validation_notes = fields.Text(string='Validation Notes')
    
    @api.depends('box_ids', 'new_box_type_code')
    def _compute_name(self):
        for record in self:
            if record.box_ids and record.new_box_type_code:
                type_dict = dict(record._fields['new_box_type_code'].selection)
                type_name = type_dict.get(record.new_box_type_code, record.new_box_type_code)
                record.name = f"Convert {len(record.box_ids)} boxes to {type_name.split(' - ')[0]}"
            else:
                record.name = "Box Type Converter"

    @api.depends('box_ids')
    def _compute_conversion_count(self):
        for record in self:
            record.conversion_count = len(record.box_ids)

    @api.depends('box_ids', 'new_box_type_code')
    def _compute_cost_impact(self):
        for record in self:
            if not record.box_ids or not record.new_box_type_code:
                record.cost_impact = 0.0
                continue
                
            current_total = sum(box.monthly_rate for box in record.box_ids)
            rate_mapping = {'01': 0.32, '03': 0.50, '04': 1.25, '06': 2.00}
            new_rate = rate_mapping.get(record.new_box_type_code, 0.32)
            new_total = new_rate * len(record.box_ids)
            record.cost_impact = new_total - current_total

    @api.depends('box_ids', 'new_box_type_code', 'update_location')
    def _compute_efficiency_score(self):
        for record in self:
            if not record.box_ids:
                record.efficiency_score = 0.0
                continue
                
            # Calculate efficiency based on cost optimization and location matching
            base_score = 50.0
            
            # Bonus for cost savings
            if record.cost_impact < 0:
                base_score += min(30.0, abs(record.cost_impact) * 10)
            
            # Bonus for auto-relocation
            if record.update_location:
                base_score += 20.0
                
            record.efficiency_score = min(100.0, base_score)

    @api.depends('box_ids', 'new_box_type_code', 'update_location')
    def _compute_summary_line(self):
        for wizard in self:
            if not wizard.box_ids or not wizard.new_box_type_code:
                wizard.summary_line = '<p>Please select boxes and new type</p>'
                continue
                
            box_count = len(wizard.box_ids)
            type_mapping = dict(wizard._fields['new_box_type_code'].selection)
            new_type_name = type_mapping.get(wizard.new_box_type_code, 'Unknown')
            
            # Calculate cost impact
            current_total = sum(box.monthly_rate for box in wizard.box_ids)
            
            # Calculate new rates
            rate_mapping = {
                '01': 0.32, '03': 0.50, '04': 1.25, '06': 2.00
            }
            new_rate = rate_mapping.get(wizard.new_box_type_code, 0.32)
            new_total = new_rate * box_count
            cost_change = new_total - current_total
            
            cost_info = ""
            if cost_change > 0:
                cost_info = f"<br/><span style='color: red;'>Cost increase: +${cost_change:.2f}/month</span>"
            elif cost_change < 0:
                cost_info = f"<br/><span style='color: green;'>Cost savings: ${abs(cost_change):.2f}/month</span>"
            else:
                cost_info = "<br/><span style='color: blue;'>No cost change</span>"
            
            relocation_info = ""
            if wizard.update_location:
                relocation_info = "<br/><small>Boxes will be auto-relocated to appropriate locations</small>"
            
            wizard.summary_line = f"""
                <p><strong>Converting {box_count} boxes to {new_type_name}</strong>
                <br/>Current monthly cost: ${current_total:.2f}
                <br/>New monthly cost: ${new_total:.2f}
                {cost_info}
                {relocation_info}
                </p>
            """

    @api.model
    def default_get(self, fields_list):
        """Set default values based on context."""
        defaults = super().default_get(fields_list)
        
        # Get box IDs from context or active selection
        box_ids = self.env.context.get('default_box_ids')
        if not box_ids and self.env.context.get('active_model') == 'records.box':
            active_ids = self.env.context.get('active_ids', [])
            if active_ids:
                box_ids = [(6, 0, active_ids)]
        
        if box_ids:
            defaults['box_ids'] = box_ids
            
            # If all boxes have same type, show it
            boxes = self.env['records.box'].browse([bid for bid in box_ids[0][2]])
            box_types = boxes.mapped('box_type_code')
            if len(set(box_types)) == 1:
                defaults['current_type'] = f"{box_types[0]} ({len(boxes)} boxes)"
        
        return defaults

    def action_convert_boxes(self):
        """Execute the bulk box type conversion."""
        if not self.box_ids:
            raise ValidationError(_('Please select at least one box to convert'))
        
        if not self.new_box_type_code:
            raise ValidationError(_('Please select a new box type'))
        
        # Get target location type for auto-relocation
        location_type_mapping = {
            '01': 'aisles',     # Standard -> aisles
            '03': 'map',        # Map -> map area
            '04': 'oversize',   # Oversize -> oversize area
            '06': 'vault',      # Specialty -> vault
        }
        
        target_location_type = location_type_mapping.get(self.new_box_type_code)
        target_location = None
        
        if self.update_location and target_location_type:
            # Find a suitable location of the target type
            target_location = self.env['records.location'].search([
                ('location_type', '=', target_location_type),
                ('active', '=', True)
            ], limit=1)
        
        # Perform the conversion
        conversion_log = []
        for box in self.box_ids:
            old_type = box.box_type_code
            old_rate = box.monthly_rate
            old_location = box.location_id
            
            # Update box type
            box.box_type_code = self.new_box_type_code
            
            # Update location if requested and target found
            if self.update_location and target_location:
                box.location_id = target_location
            
            # Log the change
            new_rate = box.monthly_rate
            rate_change = new_rate - old_rate
            
            log_entry = f"Box {box.barcode}: {old_type} → {self.new_box_type_code}"
            if rate_change != 0:
                log_entry += f" (${old_rate:.2f} → ${new_rate:.2f}/month)"
            if old_location != box.location_id:
                log_entry += f" Moved: {old_location.name} → {box.location_id.name}"
                
            conversion_log.append(log_entry)
        
        # Create activity log
        if self.reason:
            log_message = f"Bulk Conversion Reason: {self.reason}\n\nChanges:\n" + "\n".join(conversion_log)
        else:
            log_message = "Bulk Box Type Conversion:\n" + "\n".join(conversion_log)
        
        # Log activity on first box (as representative)
        if self.box_ids:
            self.box_ids[0].message_post(
                body=log_message,
                subject='Bulk Box Type Conversion'
            )
        
        # Show success message
        message = _('Successfully converted %d boxes to type %s') % (
            len(self.box_ids), 
            dict(self._fields['new_box_type_code'].selection)[self.new_box_type_code]
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Conversion Complete'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_preview_changes(self):
        """Preview the changes before applying them."""
        if not self.box_ids or not self.new_box_type_code:
            raise ValidationError(_('Please select boxes and new type first'))
        
        # Calculate the impact
        rate_mapping = {'01': 0.32, '03': 0.50, '04': 1.25, '06': 2.00}
        new_rate = rate_mapping.get(self.new_box_type_code, 0.32)
        
        preview_data = []
        for box in self.box_ids:
            old_rate = box.monthly_rate
            rate_change = new_rate - old_rate
            
            preview_data.append({
                'box': box.name or box.barcode,
                'current_type': box.box_type_code,
                'current_rate': old_rate,
                'new_type': self.new_box_type_code,
                'new_rate': new_rate,
                'rate_change': rate_change,
                'current_location': box.location_id.name if box.location_id else 'Unassigned'
            })
        
        # Return preview action (could open another wizard or just update current)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Conversion Preview'),
            'res_model': 'records.box.type.converter',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'preview_data': preview_data,
                'show_preview': True
            }
        }

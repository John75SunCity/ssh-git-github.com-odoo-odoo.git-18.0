# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class VisitorPosWizard(models.TransientModel):
    _name = 'visitor.pos.wizard'
    _description = 'Wizard to Link POS Transaction to Visitor'

    visitor_id = fields.Many2one('frontdesk.visitor', string='Visitor', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Transaction', domain="[('partner_id', '=', partner_id)]")
    service_type = fields.Selection([
        ('document_shred', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform_shred', 'Uniform Shredding'),
    ], string='Service Type', help='Suggested based on visitor notes.')
    notes = fields.Text(string='Additional Notes')

    @api.onchange('visitor_id')
    def _onchange_visitor_id(self):
        """Auto-suggest service type based on visitor notes (innovative feature)."""
        if self.visitor_id and self.visitor_id.notes:  # Assuming frontdesk.visitor has a notes field; extend if needed
            notes_lower = self.visitor_id.notes.lower()
            if 'hard drive' in notes_lower:
                self.service_type = 'hard_drive'
            elif 'uniform' in notes_lower:
                self.service_type = 'uniform_shred'
            else:
                self.service_type = 'document_shred'

    def action_confirm(self):
        """Create or link POS order and update visitor for NAID audit trail."""
        self.ensure_one()
        if not self.pos_order_id:
            # Create new POS order if none selected
            pos_config = self.env['pos.config'].search([], limit=1)  # Use default POS config; customize as needed
            if not pos_config:
                raise UserError(_('No POS configuration found. Please set up POS first.'))
            session = self.env['pos.session'].search([('config_id', '=', pos_config.id), ('state', '=', 'opened')], limit=1)
            if not session:
                session = pos_config.open_session_cb()
            # Create draft order
            self.pos_order_id = self.env['pos.order'].create({
                'partner_id': self.partner_id.id,
                'session_id': session.id,
                'amount_total': 0.0,  # To be updated in POS
                'note': self.notes,
            })
            # Add lines based on service_type (extend with your products.xml)
            product = False
            if self.service_type == 'hard_drive':
                product = self.env.ref('records_management.hard_drive_destruction_product')  # Assume XML ID from products.xml
            elif self.service_type == 'uniform_shred':
                product = self.env.ref('records_management.uniform_shred_product')
            else:
                product = self.env.ref('records_management.document_shred_product')
            if product:
                self.env['pos.order.line'].create({
                    'order_id': self.pos_order_id.id,
                    'product_id': product.id,
                    'qty': 1,
                    'price_unit': product.lst_price,
                })
        # Link to visitor and log for integrity
        self.visitor_id.write({'pos_order_id': self.pos_order_id.id})
        self.env['mail.activity'].create({
            'res_id': self.visitor_id.id,
            'res_model': 'frontdesk.visitor',
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': _('POS Linked for Audit'),
            'note': _('Transaction linked via wizard for NAID compliance.'),
        })
        # Open the POS order for finalization
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.pos_order_id.id,
            'target': 'current',
        }

    def action_process_visitor(self):
        """Process visitor without creating POS order."""
        self.ensure_one()
        self.visitor_id.write({
            'state': 'processed',
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_create_pos_order(self):
        """Create new POS order."""
        self.ensure_one()
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            raise UserError(_('No POS configuration found. Please set up POS first.'))
        
        session = self.env['pos.session'].search([
            ('config_id', '=', pos_config.id), 
            ('state', '=', 'opened')
        ], limit=1)
        
        if not session:
            session = pos_config.open_session_cb()
        
        pos_order = self.env['pos.order'].create({
            'partner_id': self.partner_id.id,
            'session_id': session.id,
            'amount_total': 0.0,
            'note': self.notes,
        })
        
        self.visitor_id.write({'pos_order_id': pos_order.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': pos_order.id,
            'target': 'current',
        }

    def action_link_existing_order(self):
        """Link existing POS order."""
        self.ensure_one()
        if not self.pos_order_id:
            raise UserError(_('Please select a POS order to link.'))
        
        self.visitor_id.write({'pos_order_id': self.pos_order_id.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.pos_order_id.id,
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel wizard."""
        return {'type': 'ir.actions.act_window_close'}

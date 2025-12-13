# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AddToWorkOrderWizard(models.TransientModel):
    _name = 'add.to.work.order.wizard'
    _description = 'Add Containers to Existing Work Order'

    container_ids = fields.Many2many(
        comodel_name='records.container',
        string='Containers',
        readonly=True
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        readonly=True
    )
    
    work_order_type = fields.Selection([
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
    ], string='Work Order Type', required=True, default='retrieval')
    
    retrieval_work_order_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string='Retrieval Work Order',
        domain="[('partner_id', '=', partner_id), ('state', 'in', ['scheduled', 'in_progress'])]"
    )
    
    destruction_work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string='Shredding Work Order',
        domain="[('partner_id', '=', partner_id), ('state', 'in', ['scheduled', 'in_progress'])]"
    )
    
    container_count = fields.Integer(
        string='Container Count',
        compute='_compute_container_count'
    )
    
    @api.depends('container_ids')
    def _compute_container_count(self):
        for wizard in self:
            wizard.container_count = len(wizard.container_ids)
    
    def action_add_to_order(self):
        """Add selected containers to chosen work order"""
        self.ensure_one()
        
        if self.work_order_type == 'retrieval':
            if not self.retrieval_work_order_id:
                raise UserError(_("Please select a retrieval work order."))
            
            work_order = self.retrieval_work_order_id
            
            # Validate containers
            invalid = self.container_ids.filtered(lambda c: c.state not in ('in', 'out'))
            if invalid:
                raise UserError(_("Cannot add containers that are not 'In Storage' or 'Out'.\nInvalid: %s") % ', '.join(invalid.mapped('name')))
            
            # Add containers to scanned_barcode_ids
            existing_ids = work_order.scanned_barcode_ids.ids
            new_ids = self.container_ids.filtered(lambda c: c.id not in existing_ids)
            
            if new_ids:
                work_order.write({
                    'scanned_barcode_ids': [(4, cid) for cid in new_ids.ids]
                })
                
                # Post message
                work_order.message_post(
                    body=_('➕ Added %d container(s) from bulk action: %s') % (len(new_ids), ', '.join(new_ids.mapped('name'))),
                    subject=_('Containers Added to Work Order')
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('%d container(s) added to retrieval work order') % len(new_ids),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_("All selected containers are already in this work order."))
        
        elif self.work_order_type == 'destruction':
            if not self.destruction_work_order_id:
                raise UserError(_("Please select a destruction work order."))
            
            work_order = self.destruction_work_order_id
            
            # Validate containers
            invalid = self.container_ids.filtered(lambda c: c.state not in ('in', 'out'))
            if invalid:
                raise UserError(_("Cannot add containers that are not 'In Storage' or 'Out'.\nInvalid: %s") % ', '.join(invalid.mapped('name')))
            
            # Add containers to container_ids
            existing_ids = work_order.container_ids.ids
            new_ids = self.container_ids.filtered(lambda c: c.id not in existing_ids)
            
            if new_ids:
                work_order.write({
                    'container_ids': [(4, cid) for cid in new_ids.ids]
                })
                
                # Post message
                work_order.message_post(
                    body=_('➕ Added %d container(s) from bulk action: %s') % (len(new_ids), ', '.join(new_ids.mapped('name'))),
                    subject=_('Containers Added to Work Order')
                )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('%d container(s) added to destruction work order') % len(new_ids),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_("All selected containers are already in this work order."))

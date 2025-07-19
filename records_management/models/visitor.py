# -*- coding: utf-8 -*-
import hashlib
from odoo import fields, models, api, _

class FrontdeskVisitor(models.Model):
    _inherit = 'frontdesk.visitor'  # Inherit Odoo's Frontdesk visitor model

    pos_order_id = fields.Many2one('pos.order', string='Linked POS Transaction', readonly=True, 
                                   help='Linked walk-in shredding transaction for auditing purposes.')
    is_shred_customer = fields.Boolean(string='Walk-in Shred Customer', default=False, 
                                       help='Flag if this visitor is here for shredding services.')
    hashed_email = fields.Char(string='Hashed Email', compute='_compute_hashed_email', store=True, 
                               help='ISO-compliant hashed version of email for secure auditing.')

    @api.depends('email')
    def _compute_hashed_email(self):
        """Compute hashed email for data integrity/encryption (ISO 27001 compliance)."""
        for rec in self:
            if rec.email:
                rec.hashed_email = hashlib.sha256(rec.email.encode()).hexdigest()
            else:
                rec.hashed_email = False

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to auto-match or create partner for walk-in customers."""
        records = super(FrontdeskVisitor, self).create(vals_list)
        for record, vals in zip(records, vals_list):
            if vals.get('phone') or vals.get('email'):
                partner = self.env['res.partner'].search([
                    '|', ('phone', '=', vals.get('phone')), ('email', '=', vals.get('email'))
                ], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': vals.get('name'),
                        'phone': vals.get('phone'),
                        'email': vals.get('email'),
                        'company_id': vals.get('company_id'),
                    })
                # Link to partner for POS compatibility (optional extension)
                record.write({'partner_id': partner.id})  # Assuming visitor has or can have partner_id; extend if needed
        return records

    def action_link_pos(self):
        """Action to open wizard for linking/creating POS order from visitor."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Link Shred Transaction'),
            'res_model': 'visitor.pos.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_visitor_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }

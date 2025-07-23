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
    
    # Phase 3: Visitor Analytics
    
    # Visit Pattern Analytics
    visit_frequency_score = fields.Float(
        string='Visit Frequency Score',
        compute='_compute_visit_analytics',
        store=True,
        help='Frequency pattern analysis for visitor'
    )
    
    customer_loyalty_indicator = fields.Selection([
        ('new', 'New Visitor'),
        ('returning', 'Returning'),
        ('regular', 'Regular'),
        ('vip', 'VIP Customer')
    ], string='Customer Loyalty Level',
       compute='_compute_visit_analytics',
       store=True,
       help='Customer loyalty assessment based on visit patterns')
    
    # Service Analytics
    service_preference_score = fields.Float(
        string='Service Preference Score',
        compute='_compute_service_analytics',
        store=True,
        help='Preference scoring for shredding services'
    )

    @api.depends('email')
    def _compute_hashed_email(self):
        """Compute hashed email for data integrity/encryption (ISO 27001 compliance)."""
        for rec in self:
            if rec.email:
                rec.hashed_email = hashlib.sha256(rec.email.encode()).hexdigest()
            else:
                rec.hashed_email = False
    
    @api.depends('email', 'phone', 'is_shred_customer')
    def _compute_visit_analytics(self):
        """Compute visitor pattern analytics"""
        for record in self:
            # Find similar visitors (same email or phone)
            domain = []
            if record.email:
                domain.append(('email', '=', record.email))
            if record.phone:
                if domain:
                    domain = ['|'] + domain + [('phone', '=', record.phone)]
                else:
                    domain = [('phone', '=', record.phone)]
            
            if domain:
                total_visits = self.search_count(domain)
                shred_visits = self.search_count(domain + [('is_shred_customer', '=', True)])
            else:
                total_visits = 1
                shred_visits = 1 if record.is_shred_customer else 0
            
            # Visit frequency score
            frequency_score = min(total_visits * 20, 100)  # Max 100 for 5+ visits
            record.visit_frequency_score = frequency_score
            
            # Customer loyalty assessment
            if total_visits >= 10:
                record.customer_loyalty_indicator = 'vip'
            elif total_visits >= 5:
                record.customer_loyalty_indicator = 'regular'
            elif total_visits >= 2:
                record.customer_loyalty_indicator = 'returning'
            else:
                record.customer_loyalty_indicator = 'new'
    
    @api.depends('is_shred_customer', 'pos_order_id')
    def _compute_service_analytics(self):
        """Compute service preference analytics"""
        for record in self:
            preference_score = 50  # Base score
            
            # Shredding service preference
            if record.is_shred_customer:
                preference_score += 30
            
            # POS transaction indicates completed service
            if record.pos_order_id:
                preference_score += 20
            
            record.service_preference_score = min(preference_score, 100)

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

# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic fields structure - ready for your code
    name = fields.Char(string='Bale Reference', required=True, default='New', tracking=True)
    shredding_id = fields.Many2one('shredding.service', string='Related Shredding Service')
    paper_type = fields.Selection([
        ('white', 'White Paper'),
        ('mixed', 'Mixed Paper'),
    ], string='Paper Type', required=True, default='white')
    weight = fields.Float(string='Weight (lbs)', tracking=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale') or 'New'
        return super().create(vals_list)

    def action_weigh_bale(self):
        """Weigh the bale"""
        self.ensure_one()
        return {
            'name': _('Weigh Bale: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'paper.bale',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_load_trailer(self):
        """Load bale on trailer"""
        self.ensure_one()
        return {
            'name': _('Load on Trailer'),
            'type': 'ir.actions.act_window',
            'res_model': 'load.trailer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_quality_inspection(self):
        """Quality inspection of the bale"""
        self.ensure_one()
        return {
            'name': _('Quality Inspection'),
            'type': 'ir.actions.act_window',
            'res_model': 'quality.inspection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_print_label(self):
        """Print bale label"""
        self.ensure_one()
        return {
            'name': _('Print Bale Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.bale_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.bale_label_report',
            'context': {'active_ids': [self.id]},
        }

    def action_view_source_documents(self):
        """View source documents for this bale"""
        self.ensure_one()
        return {
            'name': _('Source Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_move_to_storage(self):
        """Move bale to storage"""
        self.ensure_one()
        return {
            'name': _('Move to Storage'),
            'type': 'ir.actions.act_window',
            'res_model': 'bale.storage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bale_id': self.id},
        }

    def action_view_weight_history(self):
        """View weight history for this bale"""
        self.ensure_one()
        return {
            'name': _('Weight History'),
            'type': 'ir.actions.act_window',
            'res_model': 'bale.weight.history',
            'view_mode': 'tree,form',
            'domain': [('bale_id', '=', self.id)],
            'context': {'default_bale_id': self.id},
        }

    def action_view_trailer_info(self):
        """View trailer information"""
        self.ensure_one()
        return {
            'name': _('Trailer Information'),
            'type': 'ir.actions.act_window',
            'res_model': 'load.trailer',
            'view_mode': 'tree,form',
            'domain': [('bale_ids', 'in', [self.id])],
            'context': {'default_bale_ids': [(6, 0, [self.id])]},
        }

    def action_view_inspection_details(self):
        """View inspection details"""
        inspection_id = self.env.context.get('inspection_id')
        if inspection_id:
            return {
                'name': _('Inspection Details'),
                'type': 'ir.actions.act_window',
                'res_model': 'quality.inspection',
                'res_id': inspection_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

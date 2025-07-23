# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """Model for paper bales in recycling workflow."""
    _name = 'paper.bale'
    _description = 'Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    # Phase 3: Analytics & Computed Fields (8 fields)
    total_documents = fields.Integer(
        string='Total Documents',
        compute='_compute_analytics',
        store=True,
        help='Total number of source documents in this bale'
    )
    weight_efficiency = fields.Float(
        string='Weight Efficiency (%)',
        compute='_compute_analytics',
        store=True,
        help='Efficiency ratio based on document count vs weight'
    )
    storage_cost = fields.Float(
        string='Storage Cost',
        compute='_compute_analytics',
        store=True,
        help='Estimated storage cost for this bale'
    )
    processing_time = fields.Float(
        string='Processing Time (hours)',
        compute='_compute_analytics',
        store=True,
        help='Total time spent processing this bale'
    )
    quality_score = fields.Float(
        string='Quality Score',
        compute='_compute_analytics',
        store=True,
        help='Quality assessment score (0-100)'
    )
    recycling_value = fields.Float(
        string='Recycling Value ($)',
        compute='_compute_analytics',
        store=True,
        help='Estimated recycling value'
    )
    bale_status_summary = fields.Char(
        string='Status Summary',
        compute='_compute_analytics',
        store=True,
        help='Human-readable status summary'
    )
    analytics_updated = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_analytics',
        store=True,
        help='Last time analytics were computed'
    )

    # Basic fields structure - ready for your code
    name = fields.Char(string='Bale Reference', required=True, default='New')
    shredding_id = fields.Many2one('shredding.service', string='Related Shredding Service')
    paper_type = fields.Selection([
        ('white', 'White Paper'),
        ('mixed', 'Mixed Paper'),
    ], string='Paper Type', required=True, default='white')
    weight = fields.Float(string='Weight (lbs)')
    
    @api.depends('weight', 'paper_type', 'create_date')
    def _compute_analytics(self):
        """Compute analytics and business intelligence fields"""
        for bale in self:
            # Get source documents
            source_docs = self.env['records.document'].search_count([
                ('bale_id', '=', bale.id)
            ])
            
            # Basic analytics
            bale.total_documents = source_docs
            bale.analytics_updated = fields.Datetime.now()
            
            # Weight efficiency (documents per pound)
            if bale.weight and bale.weight > 0:
                bale.weight_efficiency = (source_docs / bale.weight) * 100
            else:
                bale.weight_efficiency = 0.0
            
            # Storage cost estimation (based on weight and type)
            cost_per_lb = 0.50 if bale.paper_type == 'white' else 0.35
            bale.storage_cost = bale.weight * cost_per_lb
            
            # Processing time estimation
            base_time = 2.0  # 2 hours base processing
            weight_factor = (bale.weight or 0) * 0.1  # 0.1 hour per lb
            bale.processing_time = base_time + weight_factor
            
            # Quality score (based on type and weight ratio)
            if bale.paper_type == 'white':
                base_quality = 85.0
            else:
                base_quality = 70.0
            
            # Adjust for optimal weight range (100-300 lbs)
            weight_penalty = 0
            if bale.weight:
                if bale.weight < 100:
                    weight_penalty = (100 - bale.weight) * 0.2
                elif bale.weight > 300:
                    weight_penalty = (bale.weight - 300) * 0.1
            
            bale.quality_score = max(0, min(100, base_quality - weight_penalty))
            
            # Recycling value (market price estimation)
            white_paper_rate = 0.08  # $0.08 per lb
            mixed_paper_rate = 0.05  # $0.05 per lb
            
            if bale.paper_type == 'white':
                bale.recycling_value = bale.weight * white_paper_rate
            else:
                bale.recycling_value = bale.weight * mixed_paper_rate
            
            # Status summary
            if bale.weight >= 100:
                status = "Ready for Processing"
            elif bale.weight >= 50:
                status = "In Progress"
            else:
                status = "Starting Collection"
            
            bale.bale_status_summary = f"{status} ({source_docs} docs, {bale.weight:.1f} lbs)"
    
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

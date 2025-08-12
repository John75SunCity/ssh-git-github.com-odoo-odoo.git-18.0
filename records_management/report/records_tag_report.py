from odoo import models, fields, api



class RecordsTag(models.Model):
    _name = 'records.tag'
    _description = 'Records Management Tag'

    name = fields.Char('Name', required=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

class RecordsTagReport(models.TransientModel):
    _name = 'records.tag.report'
    _description = 'Records Tag Analysis Report'

    # Report date range
    date_from = fields.Date(string='Date From', required=True, default=fields.Date.today)
    date_to = fields.Date(string='Date To', required=True, default=fields.Date.today)
    
    # Tag filters
    tag_ids = fields.Many2many('records.tag', string='Tags')
    
    # Report results
    tag_usage_count = fields.Integer(string='Usage Count', compute='_compute_tag_metrics')
    most_used_tags = fields.Text(string='Most Used Tags', compute='_compute_tag_metrics')
    
    @api.depends('date_from', 'date_to', 'tag_ids')
    def _compute_tag_metrics(self):
        """Compute tag usage analytics"""
        for record in self:
            # Sample computation - adjust based on actual tag usage in your models
            domain = [('create_date', '>=', record.date_from), ('create_date', '<=', record.date_to)]
            if record.tag_ids:
                # This would need to be adjusted based on which models actually use tags
                record.tag_usage_count = len(record.tag_ids)
                record.most_used_tags = ', '.join(record.tag_ids.mapped('name'))
            else:
                record.tag_usage_count = 0
                record.most_used_tags = ''
    
    def generate_report(self):
        """Generate the tag analysis report"""
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.tag_analysis_report',
            'report_type': 'qweb-pdf',
            'data': {'form_data': self.read()[0]},
            'context': self.env.context,
        }

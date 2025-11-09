from odoo import models, fields, api, _


class RetrievalItemLine(models.Model):
    """Line items for work order retrievals - tracks individual items to be retrieved."""
    
    _name = 'retrieval.item.line'
    _description = 'Retrieval Item Line'
    _order = 'work_order_id, sequence'

    # ============================================================================
    # FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string='Work Order',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Item identification
    box_id = fields.Many2one(
        comodel_name='records.container',
        string='Box/Container',
        required=True,
        ondelete='cascade'
    )
    item_description = fields.Char(string='Item Description')
    
    # Retrieval status
    retrieved = fields.Boolean(string='Retrieved', default=False, tracking=True)
    retrieval_time = fields.Datetime(string='Retrieval Time')
    notes = fields.Text(string='Notes')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('retrieved')
    def _compute_retrieval_status(self):
        """Auto-set retrieval time when retrieved is marked as True."""
        for record in self:
            if record.retrieved and not record.retrieval_time:
                record.retrieval_time = fields.Datetime.now()

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Batch-safe create that updates parent work order box counts."""
        records = super().create(vals_list)
        for record in records:
            if record.work_order_id:
                # Update parent total_boxes count
                work_order = record.work_order_id
                work_order.total_boxes = len(work_order.retrieval_item_ids)
        return records

    def write(self, vals):
        """Update work order totals when retrieval status changes."""
        result = super().write(vals)
        if 'retrieved' in vals:
            for record in self:
                if record.work_order_id:
                    work_order = record.work_order_id
                    completed = len(work_order.retrieval_item_ids.filtered('retrieved'))
                    work_order.completed_boxes = completed
        return result

    def unlink(self):
        """Update parent work order totals when items are deleted."""
        work_orders = self.mapped('work_order_id')
        result = super().unlink()
        for work_order in work_orders:
            work_order.total_boxes = len(work_order.retrieval_item_ids)
        return result

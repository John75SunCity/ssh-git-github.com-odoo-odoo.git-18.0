from odoo import models, fields


class DocumentRetrievalEquipment(models.Model):
    _inherit = 'maintenance.equipment'
    _description = 'Document Retrieval Equipment'

    # You only need to add fields that are NOT already in maintenance.equipment
    # For example, if you need a link to a specific work order type
    retrieval_work_order_id = fields.Many2one(
        'records.retrieval.work.order',
        string='Current Retrieval Work Order',
        tracking=True
    )
    # Add any other custom fields specific to your retrieval process here.

from odoo import models, fields, api, _

class RecordsContainerTransferLine(models.Model):
    _name = 'records.container.transfer.line'
    _description = 'Records Container Transfer Line'

    transfer_id = fields.Many2one('records.container.transfer', string="Transfer", required=True, ondelete='cascade')
    container_id = fields.Many2one('records.container', string="Container", required=True)
    from_location_id = fields.Many2one(related='transfer_id.from_location_id', string="From Location", store=True, readonly=True, comodel_name='stock.location')
    to_location_id = fields.Many2one(related='transfer_id.to_location_id', string="To Location", store=True, readonly=True, comodel_name='stock.location')
    state = fields.Selection(related='transfer_id.state', string="Status", store=True, readonly=True)

    _sql_constraints = [
        ('container_transfer_uniq', 'unique(transfer_id, container_id)', 'A container can only be listed once per transfer.')
    ]

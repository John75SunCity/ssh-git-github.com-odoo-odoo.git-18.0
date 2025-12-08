# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsContainerStockInWizard(models.TransientModel):
    """Wizard for stocking in a container when no location is pre-set."""
    _name = 'records.container.stock.in.wizard'
    _description = 'Container Stock In Wizard'

    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        required=True,
        readonly=True
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Storage Location',
        required=True,
        domain="[('usage', '=', 'internal')]",
        help="Select the warehouse location where this container will be stored"
    )

    def action_confirm(self):
        """Confirm stock in with selected location."""
        self.ensure_one()
        if not self.location_id:
            raise UserError(_("Please select a storage location."))

        container = self.container_id

        # Set the location on the container
        container.location_id = self.location_id

        # Update state and storage dates - don't create stock quants here
        # Stock quants are managed by barcode operations and inventory sync
        vals = {
            'state': 'in',
        }
        if not container.storage_start_date:
            vals['storage_start_date'] = fields.Date.today()

        container.write(vals)
        container.message_post(body=_("Container stocked in at location: %s") % self.location_id.name)

        return {'type': 'ir.actions.act_window_close'}

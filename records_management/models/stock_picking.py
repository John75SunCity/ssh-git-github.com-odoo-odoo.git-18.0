from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_management = fields.Boolean(
        string="Is a Records Management Picking",
        compute='_compute_is_records_management',
        store=True,
        help="Indicates if this picking is related to records management operations."
    )
    portal_request_id = fields.Many2one(
        'portal.request',
        string="Related Service Request",
        copy=False,
        readonly=True,
        help="The customer service request that generated this picking."
    )
    destruction_order_id = fields.Many2one(
        'records.destruction.order',
        string="Destruction Order",
        copy=False,
        readonly=True,
        help="The destruction order associated with this picking."
    )
    shred_job_id = fields.Many2one(
        'fsm.order',
        string="Shredding Job",
        domain="[('is_shred_job', '=', True)]",
        copy=False,
        help="Field Service job for on-site or off-site shredding."
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('picking_type_id.code', 'portal_request_id', 'destruction_order_id')
    def _compute_is_records_management(self):
        """
        Determine if the picking is part of the records management workflow.
        This can be based on the operation type or if it's linked to a RM document.
        """
        for picking in self:
            is_rm = False
            if picking.picking_type_id.code in ('incoming', 'outgoing', 'internal'):
                if picking.portal_request_id or picking.destruction_order_id:
                    is_rm = True
            picking.is_records_management = is_rm

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_request(self):
        """
        Action to open the related portal request form view.
        """
        self.ensure_one()
        if not self.portal_request_id:
            raise UserError(_("This picking is not linked to a service request."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'portal.request',
            'view_mode': 'form',
            'res_id': self.portal_request_id.id,
            'target': 'current',
        }

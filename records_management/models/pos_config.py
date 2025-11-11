from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PosConfig(models.Model):
    _inherit = 'pos.config'

    # ============================================================================
    # FIELDS - Records Management Integration
    # ============================================================================
    enable_records_management = fields.Boolean(
        string="Enable Records Management",
        help="Activate records management features in this Point of Sale."
    )
    destruction_service_product_id = fields.Many2one(
        'product.product',
        string="Destruction Service Product",
        domain="[('sale_ok', '=', True), ('product_type', '=', 'service')]",
        help="The product used for on-the-spot destruction services."
    )
    pickup_request_product_id = fields.Many2one(
        'product.product',
        string="Pickup Request Product",
        domain="[('sale_ok', '=', True), ('product_type', '=', 'service')]",
        help="The product used to create a records pickup request from the PoS."
    )
    default_destruction_location_id = fields.Many2one(
        'stock.location',
        string="Default Destruction Location",
        domain="[('usage', '=', 'internal')]",
        help="The default location for items processed for destruction via this PoS."
    )

    # ============================================================================
    # WALK-IN CUSTOMER SERVICE (Align with view fields)
    # ============================================================================
    enable_walk_in_service = fields.Boolean(
        string="Enable Walk-In Service",
        help="Allow processing of walk-in customers with simplified POS flow."
    )
    enable_pos_customer_history = fields.Boolean(
        string="Enable Customer History",
        help="Display recent POS order history (with cashier and pricing) when selecting a customer in the PoS interface."
    )
    walk_in_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string='Default Walk-In Customer',
        help="Default customer record used when processing anonymous walk-in visitors."
    )
    walk_in_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Walk-In Pricelist',
        help="Pricelist applied to walk-in customer transactions if specified."
    )
    auto_create_customer = fields.Boolean(
        string='Auto Create Customer',
        help="Automatically create a dedicated customer from visitor data when needed."
    )
    require_customer_info = fields.Boolean(
        string='Require Customer Info',
        help="Force entry of customer details before confirming walk-in POS orders."
    )

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('enable_records_management', 'destruction_service_product_id', 'pickup_request_product_id')
    def _check_records_management_products(self):
        """
        Ensures that if the records management feature is enabled, the necessary
        service products are configured to avoid errors during PoS operations.
        """
        for config in self:
            if config.enable_records_management and not (config.destruction_service_product_id or config.pickup_request_product_id):
                raise ValidationError(_(
                    "To enable Records Management features, you must select at least one "
                    "service product (Destruction or Pickup Request)."
                ))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    def write(self, vals):
        """
        Override write to log significant changes to the PoS configuration,
        which is important for compliance and security auditing.
        """
        # Example of logging changes for audit purposes
        if 'enable_records_management' in vals or 'destruction_service_product_id' in vals:
            self.env['naid.audit.log']._log_action(
                description=f"PoS Config '{self.name}' updated. Records Management settings changed.",
                action_type='write',
                record=self
            )
        return super(PosConfig, self).write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_records_management_orders(self):
        """
        Provides a quick link to view all PoS orders that included a records
        management service, which is useful for reporting and operations.
        """
        self.ensure_one()
        service_product_ids = (self.destruction_service_product_id | self.pickup_request_product_id).ids
        if not service_product_ids:
            raise ValidationError(_("No records management service products are configured on this PoS."))

        return {
            'name': _('Records Management PoS Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'tree,form,graph',
            'domain': [
                ('config_id', '=', self.id),
                ('lines.product_id', 'in', service_product_ids)
            ],
            'context': {'search_default_config_id': self.id}
        }

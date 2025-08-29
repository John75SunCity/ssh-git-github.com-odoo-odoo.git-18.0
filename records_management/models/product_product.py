from odoo import models, fields, api

class ProductProduct(models.Model):
    """
    Extends the base product model to add fields specific to records management,
    such as container specifications and service types. This allows linking a
    billable service product directly to the physical attributes of what is being stored or handled.
    """
    _inherit = 'product.product'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_management_product = fields.Boolean(
        string="Is a Records Management Product",
        help="Check this if the product is specifically for records management services, like storage, shredding, or retrieval."
    )

    container_type_id = fields.Many2one(
        'product.container.type',
        string="Default Container Type",
        help="The default container type associated with this service product."
    )

    # These fields can be used to store default values or for products that don't use a predefined container type.
    container_volume_cf = fields.Float(
        string="Volume (cu ft)",
        digits=(12, 4),
        help="Default container volume in cubic feet."
    )
    
    container_weight_lbs = fields.Float(
        string="Weight (lbs)",
        help="Default container weight in pounds."
    )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        """
        When a container type is selected, automatically populate the product's
        default volume and weight from the container type's specifications.
        """
        if self.container_type_id:
            self.container_volume_cf = self.container_type_id.volume_cubic_feet
            self.container_weight_lbs = self.container_type_id.average_weight_lbs

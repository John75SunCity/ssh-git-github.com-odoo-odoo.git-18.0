from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior



class StockLotAttributeValue(models.Model):
    _name = 'stock.lot.attribute.value'
    _description = 'Stock Lot Attribute Value'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    # SQL constraints
    _sql_constraints = [
        ('value_attribute_lot_uniq', 'unique(value, attribute_id, lot_id)', 'Attribute values must be unique per lot and attribute.'),
    ]
    _unique_lot_attribute = models.Constraint(
        'UNIQUE(lot_id, attribute_id)',
        "Each attribute must be unique per stock lot.",
    )

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    lot_id = fields.Many2one(comodel_name='stock.lot', string="Stock Lot", required=True, ondelete='cascade')
    attribute_id = fields.Many2one(comodel_name='stock.lot.attribute', string="Attribute", required=True)
    attribute_type = fields.Selection(related='attribute_id.attribute_type', readonly=True)

    value_text = fields.Char(string='Text Value')
    value_number = fields.Float(string='Number Value')
    value_date = fields.Date(string='Date Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    value_selection_id = fields.Many2one(comodel_name='stock.lot.attribute.option', string="Selection Value")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('attribute_id', 'value_text', 'value_number', 'value_date', 'value_boolean', 'value_selection_id')
    def _compute_display_name(self):
        """Compute display name based on attribute type and value"""
        for record in self:
            if not record.attribute_id:
                record.display_name = _("Not Set")
                continue

            attr_name = record.attribute_id.name or _("Unnamed Attribute")
            value_str = record._get_value_as_string()
            record.display_name = _("%s: %s") % (attr_name, value_str)

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _get_value_as_string(self):
        """Returns the attribute value as a formatted string."""
        self.ensure_one()
        attr_type = self.attribute_type
        if attr_type == "text":
            return self.value_text or _("N/A")
        elif attr_type == "number":
            return str(self.value_number)
        elif attr_type == "date":
            return self.value_date.strftime('%Y-%m-%d') if self.value_date else _("N/A")
        elif attr_type == "boolean":
            return _("Yes") if self.value_boolean else _("No")
        elif attr_type == "selection":
            return self.value_selection_id.name or _("N/A")
        return _("Unknown Type")

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate attribute types"""
        records = super().create(vals_list)
        for record in records:
            record._validate_value_type()
        return records

    def write(self, vals):
        """Override write to validate attribute types"""
        # Call super() first. If validation fails, the transaction will be rolled back.
        result = super().write(vals)
        if any(key.startswith('value_') for key in vals) or 'attribute_id' in vals:
            self._validate_value_type() # The constraint method already loops over self
        return result

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('attribute_id', 'value_text', 'value_number', 'value_date', 'value_boolean', 'value_selection_id')
    def _validate_value_type(self):
        """Validate that the correct value field is used for the attribute type."""
        for record in self:
            if not record.attribute_id:
                continue

            attr_type = record.attribute_type
            value_fields = {
                'text': 'value_text',
                'number': 'value_number',
                'date': 'value_date',
                'boolean': 'value_boolean',
                'selection': 'value_selection_id'
            }

            expected_field = value_fields.get(attr_type)
            if not expected_field:
                continue

            # Check that only the correct value field is set
            for field_type, field_name in value_fields.items():
                if field_type != attr_type and record[field_name]:
                    raise ValidationError(
                        _("Attribute '%(attribute)s' expects a '%(expected_type)s' value, but a '%(actual_type)s' value was provided.",
                          attribute=record.attribute_id.name,
                          expected_type=attr_type,
                          actual_type=field_type)
                    )

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class StockLotAttributeValue(models.Model):
    _name = 'stock.lot.attribute.value'
    _description = 'Stock Lot Attribute Value'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char(string='Display Name')
    lot_id = fields.Many2one()
    attribute_id = fields.Many2one()
    value_text = fields.Char(string='Text Value')
    value_number = fields.Float(string='Number Value')
    value_date = fields.Date(string='Date Value')
    value_boolean = fields.Boolean()
    value_selection = fields.Char()
    state = fields.Selection()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    name = fields.Char(string='Name')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name based on attribute type and value"""
            for record in self:
                if not record.attribute_id:
                    record.display_name = "No Attribute"
                    continue

                attr_type = record.attribute_id.attribute_type
                attr_name = record.attribute_id.name or "Unknown"

                if attr_type == "text":
                    value = record.value_text or "Empty"
                    record.display_name = _("%s: %s", attr_name, value)
                elif attr_type == "number":
                    value = record.value_number if record.value_number is not None else 0:
                        pass
                    record.display_name = _("%s: %s", attr_name, value)
                elif attr_type == "date":
                    value = record.value_date or "No Date"
                    record.display_name = _("%s: %s", attr_name, value)
                elif attr_type == "boolean":
                    value = "Yes" if record.value_boolean else "No":
                    record.display_name = _("%s: %s", attr_name, value)
                elif attr_type == "selection":
                    value = record.value_selection or "Not Selected"
                    record.display_name = _("%s: %s", attr_name, value)
                else:
                    record.display_name = _("%s: Unknown Type", attr_name)


    def _check_unique_attribute_per_lot(self):
            """Ensure each attribute is only assigned once per lot"""
            for record in self:
                existing = self.search([)]
                    ('lot_id', '=', record.lot_id.id),
                    ('attribute_id', '=', record.attribute_id.id),
                    ('id', '!=', record.id)

                if existing:
                    raise ValidationError(_("Attribute %s is already defined for this stock lot", record.attribute_id.name)):

    def get_effective_value(self):
            """Get the effective value based on attribute type"""
            self.ensure_one()
            if not self.attribute_id:
                return None

            attr_type = self.attribute_id.attribute_type
            if attr_type == "text":
                return self.value_text
            if attr_type == "number":
                return self.value_number
            if attr_type == "date":
                return self.value_date
            if attr_type == "boolean":
                return self.value_boolean
            if attr_type == "selection":
                return self.value_selection
            return None


    def create(self, vals_list):
            """Override create to validate attribute types"""
            records = super().create(vals_list)
            for record in records:
                record._validate_value_type()
            return records


    def write(self, vals):
            """Override write to validate attribute types"""
            result = super().write(vals)
            if any(key.startswith('value_') for key in vals) or 'attribute_id' in vals:
                for record in self:
                    record._validate_value_type()
            return result


    def _validate_value_type(self):
            """Validate that the correct value field is used for the attribute type""":
            if not self.attribute_id:
                return

            attr_type = self.attribute_id.attribute_type
            value_fields = ['value_text', 'value_number', 'value_date', 'value_boolean', 'value_selection']
            expected_field = f'value_{attr_type}'

            if expected_field not in value_fields:
                return  # Unknown type, skip validation

            # Check that only the correct value field is set
            for field in value_fields:
                if field != expected_field and getattr(self, field):
                    raise ValidationError(_())
                        "Attribute %s expects %s type, but %s value is provided",
                        self.attribute_id.name,
                        attr_type,
                        field.replace('value_', '')


            # Check that the correct field has a value
            if not getattr(self, expected_field) and attr_type != 'boolean':
                raise ValidationError(_())
                    "Please provide a value for %s attribute %s",:
                    attr_type,
                    self.attribute_id.name


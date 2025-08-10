# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockLotAttributeValue(models.Model):
    """Stock Lot Attribute Values"""

    _name = "stock.lot.attribute.value"
    _description = "Stock Lot Attribute Value"
    _rec_name = "display_name"

    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    lot_id = fields.Many2one(
        "stock.lot",
        string="Stock Lot",
        required=True,
        ondelete="cascade",
        help="Associated stock lot",
    )
    attribute_id = fields.Many2one(
        "stock.lot.attribute",
        string="Attribute",
        required=True,
        ondelete="cascade",
        help="Attribute definition",
    )

    # Value fields for different types
    value_text = fields.Char(string="Text Value", help="Text attribute value")
    value_number = fields.Float(string="Number Value", help="Numeric attribute value")
    value_date = fields.Date(string="Date Value", help="Date attribute value")
    value_boolean = fields.Boolean(
        string="Boolean Value", help="Boolean attribute value"
    )
    value_selection = fields.Char(
        string="Selection Value", help="Selected option value"
    )

    @api.depends(
        "attribute_id",
        "value_text",
        "value_number",
        "value_date",
        "value_boolean",
        "value_selection",
    )
    def _compute_display_name(self):
        """Compute display name based on attribute type and value"""
        for record in self:
            if not record.attribute_id:
                record.display_name = "No Attribute"
                continue

            attr_type = record.attribute_id.attribute_type
            if attr_type == "text":
                record.display_name = (
                    f"{record.attribute_id.name}: {record.value_text or 'N/A'}"
                )
            elif attr_type == "number":
                record.display_name = (
                    f"{record.attribute_id.name}: {record.value_number or 0}"
                )
            elif attr_type == "date":
                record.display_name = (
                    f"{record.attribute_id.name}: {record.value_date or 'N/A'}"
                )
            elif attr_type == "boolean":
                record.display_name = f"{record.attribute_id.name}: {'Yes' if record.value_boolean else 'No'}"
            elif attr_type == "selection":
                record.display_name = (
                    f"{record.attribute_id.name}: {record.value_selection or 'N/A'}"
                )
            else:
                record.display_name = f"{record.attribute_id.name}: Unknown Type"

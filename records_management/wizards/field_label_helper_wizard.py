# -*- coding: utf-8 -*-
from odoo import models, fields, api, _




class FieldLabelHelperWizard(models.TransientModel):
    _name = "field.label.helper.wizard"
    _description = "Field Label Helper Wizard"

    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        domain="[('model', 'in', available_model_names)]",
        required=True,
    )

    field_id = fields.Many2one(
        "ir.model.fields",
        string="Field",
        domain="[('model_id', '=', model_id), ('name', 'not in', ['id', 'create_date', 'write_date', 'create_uid', 'write_uid'])]",
    )

    available_model_names = fields.Char(compute="_compute_available_models")

    @api.depends()
    def _compute_available_models(self):
        """Get all records_management models"""
        for record in self:
            customization_model = self.env["field.label.customization"]
            models = customization_model._get_records_management_models()
            record.available_model_names = str(models)

    def action_select_field(self):
        """Return selected model and field to the customization form"""

        self.ensure_one()
        if not self.model_id or not self.field_id:
            return {"type": "ir.actions.act_window_close"}

        return {
            "type": "ir.actions.act_window_close",
            "infos": {
                "model_name": self.model_id.model,
                "field_name": self.field_id.name,
                "original_label": self.field_id.field_description,
            },
        }

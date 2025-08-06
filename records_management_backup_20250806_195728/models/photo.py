# -*- coding: utf-8 -*-
from odoo import models, fields, api


class Photo(models.Model):
    _name = "photo"
    _description = "Photo Attachment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Photo Name", required=True, default="New Photo")
    description = fields.Text(string="Description")

    # File attachment
    image = fields.Binary(string="Image", attachment=True)
    image_filename = fields.Char(string="Image Filename")

    # Relationships
    mobile_bin_key_wizard_id = fields.Many2one(
        "mobile.bin.key.wizard", string="Mobile Bin Key Wizard"
    )
    partner_id = fields.Many2one("res.partner", string="Related Partner")

    # Metadata
    date = fields.Datetime(string="Date Taken", default=fields.Datetime.now)
    location = fields.Char(string="Location")
    tags = fields.Char(string="Tags")

    # Technical fields
    file_size = fields.Integer(string="File Size (bytes)")
    file_type = fields.Char(string="File Type")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New Photo") == "New Photo":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("photo") or "New Photo"
                )
        return super().create(vals_list)
